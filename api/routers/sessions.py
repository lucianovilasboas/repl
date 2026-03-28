"""Sessions router — CRUD for calculator sessions."""

from __future__ import annotations

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import User, CalcSession
from api.schemas import (
    SessionCreate, SessionResponse, SessionDetailResponse,
    SettingsUpdate, SettingsResponse, ExecutionResult,
)
from api.dependencies import get_current_user, get_session_and_calc, persist_calc
from api.calculator import CalculatorService

router = APIRouter(prefix="/sessions", tags=["sessions"])


def _session_response(s: CalcSession) -> SessionResponse:
    stack_data = json.loads(s.stack_json)
    return SessionResponse(
        id=s.id, name=s.name, stack_depth=len(stack_data),
        created_at=s.created_at, updated_at=s.updated_at,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: SessionCreate = SessionCreate(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = CalcSession(user_id=user.id, name=body.name)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _session_response(session)


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalcSession).where(CalcSession.user_id == user.id).order_by(CalcSession.updated_at.desc())
    )
    return [_session_response(s) for s in result.scalars().all()]


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalcSession).where(CalcSession.id == session_id, CalcSession.user_id == user.id)
    )
    s = result.scalar_one_or_none()
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    calc = CalculatorService.from_db(s.stack_json, s.variables_json, s.settings_json, s.undo_json)
    return SessionDetailResponse(
        id=s.id, name=s.name,
        stack=calc.get_stack_items(),
        variables=calc.get_variables_map(),
        settings=SettingsResponse(**calc.settings),
        stack_depth=calc.stack.depth(),
        created_at=s.created_at, updated_at=s.updated_at,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalcSession).where(CalcSession.id == session_id, CalcSession.user_id == user.id)
    )
    s = result.scalar_one_or_none()
    if s is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await db.delete(s)
    await db.commit()


@router.post("/{session_id}/reset", response_model=ExecutionResult)
async def reset_session(
    session_and_calc=Depends(get_session_and_calc),
    db: AsyncSession = Depends(get_db),
):
    session, calc = session_and_calc
    result = calc.reset()
    await persist_calc(session, calc, db)
    return result


@router.patch("/{session_id}/settings", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate,
    session_and_calc=Depends(get_session_and_calc),
    db: AsyncSession = Depends(get_db),
):
    session, calc = session_and_calc
    calc.update_settings(**body.model_dump(exclude_unset=True))
    await persist_calc(session, calc, db)
    return SettingsResponse(**calc.settings)
