import json
import re
from typing import Any

from llm import LLMClient


class SolutionGenerator:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    async def run(self, question: str, optimized_prompt: str, steps: list[dict[str, Any]], tool_summary: str) -> str:
        system_prompt = "你是 Solution Generator 答案生成器，负责基于优化提示词和拆解步骤生成最终高质量答案。"
        user_prompt = f"""
原始问题：{question}

优化提示词：
{optimized_prompt}

任务拆解：
{steps}

工具摘要：
{tool_summary}

请给出结构完整、可直接使用的最终答案。使用 Markdown 输出。
"""
        return await self.llm.generate(system_prompt, user_prompt)

    async def run_plan_once(self, question: str, task_type: str) -> dict[str, Any]:
        """Generate the diagnostic and plan artifacts in one public-LLM call."""
        system_prompt = "你是 Universal Problem Optimizer Agent 的规划阶段。你必须严格只输出合法 JSON，不要输出 Markdown 代码块或任何解释。"
        user_prompt = f"""
用户原始问题：{question}
任务类型：{task_type}

请一次性完成问题诊断、提示词优化和任务拆解。对于缺少的信息采用合理默认假设，并在优化提示词中明确要求最终答案标注这些假设。
请输出以下 JSON 结构：
{{
  "analysis": "结构化问题分析，使用中文 Markdown 标题和列表",
  "optimized_prompt": "可直接复用的高质量提示词；不得要求用户确认、等待或进行下一轮对话",
  "steps": [
    {{"step": 1, "title": "子任务标题", "description": "具体说明"}}
  ]
}}

约束：steps 必须包含 4 到 8 项；内容必须针对用户原始问题，不要输出泛化模板；分析和提示词保持精炼。
"""
        content = await self.llm.generate(system_prompt, user_prompt, temperature=0.25)
        try:
            data = json.loads(self._json_text(content))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"模型未返回可解析的结构化结果：{content[:500]}") from exc

        required = ("analysis", "optimized_prompt", "steps")
        if not all(data.get(key) for key in required) or not isinstance(data["steps"], list):
            raise RuntimeError("模型返回的结构化结果缺少 analysis、optimized_prompt 或 steps。")
        return data

    @staticmethod
    def _json_text(content: str) -> str:
        text = content.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
        start, end = text.find("{"), text.rfind("}")
        return text[start : end + 1] if start >= 0 and end > start else text
