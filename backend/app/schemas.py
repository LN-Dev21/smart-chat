"""请求与响应的数据模型：接口的"合同"，前后端都照此开发"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """对话请求体"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: str = Field(..., description="会话ID")


class ChatResponse(BaseModel):
    """统一响应体：code=0 成功，非 0 失败"""
    code: int = 0
    message: str = "success"
    data: dict = {}


class SessionOut(BaseModel):
    """会话信息（返回给前端的格式）"""
    model_config = ConfigDict(from_attributes=True)   # 允许直接从 ORM 对象转换

    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageOut(BaseModel):
    """消息内容（返回给前端的格式）"""
    model_config = ConfigDict(from_attributes=True)

    role: str
    content: str
    created_at: datetime


class Intent(BaseModel):
    """意图分类结果（供 /api/smart/chat 意图路由使用）"""
    intent: Literal["chat", "agent"] = Field(
        description="chat=日常问答闲聊；agent=需要订单/天气/时间/计算等工具的请求"
    )
