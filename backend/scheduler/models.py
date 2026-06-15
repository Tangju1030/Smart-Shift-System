"""排班引擎数据模型 — 纯数据结构，无外部依赖"""

from dataclasses import dataclass, field


@dataclass
class ScheduleConfig:
    """排班配置（由规则配置中心注入）"""
    weekdays: list[str] = field(default_factory=lambda: ["周一", "周二", "周三", "周四", "周五"])
    duty_slots: list[str] = field(default_factory=lambda: ["第一节", "第二节", "第三节", "第四节"])
    period_capacities: dict[str, int] = field(default_factory=lambda: {
        "第一节": 2, "第二节": 2, "第三节": 2, "第四节": 2
    })
    max_weekly_shifts: int = 2
    allow_consecutive_days: bool = False
    balance_weight: int = 70
    randomness_weight: int = 30
    search_iterations: int = 200


@dataclass
class PersonState:
    """单人在排班过程中的状态"""
    name: str
    user_id: int
    history_count: int = 0
    week_count: int = 0
    assigned_days: list[str] = field(default_factory=list)
    assignments: list[tuple[str, str]] = field(default_factory=list)  # [(weekday, slot), ...]


@dataclass
class SlotState:
    """单个时段的状态"""
    weekday: str
    slot: str
    capacity: int
    assigned: list[str] = field(default_factory=list)

    @property
    def spots_left(self) -> int:
        return max(0, self.capacity - len(self.assigned))

    @property
    def is_full(self) -> bool:
        return len(self.assigned) >= self.capacity


@dataclass
class ScheduleResult:
    """排班结果"""
    week_no: int
    week_dates: dict[str, str]  # {'周一': '5.12', ...}
    assignments: dict[str, dict[str, list[str]]]  # {'周一': {'第一节': ['张三'], ...}}
    week_counts: dict[str, int]
    accumulated_counts: dict[str, int]
    seed_used: int
    score: float
    stats: dict
