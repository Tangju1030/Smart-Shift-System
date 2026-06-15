"""AI 辅助 API"""

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from services.ai_service import AIService, AIProvider

router = APIRouter(prefix="/api/ai", tags=["AI助手"])

# 全局 AI 服务实例（可在 app 启动时配置）
ai_service: AIService | None = None


def get_ai_service() -> AIService:
    if ai_service is None:
        raise HTTPException(status_code=503, detail="AI 服务未配置，请在环境变量中设置 API_KEY")
    return ai_service


class OptimizeRequest(BaseModel):
    current_rules: dict = Field(..., description="当前规则配置")
    history_data: dict = Field(..., description="历史值班统计")
    availability_summary: dict = Field(..., description="课表概况")


class ExplainRequest(BaseModel):
    week_no: int = Field(..., description="周次")
    schedule_data: dict = Field(..., description="排班结果")
    user_history: dict = Field(..., description="各成员历史次数")


class ChatRequest(BaseModel):
    message: str = Field(..., description="用户消息")
    context: dict = Field(default_factory=dict, description="系统上下文")


class ChatResponse(BaseModel):
    reply: str


@router.post("/optimize-rule")
async def optimize_rules(req: OptimizeRequest):
    """AI 规则优化建议"""
    svc = get_ai_service()
    suggestion = await svc.optimize_rules(
        req.current_rules,
        req.history_data,
        req.availability_summary,
    )
    return {"suggestion": suggestion}


@router.post("/explain-schedule")
async def explain_schedule(req: ExplainRequest):
    """AI 解释排班结果"""
    svc = get_ai_service()
    explanation = await svc.explain_schedule(
        req.week_no,
        req.schedule_data,
        req.user_history,
    )
    return {"explanation": explanation}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """AI 自由对话"""
    svc = get_ai_service()
    reply = await svc.chat(req.message, req.context)
    return ChatResponse(reply=reply)
