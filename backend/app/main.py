"""FastAPI 服务入口：中间件（日志+限流）+ 会话管理 + 全部对话接口"""
import json
import logging
import time
from collections import defaultdict

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage
from sqlalchemy.orm import Session

from app import memory
from app.agent import agent_chat
from app.config import RATE_LIMIT, SYSTEM_PROMPT
from app.database import SessionLocal, init_db
from app.llm import chat, classify_intent, llm, to_messages
from app.schemas import ChatRequest, ChatResponse, MessageOut, SessionOut

# ============ 日志配置 ============
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smart-chat")

init_db()   # 启动时自动建表

app = FastAPI(title="智聊助手 API", version="2.0.0")

# CORS 跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ 依赖注入：每个请求自动分配一个数据库连接 ============
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ 日志中间件：每个请求自动记录路径、状态码、耗时 ============
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    cost = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} 耗时 {cost:.0f}ms")
    return response


# ============ 限流中间件：滑动窗口，每 IP 每分钟最多 RATE_LIMIT 次 /api 请求 ============
_rate_store: dict[str, list[float]] = defaultdict(list)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        _rate_store[ip] = [t for t in _rate_store[ip] if now - t < 60]
        if len(_rate_store[ip]) >= RATE_LIMIT:
            return JSONResponse(
                status_code=429,
                content={"code": 429, "message": "请求过于频繁，请稍后再试"},
            )
        _rate_store[ip].append(now)
    return await call_next(request)


# ============ 健康检查 ============
@app.get("/")
def index():
    return {"message": "智聊助手后端运行中，接口文档见 /docs"}


# ============ 会话管理接口 ============
@app.get("/api/sessions", response_model=list[SessionOut])
def list_sessions_api(db: Session = Depends(get_db)):
    """会话列表（前端侧边栏用）"""
    return memory.list_sessions(db)


@app.post("/api/sessions", response_model=SessionOut)
def create_session_api(db: Session = Depends(get_db)):
    """新建会话"""
    return memory.create_session(db)


@app.delete("/api/sessions/{session_id}", response_model=ChatResponse)
def delete_session_api(session_id: str, db: Session = Depends(get_db)):
    """删除会话及其全部消息"""
    if not memory.delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return ChatResponse(code=0, message="已删除", data={})


@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages_api(session_id: str, db: Session = Depends(get_db)):
    """某会话的全部历史消息"""
    return memory.get_messages(db, session_id)


# ============ 普通对话接口 ============
@app.post("/api/chat", response_model=ChatResponse)
def chat_api(req: ChatRequest, db: Session = Depends(get_db)):
    """多轮对话：取历史 → 带历史调模型 → 结果落库"""
    try:
        history = memory.get_history(db, req.session_id)
        reply = chat(req.message, history)
        memory.append(db, req.session_id, req.message, reply)
        return ChatResponse(code=0, message="success", data={"reply": reply})
    except Exception as e:
        logger.error(f"/api/chat 异常: {e}")
        return ChatResponse(code=500, message=f"AI 服务异常：{str(e)}", data={"reply": ""})


# ============ 智能体对话接口 ============
@app.post("/api/agent/chat", response_model=ChatResponse)
def agent_chat_api(req: ChatRequest, db: Session = Depends(get_db)):
    """智能体对话：工具调用 + 记忆持久化，结果同步写入业务库"""
    try:
        result = agent_chat(req.message, req.session_id)
        tools = result["tools_used"]
        record = (f"🔧 [调用工具：{'、'.join(tools)}]\n\n" + result["reply"]) if tools else result["reply"]
        memory.append(db, req.session_id, req.message, record)
        return ChatResponse(code=0, message="success", data={
            "reply": result["reply"],
            "tools_used": tools,
        })
    except Exception as e:
        logger.error(f"/api/agent/chat 异常: {e}")
        return ChatResponse(code=500, message=f"智能体服务异常：{str(e)}", data={"reply": ""})


# ============ 统一入口：意图路由 ============
@app.post("/api/smart/chat", response_model=ChatResponse)
def smart_chat_api(req: ChatRequest, db: Session = Depends(get_db)):
    """统一入口：先意图识别，再自动路由到普通对话或智能体"""
    try:
        intent = classify_intent(req.message)
        if intent == "agent":
            result = agent_chat(req.message, req.session_id)
            tools = result["tools_used"]
            record = (f"🔧 [调用工具：{'、'.join(tools)}]\n\n" + result["reply"]) if tools else result["reply"]
            memory.append(db, req.session_id, req.message, record)
            return ChatResponse(code=0, message="success", data={
                "route": "agent", "reply": result["reply"], "tools_used": tools,
            })
        history = memory.get_history(db, req.session_id)
        reply = chat(req.message, history)
        memory.append(db, req.session_id, req.message, reply)
        return ChatResponse(code=0, message="success", data={"route": "chat", "reply": reply})
    except Exception as e:
        logger.error(f"/api/smart/chat 异常: {e}")
        return ChatResponse(code=500, message=f"服务异常：{str(e)}", data={"reply": ""})


# ============ 流式对话接口（SSE）============
@app.post("/api/chat/stream")
async def chat_stream_api(req: ChatRequest, db: Session = Depends(get_db)):
    """流式对话接口（SSE）：逐字推送 AI 回复"""
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    messages.extend(to_messages(memory.get_history(db, req.session_id)))
    messages.append(HumanMessage(content=req.message))

    async def event_generator():
        full_reply = ""
        try:
            async for chunk in llm.astream(messages):
                if chunk.content:
                    full_reply += chunk.content
                    yield f"data: {json.dumps({'delta': chunk.content}, ensure_ascii=False)}\n\n"
            memory.append(db, req.session_id, req.message, full_reply)
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
