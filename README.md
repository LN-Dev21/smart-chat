# 智聊助手 SmartChat

基于 LangChain + FastAPI + Vue3 的企业级智能客服系统。

> 版本 v2.0.0 定稿 | 2026-10-08

## 功能

- 多轮对话（SQLite 持久化，重启不丢）
- 智能体工具调用（订单查询 / 天气 / 精确计算 / 当前时间）
- 意图路由（自动分流闲聊与工具请求）
- SSE 流式输出（打字机效果）
- 接口限流（每 IP 每分钟 20 次）
- Docker Compose 一键部署

## 技术栈

- 后端：Python 3.11+ / FastAPI / LangChain 1.x / LangGraph / SQLAlchemy / SQLite
- 前端：Vue3 / Vite / Element Plus / Axios
- 大模型：智谱 GLM-4.7（OpenAI 兼容协议）
- 部署：Docker / Nginx

## 快速启动

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# 编辑 .env 填入 LLM_API_KEY
uvicorn app.main:app --reload --port 8000
```

### 前端

```powershell
cd frontend
npm install
npm run dev
```

浏览器打开 http://localhost:5173

### Docker 一键部署

```powershell
docker compose up -d --build
```

访问 http://localhost:8080

## 接口文档

后端启动后访问 http://localhost:8000/docs
