"""用户管理服务"""

from sqlalchemy.orm import Session
from models.user import User


class UserService:

    def __init__(self, db: Session):
        self.db = db

    def list_all(self, enabled_only: bool = False) -> list[User]:
        q = self.db.query(User)
        if enabled_only:
            q = q.filter(User.enabled == True)
        return q.order_by(User.id).all()

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.query(User).filter(User.id == user_id).first()

    def create(self, name: str, student_id: str = "", class_name: str = "") -> User:
        user = User(name=name, student_id=student_id, class_name=class_name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user_id: int, **kwargs) -> User | None:
        user = self.get_by_id(user_id)
        if not user:
            return None
        for key, val in kwargs.items():
            if hasattr(user, key) and val is not None:
                setattr(user, key, val)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user_id: int) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        self.db.delete(user)
        self.db.commit()
        return True

    def batch_create(self, names: list[str]) -> list[User]:
        users = []
        for name in names:
            if not self.db.query(User).filter(User.name == name).first():
                user = User(name=name)
                self.db.add(user)
                users.append(user)
        self.db.commit()
        for u in users:
            self.db.refresh(u)
        return users

    def count(self) -> int:
        return self.db.query(User).filter(User.enabled == True).count()
