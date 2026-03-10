"""Agent Audit Log — tracks all agent decisions and actions."""

import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class AgentAuditLog(Base):
    __tablename__ = "agent_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)

    agent_name = Column(String, nullable=False)
    action = Column(String, nullable=False)
    input_data = Column(Text, nullable=True)   # JSON
    output_data = Column(Text, nullable=True)  # JSON
    status = Column(String, default="success")  # success, failed, dry_run

    created_at = Column(DateTime, default=func.now(), index=True)
