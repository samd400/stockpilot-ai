from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.services.assistant_service import chat

router = APIRouter(prefix="/assistant", tags=["AI Assistant"])


@router.post("/chat")
def chat_endpoint(payload: Dict[str, Any], db: Session = Depends(get_db),
                  user: Dict = Depends(get_current_user)):
    """
    Multi-turn AI business assistant.
    Body: {message: str, conversation_history: [{role, content}]}
    """
    message = payload.get("message", "").strip()
    if not message:
        return {"response": "Please provide a message.", "tokens_used": 0}
    history = payload.get("conversation_history", [])
    response = chat(db, user["tenant_id"], message, history)
    return {"response": response, "user_message": message}
