from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class InspectionStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    INCONCLUSIVE = "inconclusive"
    ERROR = "error"


@dataclass
class Evidence:
    """A piece of evidence collected during an inspection."""
    description: str
    source: str  # e.g., "fixture", "provider_response", "audit_trail"
    data: Dict[str, Any] = field(default_factory=dict)
    supports_finding: bool = True  # True if evidence supports the finding, False if it contradicts


@dataclass
class InspectionResult:
    """Result of a single inspection."""
    inspection_id: str
    name: str
    category: str
    pillar: Optional[str] = None
    status: InspectionStatus = InspectionStatus.INCONCLUSIVE
    score: Optional[float] = None  # 0.0 to 1.0
    evidence: List[Evidence] = field(default_factory=list)
    details: str = ""
    error: Optional[str] = None
    mandatory_minimum: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.inspection_id,
            "name": self.name,
            "category": self.category,
            "pillar": self.pillar,
            "status": self.status.value,
            "score": self.score,
            "evidence_count": len(self.evidence),
            "details": self.details,
            "error": self.error,
            "mandatory_minimum": self.mandatory_minimum,
        }


class InspectionContext:
    """Context passed to inspections during execution."""

    def __init__(
        self,
        fixture: Dict[str, Any],
        provider_responses: List[Dict[str, Any]],
        audit_trail: List[Dict[str, Any]],
        governance: Dict[str, Any],
    ):
        self.fixture = fixture
        self.provider_responses = provider_responses
        self.audit_trail = audit_trail
        self.governance = governance

    def get_users(self) -> List[Dict[str, Any]]:
        return self.fixture.get("users", [])

    def get_tools(self) -> List[Dict[str, Any]]:
        return self.fixture.get("tools", [])

    def get_permissions(self) -> List[Dict[str, Any]]:
        return self.fixture.get("permissions", [])

    def get_policies(self) -> Dict[str, Any]:
        return self.fixture.get("policies", {})

    def get_governance(self) -> Dict[str, Any]:
        return self.governance


class BaseInspection(ABC):
    """Abstract base class for all inspections."""

    # Class attributes that must be defined by subclasses
    inspection_id: str = ""
    name: str = ""
    category: str = ""
    pillar: Optional[str] = None
    mandatory_minimum: bool = False
    min_evidence_items: int = 10

    @abstractmethod
    async def run(self, context: InspectionContext) -> InspectionResult:
        """Run the inspection and return a result."""
        pass

    def _check_evidence_floor(self, evidence_count: int) -> bool:
        """Check if we have enough evidence items."""
        return evidence_count >= self.min_evidence_items

    def _create_result(
        self,
        status: InspectionStatus,
        score: Optional[float] = None,
        evidence: Optional[List[Evidence]] = None,
        details: str = "",
        error: Optional[str] = None,
    ) -> InspectionResult:
        return InspectionResult(
            inspection_id=self.inspection_id,
            name=self.name,
            category=self.category,
            pillar=self.pillar,
            status=status,
            score=score,
            evidence=evidence or [],
            details=details,
            error=error,
            mandatory_minimum=self.mandatory_minimum,
        )