"""配置中心：从 .env 文件读取全部配置（企业规范：配置集中一处管理）"""
import os
from dotenv import load_dotenv

load_dotenv()   # 读取 backend/.env，把配置装进环境变量

API_KEY: str = os.getenv("LLM_API_KEY", "")
BASE_URL: str = os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
MODEL: str = os.getenv("LLM_MODEL", "glm-4.7")
DB_PATH: str = os.getenv("DB_PATH", "data/smartchat.db")
AGENT_DB_PATH: str = os.getenv("AGENT_DB_PATH", "data/agent_memory.db")
RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "20"))

# 系统提示词：给 AI 定人设（客服场景）
SYSTEM_PROMPT: str = (
    "你是「智聊助手」，一家电商公司的智能客服。"
    "回答使用简体中文，礼貌、简洁、条理清晰。"
    "不确定的内容明确告知用户，绝不编造。"
)

if not API_KEY or "在这里填" in API_KEY:
    raise RuntimeError("未找到 LLM_API_KEY，请检查 backend/.env 是否配置正确")
