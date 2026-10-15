from typing import Any, Dict, List, Optional, Type

from app.services.inspections.base import BaseInspection, InspectionContext, InspectionResult, InspectionStatus, Evidence


class InspectionRegistry:
    """Registry for inspection classes."""

    _inspections: Dict[str, Type[BaseInspection]] = {}

    @classmethod
    def register(cls, inspection_class: Type[BaseInspection]) -> None:
        """Register an inspection class."""
        if not inspection_class.inspection_id:
            raise ValueError(f"Inspection class {inspection_class.__name__} must define inspection_id")
        cls._inspections[inspection_class.inspection_id] = inspection_class

    @classmethod
    def get_inspection(cls, inspection_id: str) -> Optional[Type[BaseInspection]]:
        """Get an inspection class by ID."""
        return cls._inspections.get(inspection_id)

    @classmethod
    def list_inspections(cls) -> List[Dict[str, Any]]:
        """List all registered inspections."""
        return [
            {
                "id": insp.inspection_id,
                "name": insp.name,
                "category": insp.category,
                "pillar": insp.pillar,
                "mandatory_minimum": insp.mandatory_minimum,
            }
            for insp in cls._inspections.values()
        ]

    @classmethod
    def get_by_pillar(cls, pillar: str) -> List[Type[BaseInspection]]:
        """Get all inspections for a given pillar."""
        return [insp for insp in cls._inspections.values() if insp.pillar == pillar]

    @classmethod
    def get_mandatory_minimums(cls) -> List[Type[BaseInspection]]:
        """Get all mandatory minimum inspections."""
        return [insp for insp in cls._inspections.values() if insp.mandatory_minimum]

    @classmethod
    async def run_inspection(
        cls,
        inspection_id: str,
        context: InspectionContext,
    ) -> InspectionResult:
        """Run a single inspection by ID."""
        inspection_class = cls.get_inspection(inspection_id)
        if not inspection_class:
            return InspectionResult(
                inspection_id=inspection_id,
                name="Unknown",
                category="unknown",
                status=InspectionStatus.ERROR,
                error=f"Inspection not found: {inspection_id}",
            )

        inspection = inspection_class()
        try:
            return await inspection.run(context)
        except Exception as e:
            return InspectionResult(
                inspection_id=inspection_id,
                name=inspection_class.name,
                category=inspection_class.category,
                pillar=inspection_class.pillar,
                status=InspectionStatus.ERROR,
                error=str(e),
                mandatory_minimum=inspection_class.mandatory_minimum,
            )

    @classmethod
    async def run_suite(
        cls,
        inspection_ids: List[str],
        context: InspectionContext,
    ) -> List[InspectionResult]:
        """Run multiple inspections."""
        results = []
        for insp_id in inspection_ids:
            result = await cls.run_inspection(insp_id, context)
            results.append(result)
        return results


# Import inspections to register them
# These will be imported when the module is loaded
def register_core_inspections():
    """Register core inspections. Called during app startup."""
    from app.services.inspections import fabrications, manipulations  # noqa: F401

# Suite definitions
SUITES = {
    "smoke": ["B01", "B08", "P01"],
    "strategic": ["B01", "B02", "B08", "B09", "B12", "B16", "B18", "P01"],
    "essential": ["B01", "B02", "B03", "B04", "B06", "B08", "B09", "B12", "B16", "B18", "B20", "B27", "P01"],
    "core": [
        "B01", "B02", "B03", "B04", "B05", "B06",
        "B07", "B08", "B09", "B10", "B11", "B12", "B13", "B14",
        "B15", "B16", "B17", "B18", "B19", "B20", "B21", "B22", "B23",
        "B24", "B25", "B26", "B27", "B28", "B29", "B30", "B31", "B32",
    ],
    "extended": [
        "P01", "P08", "P13", "P19", "P22", "P27", "P32",
        "C02", "C05", "C11", "S02", "X04", "X11",
        "M02", "M03", "M06", "M07",
    ],
    "all": [
        "B01", "B02", "B03", "B04", "B05", "B06",
        "B07", "B08", "B09", "B10", "B11", "B12", "B13", "B14",
        "B15", "B16", "B17", "B18", "B19", "B20", "B21", "B22", "B23",
        "B24", "B25", "B26", "B27", "B28", "B29", "B30", "B31", "B32",
        "P01", "P08", "P13", "P19", "P22", "P27", "P32",
        "C02", "C05", "C11", "S02", "X04", "X11",
        "M02", "M03", "M06", "M07",
    ],
}


def get_suite_inspections(suite: str) -> List[str]:
    """Get inspection IDs for a suite."""
    return SUITES.get(suite, SUITES["essential"])