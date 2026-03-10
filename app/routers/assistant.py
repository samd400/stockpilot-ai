"""Conversational Business Assistant Router — natural language interface to platform."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User
from app.services.assistant_service import process_query, execute_action

router = APIRouter(prefix="/assistant", tags=["Assistant"])


class QueryRequest(BaseModel):
    query: str


class ExecuteRequest(BaseModel):
    action: str
    params: Dict[str, Any]


@router.post("/query")
async def assistant_query(
    data: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send a natural language query to the AI assistant. Returns proposed action (not executed)."""
    result = await process_query(db, str(current_user.tenant_id), data.query)
    return result


@router.post("/execute")
async def assistant_execute(
    data: ExecuteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute a validated action from the assistant."""
    result = await execute_action(
        db=db,
        tenant_id=str(current_user.tenant_id),
        user_id=str(current_user.id),
        action=data.action,
        params=data.params,
    )
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Action failed"))
    return result
