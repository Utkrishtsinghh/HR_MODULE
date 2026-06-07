from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import logging

from app.api.routes import auth, health, jobs, resumes, users, video
from app.db.init_db import init_db

logger = logging.getLogger("ats")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.addHandler(console_handler)

try:
    import logging_loki
    logging_loki.emitter.LokiEmitter.level_tag = "level"
    handler = logging_loki.LokiHandler(
        url="http://localhost:3100/loki/api/v1/push",
        tags={"application": "ats-backend"},
        version="1",
    )
    logger.addHandler(handler)
    logger.info("Loki logging enabled")
except Exception as e:
    logger.warning(f"Loki logging not available (running locally?): {e}")

logger.info("ATS Backend Starting")

app = FastAPI(title="UTK AI HR")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(jobs.router)
app.include_router(resumes.router)
app.include_router(video.router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")


@app.on_event("startup")
def on_startup():
    init_db()
    logger.info("Database Initialized")


@app.on_event("shutdown")
def on_shutdown():
    logger.info("ATS Backend Shutdown")
