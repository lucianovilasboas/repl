"""FastAPI application factory."""

from __future__ import annotations

import sys
import os
from contextlib import asynccontextmanager

# Ensure the project root is on sys.path so core imports (stack, parser, …) work.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import Settings
from api.database import init_db
from api.routers import auth, sessions, calculate, stack, operations

_settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="HP 50g RPN Calculator API",
    description=(
        "REST API for the HP 50g RPN Calculator Simulator. "
        "Supports all 130+ operations: arithmetic, scientific, stack manipulation, "
        "lists, vectors, matrices, programs, variables, and more."
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "User registration, login and token management"},
        {"name": "sessions", "description": "Calculator session CRUD"},
        {"name": "calculate", "description": "Execute RPN expressions"},
        {"name": "stack", "description": "Direct stack manipulation"},
        {"name": "operations", "description": "Discover available operations (public, no auth)"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(calculate.router)
app.include_router(stack.router)
app.include_router(operations.router)


@app.get("/", tags=["root"])
async def root():
    return {"message": "HP 50g RPN Calculator API", "docs": "/docs"}
