"""Stack router — direct push / get / clear."""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.schemas import PushRequest, ExecutionResult, StackItem
from api.dependencies import get_session_and_calc, persist_calc

router = APIRouter(prefix="/sessions/{session_id}/stack", tags=["stack"])


@router.get("", response_model=List[StackItem])
async def get_stack(
    session_and_calc=Depends(get_session_and_calc),
):
    _, calc = session_and_calc
    return calc.get_stack_items()


@router.post("/push", response_model=ExecutionResult)
async def push(
    body: PushRequest,
    session_and_calc=Depends(get_session_and_calc),
    db: AsyncSession = Depends(get_db),
):
    session, calc = session_and_calc
    result = calc.push(body.value, body.type)
    await persist_calc(session, calc, db)
    return result


@router.delete("", response_model=ExecutionResult)
async def clear_stack(
    session_and_calc=Depends(get_session_and_calc),
    db: AsyncSession = Depends(get_db),
):
    session, calc = session_and_calc
    result = calc.clear()
    await persist_calc(session, calc, db)
    return result
