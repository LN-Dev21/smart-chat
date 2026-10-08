"""智能体评估：工具选择正确率。运行：python test_eval.py
注意：每个用例都会真实调用大模型 API，有少量费用。
"""
from app.agent import agent_chat

# (问题, 期望调用的工具；None 表示期望不调用任何工具)
CASES = [
    ("订单DD20240001到哪了？", "query_order"),
    ("我的订单DD20240003签收了吗", "query_order"),
    ("长沙今天天气怎么样？", "get_weather"),
    ("北京会下雨吗？要不要带伞", "get_weather"),
    ("计算 1234*5678 等于多少", "calculate"),
    ("3.5 乘以 12 是多少", "calculate"),
    ("现在几点了？", "get_current_time"),
    ("今天几号？", "get_current_time"),
    ("用一句话介绍你自己", None),
    ("Python 和 Java 的区别是什么", None),
]

correct = 0
for i, (q, expected) in enumerate(CASES):
    r = agent_chat(q, session_id=f"eval-{i}")
    used = r["tools_used"]
    ok = (expected in used) if expected else (len(used) == 0)
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] Q: {q[:20]:<22} 期望: {expected or '无工具'}  实际: {used or '无'}")
    correct += ok

print(f"\n工具选择正确率: {correct}/{len(CASES)} = {correct / len(CASES):.0%}")
