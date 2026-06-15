"""课表管理 API"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from services.schedule_service import ScheduleService
from scheduler.parser import parse_docx_schedule, parse_xlsx_schedule

router = APIRouter(prefix="/api/availability", tags=["课表管理"])


@router.get("/{user_id}")
def get_user_availability(user_id: int, db: Session = Depends(get_db)):
    """获取某人课表"""
    from models.schedule import Availability
    records = db.query(Availability).filter(Availability.user_id == user_id).all()
    availability = {}
    for r in records:
        if r.weekday not in availability:
            availability[r.weekday] = {}
        availability[r.weekday][r.period] = r.available
    return {"user_id": user_id, "availability": availability}


@router.put("/{user_id}")
def update_availability(
    user_id: int,
    availability: dict[str, dict[str, bool]],
    db: Session = Depends(get_db),
):
    """手动更新某人课表"""
    svc = ScheduleService(db)
    svc.save_availability(user_id, availability)
    return {"detail": "更新成功"}


@router.post("/upload/docx")
async def upload_docx(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    week_no: int = Form(None),
    db: Session = Depends(get_db),
):
    """上传 Word 课表并解析"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(400, "仅支持 .docx 文件")

    content = await file.read()
    parsed = parse_docx_schedule(content, file.filename, week_no)

    if parsed.get("error"):
        raise HTTPException(400, f"解析失败: {parsed['error']}")

    svc = ScheduleService(db)
    svc.save_availability(user_id, parsed["availability"])

    return {
        "user_id": user_id,
        "name": parsed["name"],
        "availability": parsed["availability"],
    }


@router.post("/upload/xlsx")
async def upload_xlsx(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传 Excel 课表批量导入"""
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(400, "仅支持 .xlsx 文件")

    content = await file.read()
    results = parse_xlsx_schedule(content)

    from services.user_service import UserService
    svc = ScheduleService(db)
    user_svc = UserService(db)

    imported = 0
    for r in results:
        # 按姓名匹配用户
        user = db.query(db.bind).first()  # placeholder
        # 简化：假设 users 表已存在对应姓名
        users = user_svc.list_all()
        matched = next((u for u in users if u.name == r["name"]), None)
        if matched:
            svc.save_availability(matched.id, r["availability"])
            imported += 1

    return {"imported": imported, "total": len(results)}
