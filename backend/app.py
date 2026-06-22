import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from agent import ProblemDiagnoser, PromptOptimizer, ReportGenerator, SolutionGenerator, TaskDecomposer, ToolCaller
from llm import LLMClient

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
REPORT_DIR = BASE_DIR / "reports"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"

app = FastAPI(title="Universal Problem Optimizer Agent API", version="1.0.0")

origins_raw = os.getenv("CORS_ORIGINS", "*")
origins = ["*"] if origins_raw == "*" else [origin.strip() for origin in origins_raw.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OptimizeRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=10000)
    task_type: str = Field("通用类", max_length=50)


class OptimizeResponse(BaseModel):
    analysis: str
    optimized_prompt: str
    steps: list[dict[str, Any]]
    solution: str
    report_id: str
    logs: list[str]


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "Universal Problem Optimizer Agent", "status": "running"}


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": os.getenv("LLM_PROVIDER", "mock")}


@app.post("/api/optimize", response_model=OptimizeResponse)
async def optimize(request: OptimizeRequest) -> OptimizeResponse:
    logs: list[str] = []

    try:
        llm = LLMClient()
        diagnoser = ProblemDiagnoser(llm)
        optimizer = PromptOptimizer(llm)
        decomposer = TaskDecomposer(llm)
        tools = ToolCaller()
        solution_generator = SolutionGenerator(llm)
        report_generator = ReportGenerator(REPORT_DIR)

        logs.append("正在分析问题：检查目标、条件、约束和输出格式。")
        analysis = await diagnoser.run(request.question, request.task_type)

        logs.append("正在优化提示词：补充角色、任务目标、步骤和质量标准。")
        optimized_prompt = await optimizer.run(request.question, request.task_type, analysis)

        logs.append("正在拆解任务：将复杂问题分解为可执行子任务。")
        steps = await decomposer.run(optimized_prompt, request.task_type)

        logs.append("正在调用文本摘要工具：压缩问题诊断与优化结果。")
        summary = tools.summarize_text(f"{analysis}\n{optimized_prompt}", max_chars=700)

        logs.append("正在调用关键词提取工具：抽取核心概念。")
        keywords = tools.extract_keywords(f"{request.question}\n{optimized_prompt}")

        logs.append("正在调用结构化输出工具：整理任务拆解 Markdown。")
        steps_markdown = tools.format_steps_markdown(steps)
        tool_logs = [
            f"文本摘要工具输出：{summary}",
            f"关键词提取工具输出：{', '.join(keywords)}",
            f"结构化输出工具输出：\n{steps_markdown}",
        ]

        logs.append("正在生成最终答案：基于优化提示词和任务拆解完成求解。")
        solution = await solution_generator.run(request.question, optimized_prompt, steps, "\n".join(tool_logs))

        logs.append("正在生成 PDF 报告：汇总完整求解过程。")
        report_id, _ = report_generator.generate(
            {
                "question": request.question,
                "task_type": request.task_type,
                "analysis": analysis,
                "optimized_prompt": optimized_prompt,
                "steps": steps,
                "tool_logs": tool_logs,
                "solution": solution,
            }
        )

        logs.append("智能体流程完成：报告已生成，可下载。")
        return OptimizeResponse(
            analysis=analysis,
            optimized_prompt=optimized_prompt,
            steps=steps,
            solution=solution,
            report_id=report_id,
            logs=logs,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"智能体运行失败：{exc}") from exc


@app.get("/api/report/{report_id}")
async def download_report(report_id: str) -> FileResponse:
    safe_name = Path(report_id).name
    path = REPORT_DIR / safe_name
    if not path.exists() or path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="报告不存在或已过期。")
    return FileResponse(str(path), media_type="application/pdf", filename=safe_name)


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", response_class=HTMLResponse)
    async def serve_frontend(full_path: str) -> FileResponse:
        index_file = FRONTEND_DIST / "index.html"
        if not index_file.exists():
            raise HTTPException(status_code=404, detail="前端构建产物不存在。")
        return FileResponse(str(index_file))
