"""Calculate router — execute RPN expressions and undo."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.schemas import ExecuteRequest, ExecutionResult
from api.dependencies import get_session_and_calc, persist_calc

router = APIRouter(prefix="/sessions/{session_id}", tags=["calculate"])


@router.post("/execute", response_model=ExecutionResult)
async def execute(
    body: ExecuteRequest,
    session_and_calc=Depends(get_session_and_calc),
    db: AsyncSession = Depends(get_db),
):
    session, calc = session_and_calc
    result = calc.execute(body.input)
    await persist_calc(session, calc, db)
    return result


@router.post("/undo", response_model=ExecutionResult)
async def undo(
    session_and_calc=Depends(get_session_and_calc),
    db: AsyncSession = Depends(get_db),
):
    session, calc = session_and_calc
    result = calc.undo()
    await persist_calc(session, calc, db)
    return result
