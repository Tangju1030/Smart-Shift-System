"""排班规则配置模型"""

from sqlalchemy import Column, Integer, String, Text
from database import Base


class ScheduleRule(Base):
    __tablename__ = "schedule_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_name = Column(String(50), nullable=False, comment="规则名称（显示用）")
    rule_key = Column(String(50), unique=True, nullable=False, comment="规则键（程序用）")
    rule_value = Column(String(200), nullable=False, comment="规则值（JSON字符串）")
    description = Column(Text, default="", comment="规则描述")

    def __repr__(self):
        return f"<ScheduleRule(key={self.rule_key}, value={self.rule_value})>"
