import json
from typing import Any

from llm import LLMClient


class TaskDecomposer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    async def run(self, optimized_prompt: str, task_type: str) -> list[dict[str, Any]]:
        system_prompt = "你是 Task Decomposer 任务拆解器，只输出 JSON 数组。"
        user_prompt = f"""
任务类型：{task_type}
优化提示词：
{optimized_prompt}

请拆解为 4 到 8 个可执行子任务。输出 JSON 数组，每项包含 step、title、description。
不要输出 JSON 以外的文字。
"""
        content = await self.llm.generate(system_prompt, user_prompt, temperature=0.2)
        try:
            return json.loads(self._strip_code_fence(content))
        except json.JSONDecodeError:
            return [
                {"step": 1, "title": "澄清目标", "description": "明确用户真正想解决的问题和最终交付物。"},
                {"step": 2, "title": "补充约束", "description": "整理背景、边界、资源、格式和质量要求。"},
                {"step": 3, "title": "生成方案", "description": "按照优化提示词给出可执行答案。"},
            ]

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        text = content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
        return text.strip()
