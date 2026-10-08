"""会话记忆管理：基于 SQLite 持久化，服务重启不丢数据"""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatSession


def create_session(db: Session, title: str = "新对话") -> ChatSession:
    """新建会话，返回会话对象"""
    session = ChatSession(id=uuid.uuid4().hex, title=title)
    db.add(session)
    db.commit()
    return session


def list_sessions(db: Session) -> list[ChatSession]:
    """全部会话，按最近活跃倒序（侧边栏列表用）"""
    return list(db.scalars(select(ChatSession).order_by(ChatSession.updated_at.desc())))


def delete_session(db: Session, session_id: str) -> bool:
    """删除会话（级联删除其全部消息），返回是否删到"""
    session = db.get(ChatSession, session_id)
    if not session:
        return False
    db.delete(session)
    db.commit()
    return True


def get_messages(db: Session, session_id: str) -> list[ChatMessage]:
    """取出一个会话的全部消息（按时间正序）"""
    return list(db.scalars(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.id)
    ))


def get_history(db: Session, session_id: str) -> list[dict]:
    """取历史消息并转成 {role, content} 列表（发给大模型用）"""
    return [{"role": m.role, "content": m.content} for m in get_messages(db, session_id)]


def append(db: Session, session_id: str, user_msg: str, assistant_msg: str) -> None:
    """把一轮问答写入数据库，并维护会话元信息"""
    session = db.get(ChatSession, session_id)
    if not session:
        return
    db.add(ChatMessage(session_id=session_id, role="user", content=user_msg))
    db.add(ChatMessage(session_id=session_id, role="assistant", content=assistant_msg))
    # 企业细节：第一条消息自动生成会话标题（聊天软件都这么做的）
    if session.title == "新对话" and user_msg:
        session.title = user_msg[:16] + ("…" if len(user_msg) > 16 else "")
    db.commit()
