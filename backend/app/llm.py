"""大模型调用封装：所有与 LLM 交互的代码集中在这里（LangChain 版）"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import API_KEY, BASE_URL, MODEL, SYSTEM_PROMPT
from app.schemas import Intent

# 对话模型：全项目共用（温度 0.7 适合日常对话）
llm = ChatOpenAI(
    model=MODEL,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0.7,
)


def to_messages(history: list[dict]) -> list:
    """把数据库查出的 {role, content} 字典历史，转成 LangChain 消息对象"""
    result = []
    for m in history:
        if m["role"] == "user":
            result.append(HumanMessage(content=m["content"]))
        else:
            result.append(AIMessage(content=m["content"]))
    return result


def chat(user_message: str, history: list[dict] | None = None) -> str:
    """
    发送一轮对话，返回 AI 的文本回复。
    :param user_message: 用户本轮输入
    :param history: 历史消息列表（多轮对话用）
    """
    messages = [SystemMessage(content=SYSTEM_PROMPT)]   # 1. 人设
    if history:
        messages.extend(to_messages(history))           # 2. 历史
    messages.append(HumanMessage(content=user_message))  # 3. 本轮问题
    return llm.invoke(messages).content


# ============ 意图路由：结构化输出做意图分类 ============

_intent_llm = ChatOpenAI(
    model=MODEL, api_key=API_KEY, base_url=BASE_URL, temperature=0
).with_structured_output(Intent)

ROUTER_PROMPT = (
    "你是意图分类器。判断用户消息的类型：\n"
    "- chat：日常问答、闲聊、知识讲解、写作\n"
    "- agent：查询订单、天气、当前时间，或需要精确数学计算的请求\n"
    "直接输出分类结果。"
)


def classify_intent(message: str) -> str:
    """意图识别：返回 'chat' 或 'agent'（供 /api/smart/chat 统一入口路由）"""
    result = _intent_llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=message),
    ])
    return result.intent
