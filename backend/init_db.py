"""数据库初始化脚本 — 创建所有表并填充默认数据"""

from database import init_db, SessionLocal
from models.user import User
from models.rule import ScheduleRule
from services.rule_service import DEFAULT_RULES


def seed_default_users():
    """填充默认37人名单"""
    default_names = [
        '曹天仪', '曾启轩', '陈德永', '成金泽', '杜昕洛', '方瑜', '龚恩希', '郭一漫',
        '胡笑笑', '黄琴斯', '黎丹', '刘芯伶', '陆东平', '马丹', '蒙世龙', '潘小燕',
        '庞雨君', '秦子恒', '邱巧丽', '任凯熙', '沈俊宇', '宋林', '覃如萍', '唐思凡',
        '王译', '温永福', '韦谭菊', '巫永贵', '吴佳奕', '吴嘉乐', '兀泉晶', '叶智仁',
        '张靖悦', '张添惟', '赵丽伟', '朱国昱', '左顺虎',
    ]

    db = SessionLocal()
    existing = db.query(User).count()
    if existing == 0:
        for name in default_names:
            db.add(User(name=name))
        db.commit()
        print(f"已导入 {len(default_names)} 名默认人员")
    else:
        print(f"已有 {existing} 名人员，跳过导入")
    db.close()


def seed_default_rules():
    """填充默认排班规则"""
    db = SessionLocal()
    for key, value, desc in DEFAULT_RULES:
        if not db.query(ScheduleRule).filter(ScheduleRule.rule_key == key).first():
            db.add(ScheduleRule(rule_name=key, rule_key=key, rule_value=value, description=desc))
    db.commit()
    print(f"已初始化 {len(DEFAULT_RULES)} 条默认规则")
    db.close()


if __name__ == "__main__":
    print("正在创建数据库表...")
    init_db()
    print("数据库表创建完成")

    seed_default_rules()
    seed_default_users()

    print("数据库初始化完成！")
    print("运行: uvicorn app:app --reload --port 8000")
