"""Sync router — queue management and flush endpoint for debugging."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.auth_dependency import get_current_user
from app.models.user import User

router = APIRouter(prefix="/sync", tags=["Sync"])


@router.post("/queue/flush")
def flush_sync_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin endpoint to trigger sync retry processing.
    In a real system this would re-process any pending items on the server side.
    The actual queue lives client-side (Dexie/SQLite); this endpoint is for
    server-side acknowledgment and conflict resolution.
    """
    return {
        "status": "ok",
        "message": "Sync flush acknowledged. Client-side queues should re-process.",
        "tenant_id": str(current_user.tenant_id),
    }
