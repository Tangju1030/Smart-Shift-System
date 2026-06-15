"""排班生成与查看 API"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models.schedule import ScheduleResult as ScheduleResultModel
from models.user import User
from services.schedule_service import ScheduleService
from services.export_service import ExportService
from schemas.schedule import ScheduleGenerateRequest, ScheduleTableOut
from fastapi.responses import PlainTextResponse, Response

router = APIRouter(prefix="/api/schedule", tags=["排班管理"])


@router.post("/generate", response_model=ScheduleTableOut)
def generate_schedule(req: ScheduleGenerateRequest, db: Session = Depends(get_db)):
    """生成排班"""
    svc = ScheduleService(db)
    try:
        return svc.generate(req.week_no, req.week_dates.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/result")
def get_result(week_no: int | None = Query(None), db: Session = Depends(get_db)):
    """查看排班结果"""
    svc = ScheduleService(db)
    results = svc.get_result(week_no)
    return [
        {
            "id": r.id,
            "week_no": r.week_no,
            "duty_date": r.duty_date,
            "period": r.period,
            "user_id": r.user_id,
        }
        for r in results
    ]


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    """仪表盘汇总"""
    svc = ScheduleService(db)
    return svc.get_summary()


@router.get("/export/docx")
def export_docx(
    week_no: int = Query(...),
    db: Session = Depends(get_db),
):
    """导出 Word 值班签到表"""
    svc = ScheduleService(db)
    export = ExportService(svc)

    # 获取排班结果
    results = svc.get_result(week_no)
    if not results:
        raise HTTPException(status_code=404, detail=f"未找到第{week_no}周排班结果，请先生成排班")

    # 重建 slots 结构
    weekdays = ['周一', '周二', '周三', '周四', '周五']
    duty_slots = ['第一节', '第二节', '第三节', '第四节']
    week_dates = {}
    slots = {wd: {s: [] for s in duty_slots} for wd in weekdays}

    # 从数据库结果获取用户名
    from models.user import User
    users = {u.id: u.name for u in db.query(User).all()}

    for r in results:
        wd = None
        for w in weekdays:
            if w in r.duty_date:
                wd = w
                break
        if not wd or r.period not in duty_slots:
            continue
        week_dates[wd] = r.duty_date
        name = users.get(r.user_id, str(r.user_id))
        if name not in slots[wd][r.period]:
            slots[wd][r.period].append(name)

    docx_bytes = export.export_docx(week_no, week_dates, slots)

    from urllib.parse import quote
    filename = f'第{week_no}周年委值班签到表.docx'
    encoded = quote(filename, safe='')
    return Response(
        content=docx_bytes,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        headers={
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded}",
        },
    )


@router.get("/export/csv")
def export_csv(
    week_no: int = Query(...),
    db: Session = Depends(get_db),
):
    """导出 CSV"""
    svc = ScheduleService(db)
    results = svc.get_result(week_no)
    if not results:
        raise HTTPException(status_code=404, detail=f"未找到第{week_no}周排班结果")

    weekdays = ['周一', '周二', '周三', '周四', '周五']
    duty_slots = ['第一节', '第二节', '第三节', '第四节']
    week_dates = {}
    slots = {wd: {s: [] for s in duty_slots} for wd in weekdays}

    from models.user import User
    users = {u.id: u.name for u in db.query(User).all()}

    for r in results:
        wd = None
        for w in weekdays:
            if w in r.duty_date:
                wd = w
                break
        if not wd or r.period not in duty_slots:
            continue
        week_dates[wd] = r.duty_date
        name = users.get(r.user_id, str(r.user_id))
        if name not in slots[wd][r.period]:
            slots[wd][r.period].append(name)

    export = ExportService(svc)
    csv_text = export.export_csv(week_no, week_dates, slots)
    return PlainTextResponse(csv_text, media_type='text/csv; charset=utf-8')


# ═══════════════════════════════════════════════════════════
# 排班结果编辑
# ═══════════════════════════════════════════════════════════

class SlotEditRequest(BaseModel):
    week_no: int
    duty_date: str   # 如 "周一"
    period: str       # 如 "第一节"
    user_name: str


class SlotReplaceRequest(SlotEditRequest):
    old_user_name: str


@router.put("/slot/add")
def add_person_to_slot(req: SlotEditRequest, db: Session = Depends(get_db)):
    """向某个时段添加一名值班人员"""
    user = db.query(User).filter(User.name == req.user_name).first()
    if not user:
        raise HTTPException(404, f"用户不存在: {req.user_name}")

    existing = db.query(ScheduleResultModel).filter(
        ScheduleResultModel.week_no == req.week_no,
        ScheduleResultModel.duty_date == req.duty_date,
        ScheduleResultModel.period == req.period,
        ScheduleResultModel.user_id == user.id,
    ).first()
    if existing:
        raise HTTPException(400, f"{req.user_name} 已在该时段")

    record = ScheduleResultModel(
        week_no=req.week_no,
        duty_date=req.duty_date,
        period=req.period,
        user_id=user.id,
    )
    db.add(record)
    db.commit()
    return {"detail": f"已添加 {req.user_name} 到 {req.duty_date} {req.period}"}


@router.delete("/slot/remove")
def remove_person_from_slot(req: SlotEditRequest, db: Session = Depends(get_db)):
    """从某个时段移除一名值班人员"""
    user = db.query(User).filter(User.name == req.user_name).first()
    if not user:
        raise HTTPException(404, f"用户不存在: {req.user_name}")

    deleted = db.query(ScheduleResultModel).filter(
        ScheduleResultModel.week_no == req.week_no,
        ScheduleResultModel.duty_date == req.duty_date,
        ScheduleResultModel.period == req.period,
        ScheduleResultModel.user_id == user.id,
    ).delete()
    db.commit()

    if deleted:
        return {"detail": f"已从 {req.duty_date} {req.period} 移除 {req.user_name}"}
    raise HTTPException(404, "未找到该排班记录")


@router.put("/slot/replace")
def replace_person_in_slot(req: SlotReplaceRequest, db: Session = Depends(get_db)):
    """替换某个时段的值班人员（先删后加）"""
    remove_person_from_slot(
        SlotEditRequest(
            week_no=req.week_no, duty_date=req.duty_date,
            period=req.period, user_name=req.old_user_name,
        ), db
    )
    add_person_to_slot(
        SlotEditRequest(
            week_no=req.week_no, duty_date=req.duty_date,
            period=req.period, user_name=req.user_name,
        ), db
    )
    return {"detail": f"已将 {req.duty_date} {req.period} 的 {req.old_user_name} 替换为 {req.user_name}"}
