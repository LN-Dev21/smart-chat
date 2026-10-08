"""智能体模块：LangChain 实现带工具调用与持久记忆的客服智能体"""
import sqlite3
from datetime import datetime

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver

from app.config import AGENT_DB_PATH, API_KEY, BASE_URL, MODEL


# ============ 四个业务工具 ============

@tool
def query_order(order_id: str) -> str:
    """根据订单号查询订单的物流状态。参数 order_id 是订单号，格式如 "DD20240001"。
    用户询问订单进度、物流、发货、签收情况时必须使用本工具。"""
    orders = {
        "DD20240001": "已发货，顺丰速运，预计明天 18:00 前送达，收件人张先生",
        "DD20240002": "待付款，订单金额 129.00 元，30 分钟内未支付将自动取消",
        "DD20240003": "已签收，签收时间 2026-09-18 14:32，感谢您的购买",
        "DD20240004": "打包中，预计今天 20:00 前发出",
    }
    return orders.get(order_id, f"未找到订单 {order_id}，请核对订单号（格式如 DD20240001）")


@tool
def get_weather(city: str) -> str:
    """查询指定中国城市今天的天气。参数 city 是城市名，如"长沙"。
    用户询问天气、是否适合发货/出行时使用本工具。"""
    fake_data = {
        "长沙": "晴，25℃，微风，适合户外活动",
        "北京": "多云，18℃，早晚温差大",
        "上海": "小雨，22℃，出门记得带伞",
        "广州": "晴间多云，28℃，湿度较高",
        "深圳": "阵雨，26℃，注意防雨",
        "郑州": "晴，22℃，空气干燥，适合发货",
        "太原": "晴，15℃，昼夜温差大",
    }
    return fake_data.get(city, f"{city}：晴，24℃（模拟数据）")


@tool
def calculate(expression: str) -> str:
    """计算数学表达式的精确结果。参数 expression 是算式，如 "3874*239"。
    遇到任何数学计算都必须使用本工具精确计算，禁止口算估算。"""
    try:
        allowed = set("0123456789+-*/.() ")
        if not set(expression) <= allowed:
            return "表达式含有非法字符"
        return f"{expression} = {eval(expression)}"
    except Exception as e:
        return f"计算失败：{e}"


@tool
def get_current_time() -> str:
    """获取当前日期和时间。用户问"现在几点""今天几号"等问题时使用。"""
    return datetime.now().strftime("现在是 %Y年%m月%d日 %H:%M:%S")


TOOLS = [query_order, get_weather, calculate, get_current_time]


# ============ 组装智能体 ============

# 智能体专用模型：温度 0（工具调用是精确动作，要稳定不要发散）
agent_llm = ChatOpenAI(
    model=MODEL, api_key=API_KEY, base_url=BASE_URL, temperature=0,
)

# 记忆持久化：SqliteSaver 把智能体每轮状态存入文件，重启不丢
_conn = sqlite3.connect(AGENT_DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(_conn)

# 组装智能体：ReAct 循环由 create_agent 内部自动完成
agent = create_agent(
    model=agent_llm,
    tools=TOOLS,
    system_prompt=(
        "你是「智聊助手」，一家电商公司的智能客服。"
        "用户的问题涉及订单查询、天气、数学计算、当前时间时，"
        "必须调用对应工具获取真实结果，禁止编造；"
        "其他问题用简体中文礼貌、简洁地回答。"
    ),
    checkpointer=checkpointer,
)


def agent_chat(message: str, session_id: str) -> dict:
    """
    智能体对话入口。
    :param session_id: 会话ID（即 thread_id，同一会话共享记忆）
    :return: {"reply": 最终回复, "tools_used": [本轮调用过的工具名]}
    """
    result = agent.invoke(
        {"messages": [{"role": "user", "content": message}]},
        config={"configurable": {"thread_id": session_id}},
    )

    reply = ""
    tools_used = []
    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content and not reply:
            reply = msg.content
    for msg in result["messages"]:
        if msg.type == "ai" and getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                tools_used.append(tc["name"])

    return {"reply": reply or "（智能体未返回内容）", "tools_used": tools_used}
