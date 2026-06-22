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
