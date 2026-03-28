"""FastAPI dependency injectors."""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.auth import decode_token
from api.models import User, CalcSession
from api.calculator import CalculatorService

_bearer = HTTPBearer()


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(cred.credentials)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))  # noqa: E712
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


async def get_session_and_calc(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> tuple[CalcSession, CalculatorService]:
    """Load a CalcSession belonging to the current user, hydrate a CalculatorService."""
    result = await db.execute(
        select(CalcSession).where(CalcSession.id == session_id, CalcSession.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    calc = CalculatorService.from_db(
        session.stack_json, session.variables_json, session.settings_json, session.undo_json
    )
    return session, calc


async def persist_calc(session: CalcSession, calc: CalculatorService, db: AsyncSession):
    """Write calculator state back to the DB row."""
    cols = calc.to_db_columns()
    session.stack_json = cols["stack_json"]
    session.variables_json = cols["variables_json"]
    session.settings_json = cols["settings_json"]
    session.undo_json = cols["undo_json"]
    await db.commit()
    await db.refresh(session)
