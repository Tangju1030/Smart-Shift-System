"""用户管理 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.user_service import UserService
from models.schedule import HistoricalDuty
from models.user import User
from schemas.user import UserOut, UserCreate, UserUpdate

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("/", response_model=list[UserOut])
def list_users(enabled_only: bool = False, db: Session = Depends(get_db)):
    """获取所有值班人员"""
    svc = UserService(db)
    return svc.list_all(enabled_only=enabled_only)


@router.get("/historical-counts")
def get_historical_counts(db: Session = Depends(get_db)):
    """获取所有人的历史值班次数汇总（必须在 /{user_id} 之前注册）"""
    users = db.query(User).filter(User.enabled == True).all()
    result = {}
    for u in users:
        count = db.query(HistoricalDuty).filter(HistoricalDuty.user_id == u.id).count()
        result[u.name] = count
    return result


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """获取单个人员信息"""
    svc = UserService(db)
    user = svc.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.post("/", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """新增值班人员"""
    svc = UserService(db)
    return svc.create(
        name=data.name,
        student_id=data.student_id,
        class_name=data.class_name,
    )


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    """修改人员信息"""
    svc = UserService(db)
    user = svc.update(user_id, **data.model_dump(exclude_none=True))
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """删除人员"""
    svc = UserService(db)
    if not svc.delete(user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"detail": "删除成功"}


@router.post("/batch", response_model=list[UserOut], status_code=201)
def batch_create(names: list[str], db: Session = Depends(get_db)):
    """批量导入人员"""
    svc = UserService(db)
    return svc.batch_create(names)


@router.post("/historical-counts")
def import_historical_counts(counts: dict[str, int], db: Session = Depends(get_db)):
    """
    批量导入历史值班次数。

    输入格式: {"曹天仪": 5, "曾启轩": 7, ...}

    会清除旧历史数据并重新写入。
    """
    if not counts:
        raise HTTPException(status_code=400, detail="数据为空")

    # 清除所有历史记录
    db.query(HistoricalDuty).delete()

    imported = 0
    not_found = []
    for name, count in counts.items():
        user = db.query(User).filter(User.name == name).first()
        if not user:
            not_found.append(name)
            continue
        # 为每个人插入 count 条历史记录
        for i in range(count):
            duty = HistoricalDuty(
                user_id=user.id,
                week_no=1,
                duty_date=f"历史-{i+1}",
                period="第一节",
            )
            db.add(duty)
        imported += 1

    db.commit()

    return {
        "imported": imported,
        "not_found": not_found,
    }
