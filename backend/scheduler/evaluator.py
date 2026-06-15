"""评估层 — 对排班方案打分"""

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import ScheduleConfig, PersonState


class ScheduleEvaluator:
    """排班方案评分器"""

    def __init__(self, config: "ScheduleConfig"):
        self.config = config

    def evaluate(
        self,
        persons: list["PersonState"],
        seed: int = 42,
    ) -> float:
        """
        综合评分 = 历史均衡得分 + 随机扰动得分 + 工作量均衡得分

        分数越高越好（引擎选择最高分方案）
        """
        balance_score = self._balance_score(persons)
        randomness_score = self._randomness_score(seed)
        workload_score = self._workload_score(persons)

        total = (
            balance_score * self.config.balance_weight / 100
            + randomness_score * self.config.randomness_weight / 100
            + workload_score * 0.1  # 工作量均衡作为小幅修正
        )
        return total

    def _balance_score(self, persons: list["PersonState"]) -> float:
        """
        历史均衡得分：累计次数极差越小，得分越高
        归一化到 [0, 1]
        """
        if not persons:
            return 0.0
        counts = [p.history_count + p.week_count for p in persons]
        min_c, max_c = min(counts), max(counts)
        range_val = max_c - min_c
        avg = sum(counts) / len(counts) if counts else 1
        if avg == 0:
            return 1.0
        # range_val越小，得分越高
        return 1.0 / (1.0 + range_val / (avg + 1))

    def _randomness_score(self, seed: int) -> float:
        """随机扰动得分：提供方案多样性"""
        rng = random.Random(seed)
        return rng.random()

    def _workload_score(self, persons: list["PersonState"]) -> float:
        """
        工作量均衡得分：本周安排分布是否均匀
        """
        if not persons:
            return 0.0
        counts = [p.week_count for p in persons]
        max_c = max(counts) if counts else 1
        if max_c == 0:
            return 1.0
        # 本周次数分布越均匀，得分越高
        variance = sum((c - sum(counts) / len(counts)) ** 2 for c in counts) / len(counts)
        return 1.0 / (1.0 + variance)

    def get_balance_report(self, persons: list["PersonState"]) -> dict:
        """生成均衡度报告"""
        counts = [p.history_count + p.week_count for p in persons]
        return {
            "min": min(counts) if counts else 0,
            "max": max(counts) if counts else 0,
            "avg": round(sum(counts) / len(counts), 1) if counts else 0,
            "range": max(counts) - min(counts) if counts else 0,
            "persons_with_0": sum(1 for p in persons if p.week_count == 0),
            "persons_with_1": sum(1 for p in persons if p.week_count == 1),
            "persons_with_2": sum(1 for p in persons if p.week_count >= 2),
        }
