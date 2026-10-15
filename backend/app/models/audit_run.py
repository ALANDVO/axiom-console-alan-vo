"""SQLAlchemy model for audit runs."""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, JSON, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow() -> datetime:
    """Return current UTC time with timezone info."""
    return datetime.now(timezone.utc)


def _uuid() -> str:
    """Generate a UUID string for use as a default value."""
    return str(uuid.uuid4())


class AuditRunStatus(str, enum.Enum):
    """Status of an audit run."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditRun(Base):
    """An audit run against an AI agent."""

    __tablename__ = "audit_runs"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    fixture_id = Column(String(36), ForeignKey("fixtures.id"), nullable=True)
    provider_config = Column(JSON, nullable=False)
    judge_config = Column(JSON, nullable=True)
    suite = Column(String(50), nullable=False, default="essential")
    eval_mode = Column(String(50), nullable=False, default="self")
    status = Column(Enum(AuditRunStatus), nullable=False, default=AuditRunStatus.PENDING)
    overall_score = Column(Float, nullable=True)
    grade = Column(String(1), nullable=True)
    pillar_scores = Column(JSON, nullable=True)
    inspection_results = Column(JSON, nullable=True)
    report_json = Column(JSON, nullable=True)
    report_markdown = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    fixture = relationship("Fixture", back_populates="audit_runs")