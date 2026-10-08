"""数据库连接：SQLAlchemy 引擎 + 会话工厂 + 建表入口"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DB_PATH

# 确保 data 目录存在（SQLite 的库文件放在这里）
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# echo=False 不打印 SQL 日志；check_same_thread=False 允许多线程访问（Web 服务必需）
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})

# SessionLocal：数据库会话工厂，用完必须 close（相当于一次数据库连接）
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Base：所有 ORM 模型的父类
Base = declarative_base()


def init_db() -> None:
    """根据 models.py 里定义的表结构，在数据库中建表（已有表则跳过）"""
    from app import models   # 延迟导入：确保模型定义先被加载
    Base.metadata.create_all(bind=engine)
