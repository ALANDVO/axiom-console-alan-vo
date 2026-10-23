from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class Role(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class User(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    roles: List[str] = Field(default_factory=list)


class Tool(BaseModel):
    tool_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=100)
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")
    tool_behavior: Optional[str] = Field(None, pattern="^(read|write|destructive|execute)$")


class Permission(BaseModel):
    role: str = Field(..., min_length=1, max_length=100)
    tools: List[str] = Field(default_factory=list)


class PolicyRule(BaseModel):
    id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class Policies(BaseModel):
    enforcement_point: Optional[str] = Field(None, pattern="^(before_llm|after_llm|both)$")
    rules: List[PolicyRule] = Field(default_factory=list)


class GovernanceTool(BaseModel):
    tool_id: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    risk_level: Optional[str] = Field(None, pattern="^(low|medium|high|critical)$")


class AuthorizationPolicy(BaseModel):
    role: str = Field(..., min_length=1, max_length=100)
    tools: List[str] = Field(default_factory=list)


class OverridePolicy(BaseModel):
    deny_message: Optional[str] = None
    authorized_roles: List[str] = Field(default_factory=list)


class GovernanceArchitecture(BaseModel):
    layers: List[str] = Field(default_factory=list)
    deterministic_control: Optional[bool] = None
    components: List[str] = Field(default_factory=list)


class GovernancePolicies(BaseModel):
    authorization: List[AuthorizationPolicy] = Field(default_factory=list)
    override: Optional[OverridePolicy] = None
    governance_architecture: Optional[GovernanceArchitecture] = None


class Governance(BaseModel):
    version: str = Field(..., min_length=1, max_length=50)
    tools: List[GovernanceTool] = Field(default_factory=list)
    policies: Optional[GovernancePolicies] = None


class FixtureContent(BaseModel):
    """Validated structure for fixture content."""
    metadata: Optional[Dict[str, Any]] = None
    roles: List[Role] = Field(default_factory=list)
    users: List[User] = Field(default_factory=list)
    tools: List[Tool] = Field(default_factory=list)
    permissions: List[Permission] = Field(default_factory=list)
    policies: Optional[Policies] = None
    high_risk_actions: List[str] = Field(default_factory=list)
    escalation_triggers: List[str] = Field(default_factory=list)
    expected_escalation_channels: List[str] = Field(default_factory=list)
    governance: Optional[Governance] = None

    @classmethod
    def validate_content(cls, content: Dict[str, Any]) -> "FixtureContent":
        """Validate and parse fixture content."""
        return cls.model_validate(content)


class FixtureBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    domain: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    content: Dict[str, Any]
    governance: Optional[Dict[str, Any]] = None

    @classmethod
    def create_validated(cls, **data) -> "FixtureBase":
        """Create fixture with validated content."""
        if "content" in data and data["content"] is not None:
            FixtureContent.validate_content(data["content"])
        if "governance" in data and data["governance"] is not None:
            Governance.model_validate(data["governance"])
        return cls(**data)


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