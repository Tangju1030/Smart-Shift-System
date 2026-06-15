"""数据库连接与Session管理"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 数据库文件固定存放在 backend/ 目录下，不随启动目录变化
_DB_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_DB = f"sqlite:///{_DB_DIR}/scheduler.db"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI依赖注入：获取数据库Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
