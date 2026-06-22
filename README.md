# Universal Problem Optimizer Agent

通用问题优化智能体是一个前后端完整 Web 应用，用于自动分析、优化、拆解并辅助求解用户原始问题。系统支持公开大模型 API，例如 OpenAI GPT API 和阿里通义千问 API；没有 API Key 时会自动使用 mock 模式，方便本地演示和录制 MP4。

## 功能说明

- 问题诊断：分析目标不清晰、条件缺失、输出格式不明确、约束不足、问题过大、需要拆解、缺少背景信息等问题。
- 提示词优化：把原始问题改写为更适合大模型求解的高质量提示词。
- 任务拆解：将复杂任务拆解为多个可执行子任务。
- 轻量工具调用：提供文本摘要、关键词提取、结构化 Markdown 输出和 PDF 报告生成。
- 答案生成：基于优化提示词和任务拆解生成最终答案。
- PDF 报告：自动生成包含完整求解过程的 PDF。
- 前端演示：Vue 3 页面展示输入、任务类型、运行日志、优化结果和 PDF 下载按钮。

## 技术栈

- 前端：Vue 3、Vite、Axios、Element Plus、Marked
- 后端：FastAPI、Pydantic、httpx、python-dotenv
- PDF：ReportLab
- LLM：OpenAI-compatible API、DashScope/Qwen API、Mock fallback

## 项目结构

```text
universal-problem-optimizer-agent/
├── backend/
│   ├── app.py
│   ├── agent/
│   ├── llm/
│   ├── reports/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   └── src/
├── demo_materials/
│   ├── demo_script.md
│   └── sample_question.md
└── README.md
```

## 环境配置

后端配置文件位于 `backend/.env.example`。本地运行时复制为 `.env`：

```bash
cd backend
cp .env.example .env
```

### Mock 模式

无需 API Key，适合演示：

```env
LLM_PROVIDER=mock
CORS_ORIGINS=*
```

### OpenAI API

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=*
```

### 通义千问 API

```env
LLM_PROVIDER=qwen
DASHSCOPE_API_KEY=your_dashscope_api_key_here
QWEN_MODEL=qwen-plus
CORS_ORIGINS=*
```

注意：不要把真实 API Key 提交到代码仓库。

## 后端启动

```bash
cd universal-problem-optimizer-agent/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

## 前端启动

```bash
cd universal-problem-optimizer-agent/frontend
npm install
npm run dev
```

打开：

```text
http://127.0.0.1:5173
```

本地开发时 Vite 已将 `/api` 代理到 `http://127.0.0.1:8000`。

## API 接口

### POST `/api/optimize`

请求：

```json
{
  "question": "用户输入的问题",
  "task_type": "科研类"
}
```

响应：

```json
{
  "analysis": "问题分析",
  "optimized_prompt": "优化后的问题/提示词",
  "steps": [
    {
      "step": 1,
      "title": "子任务标题",
      "description": "子任务说明"
    }
  ],
  "solution": "最终答案",
  "report_id": "problem_optimization_report_20260611_120000.pdf",
  "logs": ["运行日志1", "运行日志2"]
}
```

### GET `/api/report/{report_id}`

下载自动生成的 PDF 报告。

## PDF 中文字体

ReportLab 会尝试加载以下字体：

- `CHINESE_FONT_PATH` 环境变量指定的字体；
- macOS 的 PingFang 或 STHeiti；
- Linux 的 Noto Sans CJK 或文泉驿字体；
- 如果都找不到，则回退到 Helvetica。

如果部署环境生成中文 PDF 时出现方块字，建议安装 Noto CJK 字体，并设置：

```env
CHINESE_FONT_PATH=/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc
```

## 演示问题

```text
我想写一份关于“多模态大模型在心理健康辅助诊断中的应用”的研究方案，但不知道怎么拆解研究背景、技术路线、创新点和实验设计，请帮我优化这个问题并给出完整解决方案。
```

推荐任务类型：科研类。

## 预期输出效果

- 原始问题分析：指出目标、条件、约束、输出格式和背景信息缺失。
- 优化后的提示词：包含角色、目标、步骤、约束和质量标准。
- 问题拆解步骤：输出 4 到 8 个子任务。
- 推荐求解路径和最终答案：给出完整研究方案。
- PDF 报告：文件名格式为 `problem_optimization_report_{timestamp}.pdf`。

## 部署方案 A：Render 后端 + Vercel 前端

### Render 部署后端

1. 将项目推送到 GitHub。
2. 在 Render 创建 Web Service。
3. Root Directory 设置为 `universal-problem-optimizer-agent/backend`。
4. Build Command：

```bash
pip install -r requirements.txt
```

5. Start Command：

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

6. 在 Render 环境变量中设置：

```env
LLM_PROVIDER=mock
CORS_ORIGINS=*
```

如果使用真实模型，改为配置 `LLM_PROVIDER=openai` 或 `LLM_PROVIDER=qwen`，并填入对应 API Key。

7. 部署完成后获得后端公开地址，例如：

```text
https://your-agent-backend.onrender.com
```

### Vercel 部署前端

1. 在 Vercel 导入同一个 GitHub 仓库。
2. Root Directory 设置为 `universal-problem-optimizer-agent/frontend`。
3. Build Command：

```bash
npm install && npm run build
```

4. Output Directory：

```text
dist
```

5. 设置环境变量：

```env
VITE_API_BASE_URL=https://your-agent-backend.onrender.com
```

6. 部署完成后获得前端公开访问链接，例如：

```text
https://your-agent-frontend.vercel.app
```

## 备选部署方案 B：Hugging Face Spaces

也可以将前端构建产物交给 FastAPI 托管，或使用 Docker Space 同时启动后端与静态前端。为了简化比赛提交，推荐优先使用 Render + Vercel。

## MP4 录制建议

1. 打开部署后的前端公开链接。
2. 展示系统名称和页面结构。
3. 输入 demo 问题，选择“科研类”。
4. 点击“开始优化”。
5. 展示运行日志。
6. 展示原始问题分析、优化提示词、任务拆解和最终答案。
7. 点击下载 PDF 报告，并打开 PDF。
8. 结尾说明系统满足提交要求。

完整脚本见 `demo_materials/demo_script.md`。

## 最终提交材料

- 公开访问链接：Vercel 前端链接。
- MP4 演示视频：录制 3 到 5 分钟完整流程。
- PDF 求解文档：系统下载的报告文件。

## 检查清单

- [x] 可公开访问：支持 Render + Vercel 部署。
- [x] 使用公开大模型 API：支持 OpenAI 和通义千问。
- [x] 不使用内部未公开模型。
- [x] 通过提示词工程和轻量工具调用构建智能体。
- [x] 能解决一个具体问题。
- [x] 能生成 PDF 文档。
- [x] 方便录制 MP4。
- [x] 能提交链接、视频、PDF。
