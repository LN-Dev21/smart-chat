"""ORM 数据表模型：类 = 表，属性 = 列"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ChatSession(Base):
    """会话表：一次连续对话的元信息"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True)                       # 会话ID（uuid 字符串）
    title = Column(String, default="新对话", nullable=False)    # 会话标题
    created_at = Column(DateTime, default=datetime.now)         # 创建时间
    updated_at = Column(DateTime, default=datetime.now,
                        onupdate=datetime.now)                  # 最近活跃时间，自动更新

    # 关系：访问 session.messages 自动拿到该会话全部消息（删除会话级联删消息）
    messages = relationship("ChatMessage", back_populates="session",
                            cascade="all, delete-orphan")


class ChatMessage(Base):
    """消息表：一条一条的对话记录"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True)
    role = Column(String, nullable=False)       # "user" 或 "assistant"
    content = Column(Text, nullable=False)      # 消息内容
    created_at = Column(DateTime, default=datetime.now)

    session = relationship("ChatSession", back_populates="messages")
