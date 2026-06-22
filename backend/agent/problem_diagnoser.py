from llm import LLMClient


class ProblemDiagnoser:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    async def run(self, question: str, task_type: str) -> str:
        system_prompt = "你是 Problem Diagnoser 问题诊断器，负责分析用户问题缺陷并给出结构化诊断。"
        user_prompt = f"""
任务类型：{task_type}
原始问题：{question}

请从目标清晰度、条件缺失、输出格式、约束条件、任务规模、背景信息和优化建议七个方面分析。
使用 Markdown 列表输出，表达清晰具体。
"""
        return await self.llm.generate(system_prompt, user_prompt)
