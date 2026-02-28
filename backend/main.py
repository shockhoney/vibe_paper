"""FastAPI 主入口。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database.postgres import engine
from backend.database.models import Base
from backend.database.chroma_client import get_chroma_client, get_or_create_collection
from backend.api import papers, literature, agents, ws

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据库，关闭时释放连接。"""
    logger.info("Initializing database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables ready.")

    # 初始化 Chroma 集合
    try:
        chroma = get_chroma_client()
        get_or_create_collection(chroma)
        logger.info("Chroma collection ready.")
    except Exception as e:
        logger.warning("Chroma not available: %s", e)

    yield

    await engine.dispose()
    logger.info("Database connection closed.")


app = FastAPI(
    title="Vibe Paper - 多智能体论文写作助手",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 配置（允许 Streamlit 前端访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(papers.router, prefix="/api")
app.include_router(literature.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(ws.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
