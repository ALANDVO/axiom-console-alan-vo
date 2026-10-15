from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class FixtureBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    domain: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    content: Dict[str, Any]
    governance: Optional[Dict[str, Any]] = None


class FixtureCreate(FixtureBase):
    pass


class FixtureUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    version: Optional[str] = Field(None, min_length=1, max_length=50)
    domain: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    governance: Optional[Dict[str, Any]] = None


class FixtureResponse(FixtureBase):
    id: UUID
    is_builtin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FixtureListResponse(BaseModel):
    items: List[FixtureResponse]
    total: int
    page: int
    page_size: int


class ProviderConfig(BaseModel):
    type: str = Field(..., description="Provider type: mock, openai, anthropic, http")
    model: Optional[str] = None
    endpoint: Optional[str] = None
    api_key_env: Optional[str] = None
    extra_headers: Optional[Dict[str, str]] = None
    timeout_seconds: int = 30


class JudgeConfig(BaseModel):
    provider: str
    model: str
    api_key_env: Optional[str] = None
    weight: float = 1.0


class AuditRunBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    fixture_id: Optional[UUID] = None
    provider_config: ProviderConfig
    judge_config: Optional[List[JudgeConfig]] = None
    suite: str = "essential"
    eval_mode: str = "self"


class AuditRunCreate(AuditRunBase):
    pass


class AuditRunUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class InspectionResult(BaseModel):
    id: str
    name: str
    category: str
    pillar: Optional[str] = None
    status: str  # pass, fail, inconclusive, error
    score: Optional[float] = None
    evidence_count: int = 0
    details: Optional[str] = None
    error: Optional[str] = None
    mandatory_minimum: bool = False


class PillarScore(BaseModel):
    pillar: str
    score: float
    weight: float
    inspections: List[InspectionResult]


class AuditRunResponse(AuditRunBase):
    id: UUID
    status: str
    overall_score: Optional[float] = None
    grade: Optional[str] = None
    pillar_scores: Optional[List[PillarScore]] = None
    inspection_results: Optional[List[InspectionResult]] = None
    report_markdown: Optional[str] = None
    report_json: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditRunListResponse(BaseModel):
    items: List[AuditRunResponse]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str