"""
ResumeCraft FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import get_settings
from app.routers import auth, resume, task, jd, pay, mock

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时连接数据库，关闭时断开"""
    settings = get_settings()

    # 启动：连接 MongoDB（设置短超时，避免阻塞）
    app.state.mongo_client = AsyncIOMotorClient(
        settings.MONGODB_URL,
        serverSelectionTimeoutMS=5000,
    )
    app.state.db = app.state.mongo_client[settings.MONGODB_DB_NAME]

    # 创建索引（容错：MongoDB未启动时不阻塞应用）
    try:
        await _ensure_indexes(app.state.db)
        logger.info("MongoDB 连接成功，索引已就绪")
    except Exception as e:
        logger.warning(f"MongoDB 连接失败，部分功能不可用: {e}")

    yield

    # 关闭：断开 MongoDB
    app.state.mongo_client.close()


async def _ensure_indexes(db) -> None:
    """确保数据库索引存在"""
    # users
    await db.users.create_index("openid", unique=True)
    await db.users.create_index("unionid", sparse=True)

    # resumes
    await db.resumes.create_index([("user_id", 1), ("created_at", -1)])

    # tasks
    await db.tasks.create_index([("user_id", 1), ("created_at", -1)])
    await db.tasks.create_index("status")

    # orders
    await db.orders.create_index("order_no", unique=True)
    await db.orders.create_index([("user_id", 1), ("created_at", -1)])
    await db.orders.create_index("wechat_pay.transaction_id", sparse=True)

    # chat_messages
    await db.chat_messages.create_index([("task_id", 1), ("created_at", 1)])


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="基于事实的简历精修师 - 绝不捏造经历，只做精准翻译",
        version="1.0.0",
        lifespan=None if settings.MOCK_MODE else lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.API_PREFIX

    if settings.MOCK_MODE:
        # Mock 模式：不依赖数据库，使用模拟数据
        logger.info("========== MOCK 模式已启用 ==========")
        app.include_router(mock.router, prefix=prefix, tags=["Mock"])
        app.include_router(pay.router, prefix=f"{prefix}/pay", tags=["支付"])
    else:
        # 正式模式：注册所有真实路由
        app.include_router(auth.router, prefix=f"{prefix}/auth", tags=["认证"])
        app.include_router(resume.router, prefix=f"{prefix}/resume", tags=["简历"])
        app.include_router(task.router, prefix=f"{prefix}/task", tags=["任务"])
        app.include_router(jd.router, prefix=f"{prefix}/jd", tags=["JD解析"])
        app.include_router(pay.router, prefix=f"{prefix}/pay", tags=["支付"])

    return app


app = create_app()
