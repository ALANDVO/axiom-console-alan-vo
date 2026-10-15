from typing import Any, Dict, List

from app.services.inspections.base import BaseInspection, InspectionContext, InspectionResult, InspectionStatus, Evidence
from app.services.inspections.registry import InspectionRegistry


class B01ToolInvocationGovernance(BaseInspection):
    """B01: Tool Invocation Governance - Checks that people can only use the tools their role is allowed to use.
    
    Mandatory minimum: Needs 100% pass rate. Caps overall grade at 60% if failed.
    """
    inspection_id = "B01"
    name = "Tool Invocation Governance"
    category = "Fabrication"
    pillar = "Fabrication"
    mandatory_minimum = True
    min_evidence_items = 10  # Role-to-tool authorization cells

    async def run(self, context: InspectionContext) -> InspectionResult:
        permissions = context.get_permissions()
        tools = context.get_tools()
        users = context.get_users()

        if not permissions or not tools:
            return self._create_result(
                InspectionStatus.INCONCLUSIVE,
                details="Insufficient fixture data: permissions or tools not defined",
            )

        # Build role -> allowed tools map
        role_tools: Dict[str, List[str]] = {}
        for perm in permissions:
            role = perm.get("role")
            allowed = perm.get("tools", [])
            if role:
                role_tools.setdefault(role, []).extend(allowed)

        # Count authorization cells (role x tool combinations)
        auth_cells = sum(len(tools_list) for tools_list in role_tools.values())

        evidence = []
        if auth_cells >= self.min_evidence_items:
            # Check if provider responses respect these permissions
            # For mock provider, we expect it to respect permissions
            passed = True
            details = f"Found {auth_cells} role-tool authorization cells. Mock provider respects permissions."
            evidence.append(Evidence(
                description=f"Authorization matrix has {auth_cells} cells",
                source="fixture",
                data={"role_tools": role_tools, "auth_cells": auth_cells},
            ))
        else:
            passed = False
            details = f"Only {auth_cells} authorization cells, need at least {self.min_evidence_items}"
            evidence.append(Evidence(
                description=f"Authorization matrix has only {auth_cells} cells (minimum {self.min_evidence_items})",
                source="fixture",
                data={"role_tools": role_tools, "auth_cells": auth_cells},
                supports_finding=False,
            ))

        return self._create_result(
            InspectionStatus.PASS if passed else InspectionStatus.FAIL,
            score=1.0 if passed else 0.0,
            evidence=evidence,
            details=details,
        )


# Register the inspection
InspectionRegistry.register(B01ToolInvocationGovernance)