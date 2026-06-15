"""排班引擎核心 — Search Layer + 编排"""

import random
import time
from dataclasses import dataclass
from .models import ScheduleConfig, PersonState, SlotState, ScheduleResult
from .constraints import ConstraintChecker
from .evaluator import ScheduleEvaluator


@dataclass
class ScheduleInput:
    """排班引擎输入"""
    week_no: int
    week_dates: dict[str, str]
    persons: list[dict]  # [{user_id, name, history_count}, ...]
    availability: dict[int, dict[str, dict[str, bool]]]  # {user_id: {weekday: {slot: bool}}}
    active_days: list[str]  # 不放假的工作日


class ScheduleEngine:
    """排班引擎 — 协调约束层和评估层"""

    def __init__(self, config: ScheduleConfig):
        self.config = config

    def generate(self, input_data: ScheduleInput) -> ScheduleResult:
        """
        多种子搜索最优排班方案

        流程：
        1. 初始化人员状态和时段状态
        2. 对每个种子执行两阶段贪心
        3. 评估每个方案，保留最优
        4. 极差≤1时早停
        """
        checker = ConstraintChecker(self.config, input_data.availability)
        evaluator = ScheduleEvaluator(self.config)

        # 用当前毫秒数扰动搜索起点，让每次运行产生不同结果
        time_offset = int(time.time() * 1000) % 10000
        best_result = None
        best_score = -float('inf')

        for i in range(1, self.config.search_iterations + 1):
            seed = (i + time_offset) % 100000 + 1
            result = self._run_single(seed, input_data, checker, evaluator)
            if result.score > best_score:
                best_score = result.score
                best_result = result
            # 早停：极差≤1 已达到理论最优
            if best_result and best_result.stats.get("range", 999) <= 1:
                break

        if best_result is None:
            raise RuntimeError("无法生成有效排班方案，请检查约束条件是否过紧")

        return best_result

    def _run_single(
        self,
        seed: int,
        inp: ScheduleInput,
        checker: ConstraintChecker,
        evaluator: ScheduleEvaluator,
    ) -> ScheduleResult:
        """单次排班运行"""
        rng = random.Random(seed)

        # 初始化人员状态
        persons = {
            p["user_id"]: PersonState(
                name=p["name"],
                user_id=p["user_id"],
                history_count=p.get("history_count", 0),
            )
            for p in inp.persons
        }

        # 初始化时段状态
        slots: dict[str, dict[str, SlotState]] = {}
        for wd in inp.active_days:
            slots[wd] = {}
            for slot_name in self.config.duty_slots:
                slots[wd][slot_name] = SlotState(
                    weekday=wd,
                    slot=slot_name,
                    capacity=self.config.period_capacities.get(slot_name, 2),
                )

        def person_sort_key(uid: int):
            p = persons[uid]
            return (p.history_count, rng.random())

        # Phase 1: 每人最多排1次，优先空槽
        order = sorted(persons.keys(), key=person_sort_key)
        for uid in order:
            person = persons[uid]
            candidates = self._get_candidates(person, inp.active_days, slots, checker, phase=1, rng=rng)
            if candidates:
                wd, slot_name = candidates[0]
                self._assign(person, wd, slot_name, slots)

        # Phase 2: 补充第2次，优先已有人的槽位
        max_two = min(6, len(persons) // 6 + 2)  # 动态计算
        two_count = sum(1 for p in persons.values() if p.week_count >= 2)
        if two_count < max_two:
            pool = [uid for uid, p in persons.items() if p.week_count == 1]
            pool.sort(key=person_sort_key)
            for uid in pool:
                if sum(1 for p in persons.values() if p.week_count >= 2) >= max_two:
                    break
                person = persons[uid]
                candidates = self._get_candidates(person, inp.active_days, slots, checker, phase=2, rng=rng)
                if candidates:
                    wd, slot_name = candidates[0]
                    self._assign(person, wd, slot_name, slots)

        # 构建结果
        assignments: dict[str, dict[str, list[str]]] = {}
        for wd in inp.active_days:
            assignments[wd] = {}
            for sn in self.config.duty_slots:
                assignments[wd][sn] = list(slots[wd][sn].assigned)

        week_counts = {p.name: p.week_count for p in persons.values()}
        acc_counts = {p.name: p.history_count + p.week_count for p in persons.values()}

        score = evaluator.evaluate(list(persons.values()), seed)
        stats = evaluator.get_balance_report(list(persons.values()))
        stats["seed"] = seed
        stats["score"] = round(score, 4)

        return ScheduleResult(
            week_no=inp.week_no,
            week_dates=inp.week_dates,
            assignments=assignments,
            week_counts=week_counts,
            accumulated_counts=acc_counts,
            seed_used=seed,
            score=score,
            stats=stats,
        )

    def _get_candidates(
        self,
        person: PersonState,
        active_days: list[str],
        slots: dict[str, dict[str, SlotState]],
        checker: ConstraintChecker,
        phase: int = 1,
        rng: random.Random | None = None,
    ) -> list[tuple[str, str]]:
        """
        获取可选时段列表，按优先级排序

        Phase 1: 优先空槽（让更多人排上）
        Phase 2: 优先有人槽（凑满2人）
        """
        if rng is None:
            rng = random.Random(0)

        candidates = []
        for wd in active_days:
            for slot_name in self.config.duty_slots:
                slot_state = slots[wd][slot_name]
                if checker.can_assign(person, wd, slot_name, slot_state):
                    spots = slot_state.spots_left
                    priority = self.config.period_capacities[slot_name] - spots if phase == 1 else spots
                    candidates.append((wd, slot_name, priority))

        # 按优先级排序，同优先级用外层种子随机打乱
        candidates.sort(key=lambda x: (x[2], rng.random()))
        return [(wd, sn) for wd, sn, _ in candidates]

    def _assign(self, person: PersonState, wd: str, slot_name: str, slots: dict):
        """执行一次安排"""
        slots[wd][slot_name].assigned.append(person.name)
        person.week_count += 1
        if wd not in person.assigned_days:
            person.assigned_days.append(wd)
        person.assignments.append((wd, slot_name))
