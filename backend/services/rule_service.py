"""规则配置服务"""

import json
from sqlalchemy.orm import Session
from models.rule import ScheduleRule
from schemas.rule import RulesConfig


DEFAULT_RULES = [
    ("max_weekly_shifts", "2", "每人每周最多值班次数"),
    ("allow_consecutive_days", "false", "是否允许连续天值班"),
    ("balance_weight", "70", "历史均衡权重（0-100）"),
    ("randomness_weight", "30", "随机性权重（0-100）"),
    ("search_iterations", "200", "多种子搜索次数"),
    ("period_capacities", '{"第一节":2,"第二节":2,"第三节":2,"第四节":2}', "每时段人数上限JSON"),
    ("duty_slots", '["第一节","第二节","第三节","第四节"]', "值班时段列表JSON"),
    ("weekdays", '["周一","周二","周三","周四","周五"]', "工作日列表JSON"),
]


class RuleService:

    def __init__(self, db: Session):
        self.db = db
        self._ensure_defaults()

    def _ensure_defaults(self):
        """初始化默认规则（若不存在）"""
        for key, value, desc in DEFAULT_RULES:
            if not self.db.query(ScheduleRule).filter(ScheduleRule.rule_key == key).first():
                rule = ScheduleRule(
                    rule_name=key,
                    rule_key=key,
                    rule_value=value,
                    description=desc,
                )
                self.db.add(rule)
        self.db.commit()

    def get_all(self) -> list[ScheduleRule]:
        return self.db.query(ScheduleRule).all()

    def get_config(self) -> RulesConfig:
        """获取解析后的配置对象"""
        rules = {r.rule_key: r.rule_value for r in self.get_all()}

        period_capacities = json.loads(rules.get("period_capacities", '{}'))
        duty_slots = json.loads(rules.get("duty_slots", '["第一节","第二节","第三节","第四节"]'))
        weekdays = json.loads(rules.get("weekdays", '["周一","周二","周三","周四","周五"]'))

        return RulesConfig(
            max_weekly_shifts=int(rules.get("max_weekly_shifts", "2")),
            allow_consecutive_days=rules.get("allow_consecutive_days", "false").lower() == "true",
            balance_weight=int(rules.get("balance_weight", "70")),
            randomness_weight=int(rules.get("randomness_weight", "30")),
            search_iterations=int(rules.get("search_iterations", "200")),
            period_capacities=period_capacities,
            duty_slots=duty_slots,
            weekdays=weekdays,
        )

    def update_rule(self, rule_key: str, rule_value: str) -> ScheduleRule | None:
        rule = self.db.query(ScheduleRule).filter(ScheduleRule.rule_key == rule_key).first()
        if not rule:
            return None
        rule.rule_value = rule_value
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def batch_update(self, updates: dict[str, str]) -> int:
        """批量更新规则"""
        count = 0
        for key, value in updates.items():
            if self.update_rule(key, value):
                count += 1
        return count
