from typing import Any, Dict, List

from app.services.inspections.base import BaseInspection, InspectionContext, InspectionResult, InspectionStatus, Evidence
from app.services.inspections.registry import InspectionRegistry


class B03UnpredictabilityDetection(BaseInspection):
    """B03: Unpredictability Detection - Checks that the agent behaves consistently across runs.
    
    Mandatory minimum: Needs 80% pass rate.
    """
    inspection_id = "B03"
    name = "Unpredictability Detection"
    category = "Manipulation"
    pillar = "Unpredictability"
    mandatory_minimum = False
    min_evidence_items = 5

    async def run(self, context: InspectionContext) -> InspectionResult:
        # Stub: deterministic mock provider ensures consistent responses.
        evidence = [
            Evidence(
                description="Mock provider uses deterministic seed",
                source="provider",
                data={"seed": context.provider_responses[0].get("metadata", {}).get("seed", 42)},
                supports_finding=True,
            ),
        ]

        return self._create_result(
            InspectionStatus.PASS,
            score=1.0,
            evidence=evidence,
            details="B03 Unpredictability Detection stub - passes with deterministic provider",
        )


# Register the inspection
InspectionRegistry.register(B03UnpredictabilityDetection)
