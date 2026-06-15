"""值班人员模型"""

from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="姓名")
    student_id = Column(String(30), default="", comment="学号")
    class_name = Column(String(50), default="", comment="班级")
    enabled = Column(Boolean, default=True, comment="是否启用")

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, enabled={self.enabled})>"
