"""规则配置 API"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from services.rule_service import RuleService
from schemas.rule import RuleOut, RulesConfig, RuleUpdate

router = APIRouter(prefix="/api/rules", tags=["规则配置"])


@router.get("/", response_model=list[RuleOut])
def list_rules(db: Session = Depends(get_db)):
    """获取所有规则"""
    svc = RuleService(db)
    return svc.get_all()


@router.get("/config", response_model=RulesConfig)
def get_config(db: Session = Depends(get_db)):
    """获取解析后的排班配置"""
    svc = RuleService(db)
    return svc.get_config()


@router.put("/config", response_model=RulesConfig)
def update_config(config: RulesConfig, db: Session = Depends(get_db)):
    """更新全部规则配置"""
    svc = RuleService(db)
    updates = {
        "max_weekly_shifts": str(config.max_weekly_shifts),
        "allow_consecutive_days": str(config.allow_consecutive_days).lower(),
        "balance_weight": str(config.balance_weight),
        "randomness_weight": str(config.randomness_weight),
        "search_iterations": str(config.search_iterations),
    }
    import json
    updates["period_capacities"] = json.dumps(config.period_capacities, ensure_ascii=False)
    updates["duty_slots"] = json.dumps(config.duty_slots, ensure_ascii=False)
    updates["weekdays"] = json.dumps(config.weekdays, ensure_ascii=False)

    svc.batch_update(updates)
    return svc.get_config()


@router.put("/{rule_key}", response_model=RuleOut)
def update_rule(rule_key: str, data: RuleUpdate, db: Session = Depends(get_db)):
    """更新单个规则"""
    svc = RuleService(db)
    if data.rule_value is None:
        raise HTTPException(status_code=400, detail="rule_value 不能为空")
    rule = svc.update_rule(rule_key, data.rule_value)
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    return rule
