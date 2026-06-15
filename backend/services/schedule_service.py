"""排班调度服务"""

from sqlalchemy.orm import Session
from models.user import User
from models.schedule import ScheduleResult as ScheduleResultModel, HistoricalDuty, Availability
from scheduler.engine import ScheduleEngine, ScheduleInput
from scheduler.models import ScheduleConfig
from schemas.schedule import ScheduleTableOut, WeekCountsOut
from services.rule_service import RuleService


class ScheduleService:

    def __init__(self, db: Session):
        self.db = db

    def generate(self, week_no: int, week_dates: dict[str, str]) -> ScheduleTableOut:
        """生成一周排班"""
        rule_service = RuleService(self.db)
        rules_config = rule_service.get_config()

        # 构建引擎配置
        config = ScheduleConfig(
            weekdays=rules_config.weekdays,
            duty_slots=rules_config.duty_slots,
            period_capacities=rules_config.period_capacities,
            max_weekly_shifts=rules_config.max_weekly_shifts,
            allow_consecutive_days=rules_config.allow_consecutive_days,
            balance_weight=rules_config.balance_weight,
            randomness_weight=rules_config.randomness_weight,
            search_iterations=rules_config.search_iterations,
        )

        # 获取在册人员及其历史次数
        users = self.db.query(User).filter(User.enabled == True).all()
        if not users:
            raise ValueError("没有可用人员，请先添加值班人员")

        persons = []
        for u in users:
            history_count = (
                self.db.query(HistoricalDuty)
                .filter(HistoricalDuty.user_id == u.id)
                .count()
            )
            persons.append({
                "user_id": u.id,
                "name": u.name,
                "history_count": history_count,
            })

        # 加载课表可用性
        availability = {}
        for u in users:
            records = self.db.query(Availability).filter(Availability.user_id == u.id).all()
            avail = {wd: {s: True for s in config.duty_slots} for wd in config.weekdays}
            for rec in records:
                if rec.weekday in avail and rec.period in avail[rec.weekday]:
                    avail[rec.weekday][rec.period] = rec.available
            availability[u.id] = avail

        # 确定活跃天
        active_days = [wd for wd in config.weekdays if week_dates.get(wd, '') != '假']

        # 运行引擎
        engine = ScheduleEngine(config)
        result = engine.generate(ScheduleInput(
            week_no=week_no,
            week_dates=week_dates,
            persons=persons,
            availability=availability,
            active_days=active_days,
        ))

        # 保存到数据库
        self._save_result(week_no, week_dates, result, users)

        # 构建输出（week_dates 只保留周一~周五，过滤掉 week_no）
        clean_week_dates = {k: str(v) for k, v in week_dates.items() if k in config.weekdays}
        name_to_id = {u.name: u.id for u in users}
        return ScheduleTableOut(
            week_no=week_no,
            week_dates=clean_week_dates,
            slots=result.assignments,
            stats=WeekCountsOut(
                week_counts=result.week_counts,
                accumulated_counts=result.accumulated_counts,
                min_count=result.stats["min"],
                max_count=result.stats["max"],
                range_val=result.stats["range"],
                avg=result.stats["avg"],
                unassigned=[n for n in [u.name for u in users] if result.week_counts.get(n, 0) == 0],
                seed_used=result.seed_used,
            ),
        )

    def _save_result(self, week_no: int, week_dates: dict, result, users: list[User]):
        """保存排班结果到数据库"""
        # 清除本周旧排班结果
        self.db.query(ScheduleResultModel).filter(
            ScheduleResultModel.week_no == week_no
        ).delete()

        name_to_user = {u.name: u for u in users}

        for wd, slots in result.assignments.items():
            duty_date = wd  # 存星期名（如"周一"），编辑时前端传的也是星期名
            for slot_name, names in slots.items():
                for name in names:
                    user = name_to_user.get(name)
                    if user:
                        record = ScheduleResultModel(
                            week_no=week_no,
                            duty_date=duty_date,
                            period=slot_name,
                            user_id=user.id,
                        )
                        self.db.add(record)

        self.db.commit()

    def get_result(self, week_no: int | None = None) -> list[ScheduleResultModel]:
        """获取排班结果"""
        q = self.db.query(ScheduleResultModel)
        if week_no is not None:
            q = q.filter(ScheduleResultModel.week_no == week_no)
        return q.order_by(ScheduleResultModel.duty_date, ScheduleResultModel.period).all()

    def get_user_history(self, user_id: int) -> list[HistoricalDuty]:
        """获取某人历史值班记录"""
        return (
            self.db.query(HistoricalDuty)
            .filter(HistoricalDuty.user_id == user_id)
            .order_by(HistoricalDuty.week_no.desc())
            .all()
        )

    def get_summary(self) -> dict:
        """获取仪表盘汇总数据"""
        total_users = self.db.query(User).filter(User.enabled == True).count()
        total_records = self.db.query(HistoricalDuty).count()

        # 累计次数分布
        users = self.db.query(User).filter(User.enabled == True).all()
        counts = {}
        for u in users:
            counts[u.name] = self.db.query(HistoricalDuty).filter(
                HistoricalDuty.user_id == u.id
            ).count()

        vals = list(counts.values())
        return {
            "total_users": total_users,
            "total_records": total_records,
            "min_count": min(vals) if vals else 0,
            "max_count": max(vals) if vals else 0,
            "avg_count": round(sum(vals) / len(vals), 1) if vals else 0,
            "range": max(vals) - min(vals) if vals else 0,
            "user_counts": counts,
        }

    def save_availability(self, user_id: int, availability: dict[str, dict[str, bool]]):
        """保存个人课表"""
        self.db.query(Availability).filter(Availability.user_id == user_id).delete()
        for wd, slots in availability.items():
            for slot, avail in slots.items():
                record = Availability(
                    user_id=user_id,
                    weekday=wd,
                    period=slot,
                    available=avail,
                )
                self.db.add(record)
        self.db.commit()
