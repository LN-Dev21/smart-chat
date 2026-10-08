"""FastAPI 服务入口：会话管理 + 多轮对话接口（第1课版本）"""
import logging
import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import memory
from app.database import SessionLocal, init_db
from app.llm import chat
from app.schemas import ChatRequest, ChatResponse, MessageOut, SessionOut

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("smart-chat")

init_db()

app = FastAPI(title="智聊助手 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    cost = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} 耗时 {cost:.0f}ms")
    return response


@app.get("/")
def index():
    return {"message": "智聊助手后端运行中，接口文档见 /docs"}


@app.get("/api/sessions", response_model=list[SessionOut])
def list_sessions_api(db: Session = Depends(get_db)):
    return memory.list_sessions(db)


@app.post("/api/sessions", response_model=SessionOut)
def create_session_api(db: Session = Depends(get_db)):
    return memory.create_session(db)


@app.delete("/api/sessions/{session_id}", response_model=ChatResponse)
def delete_session_api(session_id: str, db: Session = Depends(get_db)):
    if not memory.delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    return ChatResponse(code=0, message="已删除", data={})


@app.get("/api/sessions/{session_id}/messages", response_model=list[MessageOut])
def get_messages_api(session_id: str, db: Session = Depends(get_db)):
    return memory.get_messages(db, session_id)


@app.post("/api/chat", response_model=ChatResponse)
def chat_api(req: ChatRequest, db: Session = Depends(get_db)):
    try:
        history = memory.get_history(db, req.session_id)
        reply = chat(req.message, history)
        memory.append(db, req.session_id, req.message, reply)
        return ChatResponse(code=0, message="success", data={"reply": reply})
    except Exception as e:
        logger.error(f"/api/chat 异常: {e}")
        return ChatResponse(code=500, message=f"AI 服务异常：{str(e)}", data={"reply": ""})
