"""SQLAlchemy model for fixtures."""
import uuid

from sqlalchemy import Boolean, Column, DateTime, JSON, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.audit_run import utcnow, _uuid


class Fixture(Base):
    """An agent behavior fixture used as audit input."""

    __tablename__ = "fixtures"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False, unique=True)
    version = Column(String(50), nullable=False)
    domain = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    content = Column(JSON, nullable=False)
    governance = Column(JSON, nullable=True)
    is_builtin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)

    audit_runs = relationship("AuditRun", back_populates="fixture")