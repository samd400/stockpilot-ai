"""
Agent management router — trigger, monitor, and audit AI agents.
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin_or_manager
from app.agents.base import get_agent, list_agents
from app.agents.tools import AgentTools
from app.models.agent_audit_log import AgentAuditLog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["AI Agents"])


def _run_agent_background(agent_name: str, tenant_id: str, user_id: str,
                           dry_run: bool, db: Session):
    """Run agent in background task."""
    try:
        agent = get_agent(agent_name)
        if not agent:
            return
        tools = AgentTools(db, tenant_id)
        result = agent.run(tenant_id, db, tools, dry_run=dry_run)
        logger.info(f"Agent {agent_name} completed: {result.status}, "
                    f"{result.actions_executed} actions in {result.execution_time_ms}ms")
    except Exception as e:
        logger.error(f"Background agent {agent_name} failed: {e}", exc_info=True)
    finally:
        db.close()


@router.get("/")
def list_all_agents(user: Dict = Depends(get_current_user)):
    """List all available agents."""
    return {"agents": list_agents()}


@router.post("/{agent_name}/trigger")
def trigger_agent(agent_name: str, background_tasks: BackgroundTasks,
                  payload: Optional[Dict[str, Any]] = None,
                  db: Session = Depends(get_db),
                  user: Dict = Depends(require_admin_or_manager)):
    """
    Trigger an agent run. Runs asynchronously in background.
    Body: {dry_run: bool (default: true)}
    """
    agent = get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404,
                            detail=f"Agent '{agent_name}' not found. "
                                   f"Available: {list(list_agents().keys())}")
    dry_run = (payload or {}).get("dry_run", True)

    # Get a new DB session for background task
    from app.core.database import SessionLocal
    bg_db = SessionLocal()

    background_tasks.add_task(
        _run_agent_background, agent_name, user["tenant_id"],
        user["user_id"], dry_run, bg_db
    )

    return {
        "agent": agent_name,
        "status": "triggered",
        "dry_run": dry_run,
        "message": f"Agent '{agent_name}' is running in background. "
                   f"Check /agents/{agent_name}/status for results.",
    }


@router.post("/{agent_name}/trigger-sync")
def trigger_agent_sync(agent_name: str, payload: Optional[Dict[str, Any]] = None,
                        db: Session = Depends(get_db),
                        user: Dict = Depends(require_admin_or_manager)):
    """Trigger agent synchronously (for testing). Use background trigger for production."""
    agent = get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    dry_run = (payload or {}).get("dry_run", True)
    tools = AgentTools(db, user["tenant_id"])
    result = agent.run(user["tenant_id"], db, tools, dry_run=dry_run)
    return {
        "agent": agent_name,
        "status": result.status,
        "dry_run": dry_run,
        "actions_executed": result.actions_executed,
        "execution_time_ms": result.execution_time_ms,
        "tokens_used": result.tokens_used,
        "steps": len(result.steps),
        "final_summary": result.final_summary,
        "errors": result.errors,
        "step_details": [{"iteration": s.iteration, "tool": s.tool_called,
                           "result": s.result[:200] if s.result else None}
                          for s in result.steps],
    }


@router.get("/{agent_name}/status")
def agent_status(agent_name: str, db: Session = Depends(get_db),
                 user: Dict = Depends(get_current_user)):
    """Get the last run status of an agent."""
    last = db.query(AgentAuditLog).filter(
        AgentAuditLog.tenant_id == user["tenant_id"],
        AgentAuditLog.agent_name == agent_name,
    ).order_by(AgentAuditLog.created_at.desc()).first()

    if not last:
        return {"agent": agent_name, "status": "never_run", "last_run": None}

    return {
        "agent": agent_name,
        "last_status": last.status,
        "last_run": last.created_at.isoformat(),
        "execution_time_ms": last.execution_time_ms,
        "tokens_used": last.llm_tokens_used,
        "summary": (last.output_data or {}).get("final_summary", ""),
        "actions_executed": (last.output_data or {}).get("actions_executed", 0),
    }


@router.get("/audit/logs")
def agent_audit_logs(skip: int = 0, limit: int = 50, agent_name: Optional[str] = None,
                     db: Session = Depends(get_db), user: Dict = Depends(get_current_user)):
    """Audit log of all agent runs."""
    q = db.query(AgentAuditLog).filter(AgentAuditLog.tenant_id == user["tenant_id"])
    if agent_name:
        q = q.filter(AgentAuditLog.agent_name == agent_name)
    logs = q.order_by(AgentAuditLog.created_at.desc()).offset(skip).limit(limit).all()
    return [{
        "id": str(l.id), "agent_name": l.agent_name, "action": l.action,
        "status": l.status, "execution_time_ms": l.execution_time_ms,
        "tokens_used": l.llm_tokens_used, "created_at": l.created_at.isoformat(),
        "summary": (l.output_data or {}).get("final_summary", ""),
    } for l in logs]
