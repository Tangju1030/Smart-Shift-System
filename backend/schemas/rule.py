"""规则配置 Pydantic schemas"""

from pydantic import BaseModel, Field


class RuleOut(BaseModel):
    id: int
    rule_name: str
    rule_key: str
    rule_value: str
    description: str

    class Config:
        from_attributes = True


class RuleUpdate(BaseModel):
    rule_name: str | None = None
    rule_value: str | None = None
    description: str | None = None


class RulesConfig(BaseModel):
    """全部规则配置汇总"""
    max_weekly_shifts: int = Field(default=2, description="每人每周最多值班次数")
    allow_consecutive_days: bool = Field(default=False, description="是否允许连续天值班")
    balance_weight: int = Field(default=70, ge=0, le=100, description="历史均衡权重")
    randomness_weight: int = Field(default=30, ge=0, le=100, description="随机性权重")
    search_iterations: int = Field(default=200, ge=1, le=1000, description="多种子搜索次数")
    period_capacities: dict[str, int] = Field(
        default={"第一节": 2, "第二节": 2, "第三节": 2, "第四节": 2},
        description="每时段人数上限"
    )
    duty_slots: list[str] = Field(default=["第一节", "第二节", "第三节", "第四节"])
    weekdays: list[str] = Field(default=["周一", "周二", "周三", "周四", "周五"])
