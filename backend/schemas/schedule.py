"""排班相关 Pydantic schemas"""

from pydantic import BaseModel, Field
from datetime import date


class WeekDateIn(BaseModel):
    """周次日期输入"""
    week_no: int = Field(..., ge=1, description="周次")
    mon: str = Field(..., description="周一日期，如 5.12，传'假'跳过")
    tue: str = Field(..., description="周二日期")
    wed: str = Field(..., description="周三日期")
    thu: str = Field(..., description="周四日期")
    fri: str = Field(..., description="周五日期")


class ScheduleGenerateRequest(BaseModel):
    """排班生成请求"""
    week_no: int = Field(..., ge=1)
    week_dates: WeekDateIn


class ScheduleResultOut(BaseModel):
    """排班结果输出"""
    id: int
    week_no: int
    duty_date: str
    period: str
    user_id: int
    user_name: str | None = None

    class Config:
        from_attributes = True


class ScheduleTableOut(BaseModel):
    """排班表视图"""
    week_no: int
    week_dates: dict[str, str]  # {'周一': '5.12', ...}
    slots: dict[str, dict[str, list[str]]]  # {'周一': {'第一节': ['张三', '李四'], ...}}
    stats: "WeekCountsOut"


class WeekCountsOut(BaseModel):
    """本周统计"""
    week_counts: dict[str, int]  # {'张三': 1, '李四': 2, ...}
    accumulated_counts: dict[str, int]
    min_count: int
    max_count: int
    range_val: int
    avg: float
    unassigned: list[str]
    seed_used: int


class HistoricalDutyOut(BaseModel):
    id: int
    user_id: int
    week_no: int
    duty_date: str
    period: str
    user_name: str | None = None

    class Config:
        from_attributes = True


class AvailabilityOut(BaseModel):
    user_id: int
    user_name: str | None = None
    weekday: str
    period: str
    available: bool

    class Config:
        from_attributes = True


class AvailabilityBatchIn(BaseModel):
    """批量导入课表"""
    user_id: int
    availabilities: dict[str, dict[str, bool]]  # {'周一': {'第一节': True, ...}, ...}
