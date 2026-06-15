"""AI 辅助服务 — 统一的 LLM 接口"""

import json
import os
from typing import AsyncIterator
from abc import ABC, abstractmethod


class AIProvider(ABC):
    """AI 供应商抽象基类"""

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str:
        ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        ...


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model

    async def chat(self, messages: list[dict], **kwargs) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        resp = await client.chat.completions.create(
            model=self.model, messages=messages, **kwargs
        )
        return resp.choices[0].message.content or ""

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        stream = await client.chat.completions.create(
            model=self.model, messages=messages, stream=True, **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class DeepSeekProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = "https://api.deepseek.com/v1"

    async def chat(self, messages: list[dict], **kwargs) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        resp = await client.chat.completions.create(
            model=self.model, messages=messages, **kwargs
        )
        return resp.choices[0].message.content or ""

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        stream = await client.chat.completions.create(
            model=self.model, messages=messages, stream=True, **kwargs
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AIService:
    """AI 辅助服务"""

    PROVIDERS = {
        "openai": OpenAIProvider,
        "deepseek": DeepSeekProvider,
        "claude": None,   # 预留
        "gemini": None,   # 预留
    }

    def __init__(self, provider: str = "deepseek", api_key: str | None = None, model: str | None = None):
        provider_cls = self.PROVIDERS.get(provider)
        if provider_cls is None:
            raise ValueError(f"不支持的 AI 供应商: {provider}")
        self.provider = provider_cls(api_key=api_key, model=model or "")
        self.provider_name = provider

    def _build_system_prompt(self) -> str:
        return """你是一个智能排班助手，帮助分析年委值班排班方案。
你需要根据提供的数据，给出优化建议或对排班结果进行解释。
回答应简洁、具体、可操作。使用中文回答。"""

    async def optimize_rules(
        self,
        current_rules: dict,
        history_data: dict,
        availability_summary: dict,
    ) -> str:
        """AI 规则优化建议"""
        prompt = f"""
当前排班规则配置：
{json.dumps(current_rules, ensure_ascii=False, indent=2)}

历史值班统计：
{json.dumps(history_data, ensure_ascii=False, indent=2)}

课表概况（空闲时段数）：
{json.dumps(availability_summary, ensure_ascii=False, indent=2)}

请分析当前规则配置是否合理，并给出具体的优化建议。
例如：
- 每周最大值班次数是否合适？
- 每时段人数分配是否合理？
- 如果极差较大，如何调整均衡权重？

请给出3-5条可操作的优化建议。"""

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        return await self.provider.chat(messages, temperature=0.3)

    async def explain_schedule(
        self,
        week_no: int,
        schedule_data: dict,
        user_history: dict,
    ) -> str:
        """AI 解释排班结果"""
        prompt = f"""
第{week_no}周排班结果：
{json.dumps(schedule_data, ensure_ascii=False, indent=2)}

各成员历史累计值班次数：
{json.dumps(user_history, ensure_ascii=False, indent=2)}

请用自然语言解释本周排班方案的合理性，重点说明：
1. 哪些人被安排了较多/较少值班，为什么？
2. 排班的公平性如何？
3. 是否有改进空间？

请用中文回答，语气友好专业。"""

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        return await self.provider.chat(messages, temperature=0.5)

    async def chat(self, message: str, context: dict) -> str:
        """自由对话"""
        prompt = f"""
当前系统上下文：
{json.dumps(context, ensure_ascii=False, indent=2)}

用户提问：{message}

请根据上下文回答用户的问题。回答应准确、有帮助。"""

        messages = [
            {"role": "system", "content": self._build_system_prompt()},
            {"role": "user", "content": prompt},
        ]
        return await self.provider.chat(messages, temperature=0.7)
