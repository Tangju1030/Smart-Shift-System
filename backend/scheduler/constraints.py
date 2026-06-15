"""约束层 — 检查排班方案的合法性"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ScheduleConfig, PersonState, SlotState


class ConstraintChecker:
    """排班约束检查器"""

    def __init__(self, config: "ScheduleConfig", availability: dict[int, dict[str, dict[str, bool]]]):
        """
        Args:
            config: 排班配置
            availability: {user_id: {weekday: {slot: True=空闲}}}
        """
        self.config = config
        self.availability = availability

    def has_class(self, user_id: int, weekday: str, slot: str) -> bool:
        """检查该时段是否有课"""
        user_avail = self.availability.get(user_id, {})
        return not user_avail.get(weekday, {}).get(slot, True)

    def can_assign(self, person: "PersonState", weekday: str, slot: str, slot_state: "SlotState") -> bool:
        """
        综合检查：此人能否被安排到该时段？

        约束列表：
        1. 该时段有课 → 不能排
        2. 该时段已满 → 不能排
        3. 本周次数已达上限 → 不能排
        4. 连续天限制 → 不能排
        """
        # 约束1：有课不能排
        if self.has_class(person.user_id, weekday, slot):
            return False

        # 约束2：时段已满
        if slot_state.is_full:
            return False

        # 约束3：本周次数达上限
        if person.week_count >= self.config.max_weekly_shifts:
            return False

        # 约束4：连续天限制
        if not self.config.allow_consecutive_days and person.assigned_days:
            weekday_index = self.config.weekdays.index(weekday)
            for assigned_day in person.assigned_days:
                assigned_index = self.config.weekdays.index(assigned_day)
                if abs(weekday_index - assigned_index) <= 1:
                    return False

        return True

    def get_violations(self, person: "PersonState", weekday: str, slot: str, slot_state: "SlotState") -> list[str]:
        """返回不满足的具体约束列表（用于调试和AI解释）"""
        violations = []
        if self.has_class(person.user_id, weekday, slot):
            violations.append(f"{person.name} 在 {weekday}{slot} 有课")
        if slot_state.is_full:
            violations.append(f"{weekday}{slot} 已满（{slot_state.capacity}人）")
        if person.week_count >= self.config.max_weekly_shifts:
            violations.append(f"{person.name} 本周已达上限（{self.config.max_weekly_shifts}次）")
        if not self.config.allow_consecutive_days and person.assigned_days:
            weekday_index = self.config.weekdays.index(weekday)
            for assigned_day in person.assigned_days:
                assigned_index = self.config.weekdays.index(assigned_day)
                if abs(weekday_index - assigned_index) <= 1:
                    violations.append(f"{person.name} 已在相邻天 {assigned_day} 值班")
                    break
        return violations
