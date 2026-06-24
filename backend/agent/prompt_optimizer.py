from llm import LLMClient


class PromptOptimizer:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    async def run(self, question: str, task_type: str, analysis: str) -> str:
        system_prompt = "你是 Prompt Optimizer 提示词优化器，擅长把模糊问题改写为高质量可执行提示词。"
        user_prompt = f"""
任务类型：{task_type}
原始问题：{question}
诊断结果：
{analysis}

请生成适用于“单次自动化求解”的优化提示词，必须包含角色、目标、输入条件、输出格式、步骤化要求、约束条件和质量标准。
重要：不要要求用户确认、补充信息或等待下一轮对话。对于尚未提供的条件，请要求模型采用合理的默认假设，并在结果开头明确列出这些假设，然后一次性完成完整方案。
只输出优化后的提示词正文。
"""
        return await self.llm.generate(system_prompt, user_prompt)
