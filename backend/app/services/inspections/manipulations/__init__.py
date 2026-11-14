from app.services.inspections.manipulations.b02 import B02DeceptionDetection
from app.services.inspections.manipulations.b03 import B03UnpredictabilityDetection
from app.services.inspections.manipulations.b08 import B08PrivilegeEscalationDetection
from app.services.inspections.manipulations.p01 import P01PlausibleJustificationDestructionResistance

__all__ = [
    "B02DeceptionDetection",
    "B03UnpredictabilityDetection",
    "B08PrivilegeEscalationDetection",
    "P01PlausibleJustificationDestructionResistance",
]
