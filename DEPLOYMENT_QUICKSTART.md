# 公网部署速查

推荐优先使用 Render 后端 + Vercel 前端。这样最容易拿到两个公网链接，其中提交给老师的是 Vercel 前端链接。

## 方案 A：Render + Vercel

### 1. 推送到 GitHub

将 `universal-problem-optimizer-agent` 文件夹作为仓库根目录推送到 GitHub。

### 2. 部署后端到 Render

Render 新建 Web Service 后填写：

```text
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
```

环境变量：

```env
LLM_PROVIDER=mock
CORS_ORIGINS=*
```

如果用 OpenAI：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=你的真实 Key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
CORS_ORIGINS=*
```

部署完成后复制 Render 地址，例如：

```text
https://universal-problem-optimizer-agent-api.onrender.com
```

### 3. 部署前端到 Vercel

Vercel 导入同一个 GitHub 仓库后填写：

```text
Root Directory: frontend
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
```

环境变量：

```env
VITE_API_BASE_URL=https://你的-render-后端地址.onrender.com
```

部署完成后获得 Vercel 前端地址，例如：

```text
https://universal-problem-optimizer-agent.vercel.app
```

这个 Vercel 链接就是可以提交给老师的公网访问链接。

## 方案 B：Hugging Face Spaces 一体化部署

适合只想要一个平台、一个链接的情况。

1. 创建 Hugging Face Space。
2. SDK 选择 Docker。
3. 把本项目根目录内容上传到 Space 仓库。
4. Space 的 README YAML 需要包含：

```yaml
---
title: Universal Problem Optimizer Agent
emoji: 🧠
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---
```

5. 在 Space Settings 设置环境变量：

```env
LLM_PROVIDER=mock
CORS_ORIGINS=*
```

或设置真实 OpenAI/Qwen API Key。

项目根目录已经提供 `Dockerfile`，会自动构建前端并用 FastAPI 托管静态页面和 API。

## 部署后检查

打开公网链接后依次确认：

- 页面能正常打开；
- 示例问题已预填；
- 点击“开始优化”后日志开始滚动；
- 页面展示问题分析、优化提示词、任务拆解、最终答案；
- “下载 PDF 报告”按钮可打开或下载 PDF。
