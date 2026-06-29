"""LLM服务模块"""

import json
import os
from openai import OpenAI
from ..config import get_settings


class MyAgentsLLM:
    """LLM 客户端封装（调 DeepSeek，兼容 OpenAI API）"""

    def __init__(self):
        settings = get_settings()
        self.api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or settings.openai_api_key
        self.base_url = os.getenv("LLM_BASE_URL") or settings.openai_base_url
        self.model = os.getenv("LLM_MODEL_ID") or settings.openai_model

        if not self.api_key:
            raise ValueError("LLM_API_KEY 或 OPENAI_API_KEY 未配置")

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def invoke_with_tools(self, messages: list, tools: list = None, **kwargs):
        """调用 LLM，支持 Function Calling / Tools"""
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.3),
        }
        if tools:
            params["tools"] = tools
            params["tool_choice"] = "auto"

        resp = self._client.chat.completions.create(**params)
        return resp.choices[0].message


class ToolAgent:
    """具有工具调用能力的真 Agent —— LLM 作为大脑，自主决定何时调用工具"""

    def __init__(self, name: str, llm: MyAgentsLLM, system_prompt: str,
                 tools: list = None, tool_map: dict = None):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.tool_map = tool_map or {}

    def run(self, user_query: str, max_rounds: int = 5) -> str:
        """
        执行 Agent 任务：LLM 自主决策 → 调工具 → 分析结果 → 可能再调工具 → 返回最终答案
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_query}
        ]

        for _ in range(max_rounds):
            msg = self.llm.invoke_with_tools(messages, self.tools)

            # 没有 tool_calls = LLM 认为任务完成，返回最终内容
            if not msg.tool_calls:
                return msg.content or ""

            # 把 assistant 消息（含 tool_calls）加入对话历史
            assistant_msg = {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments}
                    }
                    for tc in msg.tool_calls
                ]
            }
            messages.append(assistant_msg)

            # 逐一执行 LLM 请求的工具调用
            for tc in msg.tool_calls:
                func_name = tc.function.name
                func = self.tool_map.get(func_name)

                if func:
                    try:
                        args = json.loads(tc.function.arguments)
                        result = func(**args)
                    except Exception as e:
                        result = {"error": str(e)}
                    tool_result = json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result
                else:
                    tool_result = json.dumps({"error": f"未知工具: {func_name}"}, ensure_ascii=False)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result
                })

        return "Agent 未在预期轮数内完成任务"

