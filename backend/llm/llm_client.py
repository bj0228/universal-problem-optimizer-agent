import json
import os
from typing import Any

import httpx


class LLMClient:
    """Small public-API LLM client with a deterministic mock fallback."""

    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "mock").strip().lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.qwen_model = os.getenv("QWEN_MODEL", "qwen-plus")

        if self.provider == "openai" and not self.openai_api_key:
            self.provider = "mock"
        if self.provider == "qwen" and not self.dashscope_api_key:
            self.provider = "mock"

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        if self.provider == "openai":
            return await self._openai_chat(system_prompt, user_prompt, temperature)
        if self.provider == "qwen":
            return await self._qwen_chat(system_prompt, user_prompt, temperature)
        return self._mock_response(system_prompt, user_prompt)

    async def _openai_chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        url = f"{self.openai_base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.openai_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.openai_api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    async def _qwen_chat(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": self.qwen_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
        }
        headers = {"Authorization": f"Bearer {self.dashscope_api_key}", "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        lower = f"{system_prompt}\n{user_prompt}".lower()
        question = self._extract_question(user_prompt)

        if "problem diagnoser" in lower or "问题诊断器" in lower:
            return (
                "## 问题诊断\n"
                "- 目标清晰度：用户希望获得完整方案，但尚未明确研究对象、应用边界和成果形式。\n"
                "- 条件完整性：缺少数据来源、评估指标、伦理合规、时间资源等限制条件。\n"
                "- 输出格式：未指定研究方案结构、篇幅和是否需要表格。\n"
                "- 任务规模：问题包含背景、技术路线、创新点、实验设计，适合拆解为多阶段任务。\n"
                "- 背景信息：需要补充多模态数据类型、心理健康场景和目标使用者。\n"
                "- 优化建议：明确角色、任务目标、约束条件、输出格式和质量标准。"
            )

        if "prompt optimizer" in lower or "提示词优化器" in lower:
            return (
                "你是一名具备人工智能、医学信息学与科研方法经验的研究方案顾问。请围绕以下主题生成一份可执行研究方案："
                f"{question}\n\n"
                "要求：1. 先说明研究背景与问题价值；2. 明确研究目标、研究问题和应用边界；"
                "3. 给出多模态数据来源、模型架构、技术路线和实验流程；4. 提炼3个创新点；"
                "5. 设计实验对照、评价指标、风险控制与伦理合规方案；6. 使用标题、表格和步骤化列表输出；"
                "7. 语言专业、结构完整、可用于开题或课程作业。"
            )

        if "task decomposer" in lower or "任务拆解器" in lower:
            return json.dumps(
                [
                    {"step": 1, "title": "明确研究范围", "description": "界定心理健康辅助诊断场景、目标用户和多模态数据类型。"},
                    {"step": 2, "title": "梳理研究背景", "description": "说明现有心理健康评估痛点、多模态大模型优势和应用价值。"},
                    {"step": 3, "title": "设计技术路线", "description": "规划数据采集、预处理、特征融合、模型训练、推理和人机协同流程。"},
                    {"step": 4, "title": "提炼创新点", "description": "从多模态融合、可解释性、伦理安全和临床协作角度提炼创新。"},
                    {"step": 5, "title": "制定实验方案", "description": "设计数据集、基线模型、评价指标、消融实验和风险控制。"},
                    {"step": 6, "title": "生成最终方案", "description": "整合背景、目标、路线、创新、实验和预期成果。"},
                ],
                ensure_ascii=False,
            )

        if "solution generator" in lower or "答案生成器" in lower:
            return (
                "## 最终研究方案\n\n"
                "### 1. 研究背景\n"
                "心理健康筛查和辅助诊断通常依赖量表、访谈和医生经验，存在主观性强、连续监测不足、早期风险识别滞后等问题。"
                "多模态大模型能够融合文本、语音、面部表情、行为轨迹和生理信号，为心理状态评估提供更丰富的证据链。\n\n"
                "### 2. 研究目标\n"
                "构建一个面向抑郁、焦虑等常见心理健康风险的多模态辅助诊断框架，用于风险筛查、解释性提示和医生决策支持，"
                "不替代临床诊断。\n\n"
                "### 3. 技术路线\n"
                "| 阶段 | 内容 | 产出 |\n| --- | --- | --- |\n"
                "| 数据采集 | 量表文本、访谈语音、表情视频、行为日志 | 脱敏多模态数据集 |\n"
                "| 数据处理 | ASR转写、情绪特征、视觉表情特征、缺失值处理 | 统一样本表示 |\n"
                "| 模型建模 | 文本编码器、语音编码器、视觉编码器和跨模态融合模块 | 风险预测模型 |\n"
                "| 解释输出 | 生成风险因素摘要、证据片段和建议转介等级 | 可解释报告 |\n"
                "| 人机协同 | 医生复核、反馈标注、持续优化 | 闭环评估体系 |\n\n"
                "### 4. 创新点\n"
                "1. 将访谈文本、声学特征、面部表情和量表结果统一到多模态推理框架中。\n"
                "2. 在输出中加入证据引用和风险解释，增强医生可用性。\n"
                "3. 将伦理合规、隐私保护和人类专家复核设计为系统核心流程。\n\n"
                "### 5. 实验设计\n"
                "- 对照模型：传统机器学习、单模态深度学习、多模态融合模型。\n"
                "- 指标：AUC、F1、召回率、校准误差、解释一致性、医生满意度。\n"
                "- 消融实验：移除语音、视觉、文本、量表等模态，评估各模态贡献。\n"
                "- 安全评估：测试偏见、幻觉、隐私泄露和高风险误判场景。\n\n"
                "### 6. 风险与伦理\n"
                "系统仅用于辅助筛查；所有数据需获得知情同意并脱敏处理；高风险个体必须进入人工复核和专业转介流程。"
            )

        return f"已基于问题生成结构化辅助内容：{question}"

    @staticmethod
    def _extract_question(prompt: str) -> str:
        for marker in ["原始问题：", "用户问题：", "Question:"]:
            if marker in prompt:
                return prompt.split(marker, 1)[1].strip().split("\n", 1)[0]
        return prompt.strip()[:300]
