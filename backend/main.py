from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.cats import router as cats_router
from app.api.dashboard import router as dashboard_router
from app.api.recognition import router as recognition_router
from app.api.chat import router as chat_router
from app.config.settings import settings
from app.database.migrations import ensure_runtime_columns
from app.database.seed import seed_roles_and_admin
from app.database.session import Base, SessionLocal, engine


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)


def init_auth_database() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_runtime_columns(engine)
    db = SessionLocal()
    try:
        seed_roles_and_admin(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_auth_database()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CatTrace Agent auth and YOLO recognition API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(auth_router)
app.include_router(cats_router)
app.include_router(dashboard_router)
app.include_router(recognition_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "CatTrace Agent backend is running",
        "docs": "/docs",
        "auth": "/api/auth",
        "cats": "/api/cats",
        "dashboard": "/api/dashboard/overview",
        "recognition": "/api/recognition/analyze",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "service": "cattrace-agent-backend",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)
