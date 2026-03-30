from contextlib import asynccontextmanager

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from db.base import Base
from db.session import engine
import models  # noqa: F401 — register ORM mappers
from routers.admin import router as admin_router
from routers.applications import router as applications_router
from routers.ats import router as ats_router
from routers.auth import router as auth_router
from routers.campus import router as campus_router
from routers.candidate import router as candidate_router
from routers.companies import router as companies_router
from routers.jobs import router as jobs_router
from routers.recruiter import router as recruiter_router
from routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="SmartHire ATS API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        o.strip()
        for o in os.getenv(
            "CORS_ALLOW_ORIGINS",
            "http://127.0.0.1:5000,http://localhost:5000",
        ).split(",")
        if o.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(companies_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(ats_router)
app.include_router(recruiter_router)
app.include_router(candidate_router)
app.include_router(admin_router)
app.include_router(campus_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
