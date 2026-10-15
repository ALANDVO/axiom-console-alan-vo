import pytest

from app.services.inspections.base import InspectionContext, InspectionStatus
from app.services.inspections.fabrications.b01 import B01ToolInvocationGovernance
from app.services.inspections.manipulations.b08 import B08PrivilegeEscalationDetection
from app.services.inspections.manipulations.p01 import P01PlausibleJustificationDestructionResistance
from app.services.inspections.registry import InspectionRegistry, get_suite_inspections


@pytest.fixture
def sample_context(sample_fixture):
    return InspectionContext(
        fixture=sample_fixture,
        provider_responses=[],
        audit_trail=[],
        governance=sample_fixture.get("governance", {}),
    )


@pytest.mark.asyncio
async def test_b01_tool_invocation_governance(sample_context):
    inspection = B01ToolInvocationGovernance()
    result = await inspection.run(sample_context)
    
    assert result.inspection_id == "B01"
    assert result.name == "Tool Invocation Governance"
    assert result.category == "Fabrication"
    assert result.pillar == "Fabrication"
    assert result.mandatory_minimum is True
    assert result.status in (InspectionStatus.PASS, InspectionStatus.FAIL, InspectionStatus.INCONCLUSIVE)
    assert len(result.evidence) > 0


@pytest.mark.asyncio
async def test_b08_privilege_escalation_detection(sample_context):
    inspection = B08PrivilegeEscalationDetection()
    result = await inspection.run(sample_context)
    
    assert result.inspection_id == "B08"
    assert result.name == "Privilege Escalation Detection"
    assert result.category == "Manipulation"
    assert result.pillar == "Manipulation"
    assert result.mandatory_minimum is True
    assert result.status in (InspectionStatus.PASS, InspectionStatus.FAIL, InspectionStatus.INCONCLUSIVE)


@pytest.mark.asyncio
async def test_p01_destruction_resistance(sample_context):
    inspection = P01PlausibleJustificationDestructionResistance()
    result = await inspection.run(sample_context)
    
    assert result.inspection_id == "P01"
    assert result.name == "Plausible-Justification Destruction Resistance"
    assert result.category == "Sabotage"
    assert result.mandatory_minimum is True
    assert result.status in (InspectionStatus.PASS, InspectionStatus.FAIL, InspectionStatus.INCONCLUSIVE)


@pytest.mark.asyncio
async def test_inspection_registry():
    # Check that inspections are registered
    inspections = InspectionRegistry.list_inspections()
    inspection_ids = [i["id"] for i in inspections]
    
    assert "B01" in inspection_ids
    assert "B08" in inspection_ids
    assert "P01" in inspection_ids
    
    # Check mandatory minimums
    mandatory = InspectionRegistry.get_mandatory_minimums()
    mandatory_ids = [m.inspection_id for m in mandatory]
    assert "B01" in mandatory_ids
    assert "B08" in mandatory_ids
    assert "P01" in mandatory_ids


@pytest.mark.asyncio
async def test_suite_definitions():
    smoke = get_suite_inspections("smoke")
    assert smoke == ["B01", "B08", "P01"]
    
    strategic = get_suite_inspections("strategic")
    assert "B01" in strategic
    assert "B08" in strategic
    assert "P01" in strategic
    
    essential = get_suite_inspections("essential")
    assert "B01" in essential
    assert "B08" in essential
    assert "P01" in essential
    assert "B02" in essential
    assert "B03" in essential


@pytest.mark.asyncio
async def test_run_suite(sample_context):
    results = await InspectionRegistry.run_suite(["B01", "B08", "P01"], sample_context)
    assert len(results) == 3
    for r in results:
        assert r.inspection_id in ["B01", "B08", "P01"]