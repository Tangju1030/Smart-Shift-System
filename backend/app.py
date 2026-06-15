"""智能年委排班系统 — FastAPI 入口"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routers import users, rules, schedule, availability, ai
from services.ai_service import AIService

app = FastAPI(
    title="智能年委排班系统",
    description="支持可视化配置排班规则、自动生成排班结果、AI辅助优化的Web系统",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(users.router)
app.include_router(rules.router)
app.include_router(schedule.router)
app.include_router(availability.router)
app.include_router(ai.router)


@app.on_event("startup")
async def startup():
    """启动时初始化数据库和AI服务"""
    init_db()

    # 配置 AI 服务（从环境变量读取）
    ai_provider = os.getenv("AI_PROVIDER", "deepseek")
    ai_api_key = os.getenv("AI_API_KEY", "")
    ai_model = os.getenv("AI_MODEL", "")

    if ai_api_key:
        ai.ai_service = AIService(
            provider=ai_provider,
            api_key=ai_api_key,
            model=ai_model or None,
        )
        print(f"AI 服务已配置: {ai_provider}")
    else:
        print("AI 服务未配置，AI 相关接口将返回503")


@app.get("/")
async def root():
    return {"name": "智能年委排班系统", "version": "1.0.0", "status": "running"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
