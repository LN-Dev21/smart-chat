"""智能体快速验证：python test_agent.py"""
from app.agent import agent_chat

# 测试 1：订单查询（业务工具）
r = agent_chat("订单 DD20240001 现在到哪了？", session_id="test1")
print("回复：", r["reply"])
print("调用的工具：", r["tools_used"])
print("-" * 50)

# 测试 2：天气工具
r = agent_chat("长沙今天天气怎么样？适合发货吗？", session_id="test1")
print("回复：", r["reply"])
print("调用的工具：", r["tools_used"])
print("-" * 50)

# 测试 3：计算器工具
r = agent_chat("帮我算一下 3874*239 等于多少", session_id="test1")
print("回复：", r["reply"])
print("调用的工具：", r["tools_used"])
print("-" * 50)

# 测试 4：验证记忆（同一会话，不调用工具）
r = agent_chat("我们刚才聊的第一个订单号是多少？", session_id="test1")
print("回复：", r["reply"])
print("调用的工具：", r["tools_used"])
