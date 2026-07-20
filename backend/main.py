from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
import os
from app.config.settings import settings
from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.training import router as training_router
# from app.api.detection import router as detection_router  # 模块不存在
# from app.api.detection import encounter_router  # 模块不存在
from app.api.chat import router as chat_router
from app.api.dashboard import router as dashboard_router
from app.api.camera import router as camera_router
from app.api.knowledge import router as knowledge_router
from app.api.cats import router as cats_router
from app.core.logger import setup_logger, get_logger
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler,
)
from app.middleware.request_logger import RequestLoggerMiddleware


# 初始化日志系统
logger = setup_logger()


def init_minio():
    """初始化 MinIO 存储桶"""
    from app.storage.minio_client import MinIOClient
    try:
        minio_client = MinIOClient()
        logger.info(f"MinIO 存储桶 '{minio_client.bucket_name}' 初始化完成")
    except Exception as e:
        logger.error(f"MinIO 初始化失败: {e}")


def init_redis():
    """初始化 Redis 连接"""
    from app.storage.redis_client import redis_client
    if redis_client.is_connected():
        logger.info("Redis 连接成功")
    else:
        logger.warning("Redis 连接失败，缓存功能将不可用")


def init_seed():
    """初始化种子数据（角色、管理员）"""
    from app.database.session import SessionLocal, Base, engine
    from app.database.seed import seed_roles_and_admin

    # 创建所有数据库表（如果不存在）
    logger.info('正在创建数据库表...')
    Base.metadata.create_all(bind=engine)
    logger.info('数据库表创建完成')

    db = SessionLocal()
    try:
        seed_roles_and_admin(db)
    except Exception as e:
        logger.error(f"种子数据初始化失败: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在初始化服务...")
    init_minio()
    init_redis()
    init_seed()
    yield
    # 关闭时执行
    logger.info("服务已关闭")


# 创建 FastAPI 实例
app = FastAPI(
    title="VisAgent",
    version="0.1.0",
    description="基于 YOLOv11 的目标检测智能体平台 API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    swagger_ui_parameters={
        "persistAuthorization": True,  # 刷新页面后保留 Token
    },
)

# ── 注册 OpenAPI 认证方案（Swagger 显示 Authorize 按钮） ──
from fastapi.openapi.utils import get_openapi
from fastapi.security import HTTPBearer

security_scheme = HTTPBearer()

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="VisAgent",
        version="0.1.0",
        description="基于 YOLOv11 的目标检测智能体平台 API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "description": "输入 JWT Token（格式：<token>，不需要加 Bearer 前缀）",
        }
    }
    openapi_schema["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ── 注册异常处理器 ──────────────────────────────────
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# ── 注册中间件 ──────────────────────────────────────
# 请求日志中间件（注意：中间件按注册的逆序执行）
app.add_middleware(RequestLoggerMiddleware)

# CORS 中间件配置
# 允许前端跨域请求后端 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 挂载静态文件目录（裁剪图等） ──────────────────────
static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── 注册路由 ─────────────────────────────────────────
app.include_router(auth_router)
app.include_router(health_router)
app.include_router(training_router)
# app.include_router(detection_router)  # 模块不存在
app.include_router(chat_router)
app.include_router(dashboard_router)
app.include_router(camera_router)
app.include_router(knowledge_router)
app.include_router(cats_router)
# app.include_router(encounter_router)  # 模块不存在


@app.get("/")
def root():
    return {
        "message": "欢迎使用 VisAgent",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)
