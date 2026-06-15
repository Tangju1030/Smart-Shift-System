"""用户相关 Pydantic schemas"""

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    student_id: str = Field(default="", max_length=30, description="学号")
    class_name: str = Field(default="", max_length=50, description="班级")
    enabled: bool = Field(default=True, description="是否启用")

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    student_id: str | None = Field(None, max_length=30)
    class_name: str | None = Field(None, max_length=50)
    enabled: bool | None = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: int
    name: str
    student_id: str
    class_name: str
    enabled: bool

    class Config:
        from_attributes = True


class UserList(BaseModel):
    total: int
    items: list[UserOut]
