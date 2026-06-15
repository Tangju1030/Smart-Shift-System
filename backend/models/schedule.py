"""排班相关模型"""

from sqlalchemy import Column, Integer, String, Date, Boolean, DateTime, func
from database import Base


class HistoricalDuty(Base):
    """历史值班记录"""
    __tablename__ = "historical_duty"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="值班人员ID")
    week_no = Column(Integer, nullable=False, comment="周次")
    duty_date = Column(String(20), nullable=False, comment="值班日期")
    period = Column(String(20), nullable=False, comment="时段（第一节~第四节）")
    created_at = Column(DateTime, server_default=func.now())


class ScheduleResult(Base):
    """排班结果"""
    __tablename__ = "schedule_result"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_no = Column(Integer, nullable=False, comment="周次")
    duty_date = Column(String(20), nullable=False, comment="值班日期")
    period = Column(String(20), nullable=False, comment="时段")
    user_id = Column(Integer, nullable=False, comment="值班人员ID")
    created_at = Column(DateTime, server_default=func.now())


class Availability(Base):
    """课表可用性"""
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, comment="人员ID")
    weekday = Column(String(10), nullable=False, comment="星期（周一~周五）")
    period = Column(String(20), nullable=False, comment="时段（第一节~第四节）")
    available = Column(Boolean, default=True, comment="True=空闲可排班")
