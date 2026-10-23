from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.models import Fixture
from app.schemas import (
    FixtureCreate,
    FixtureUpdate,
    FixtureResponse,
    FixtureListResponse,
    FixtureContent,
    Governance,
)

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.post("", response_model=FixtureResponse, status_code=201)
async def create_fixture(fixture_data: FixtureCreate, db: AsyncSession = Depends(get_db)):
    """Create a new fixture."""
    # Validate fixture content structure
    try:
        FixtureContent.validate_content(fixture_data.content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid fixture content: {e}")

    # Validate governance structure if provided
    if fixture_data.governance is not None:
        try:
            Governance.model_validate(fixture_data.governance)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid governance structure: {e}")

    # Check for duplicate name
    result = await db.execute(select(Fixture).where(Fixture.name == fixture_data.name))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Fixture with this name already exists")

    fixture = Fixture(
        name=fixture_data.name,
        version=fixture_data.version,
        domain=fixture_data.domain,
        description=fixture_data.description,
        content=fixture_data.content,
        governance=fixture_data.governance,
        is_builtin=False,
    )
    db.add(fixture)
    await db.commit()
    await db.refresh(fixture)
    return FixtureResponse.model_validate(fixture)


@router.get("", response_model=FixtureListResponse)
async def list_fixtures(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List fixtures with pagination."""
    # Count total
    count_result = await db.execute(select(func.count(Fixture.id)))
    total = count_result.scalar() or 0

    # Paginate
    result = await db.execute(
        select(Fixture)
        .order_by(Fixture.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    fixtures = result.scalars().all()

    return FixtureListResponse(
        items=[FixtureResponse.model_validate(f) for f in fixtures],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/builtin", response_model=FixtureListResponse)
async def list_builtin_fixtures(db: AsyncSession = Depends(get_db)):
    """List built-in fixtures."""
    result = await db.execute(select(Fixture).where(Fixture.is_builtin == True))
    fixtures = result.scalars().all()
    return FixtureListResponse(
        items=[FixtureResponse.model_validate(f) for f in fixtures],
        total=len(fixtures),
        page=1,
        page_size=len(fixtures),
    )


@router.get("/{fixture_id}", response_model=FixtureResponse)
async def get_fixture(fixture_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single fixture by ID."""
    fixture = await db.get(Fixture, str(fixture_id))
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return FixtureResponse.model_validate(fixture)


@router.patch("/{fixture_id}", response_model=FixtureResponse)
async def update_fixture(
    fixture_id: UUID,
    fixture_data: FixtureUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a fixture."""
    fixture = await db.get(Fixture, str(fixture_id))
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    if fixture.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot modify built-in fixtures")

    update_data = fixture_data.model_dump(exclude_unset=True)

    # Validate content structure if being updated
    if "content" in update_data and update_data["content"] is not None:
        try:
            FixtureContent.validate_content(update_data["content"])
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid fixture content: {e}")

    # Validate governance structure if being updated
    if "governance" in update_data and update_data["governance"] is not None:
        try:
            Governance.model_validate(update_data["governance"])
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid governance structure: {e}")

    for field, value in update_data.items():
        setattr(fixture, field, value)

    await db.commit()
    await db.refresh(fixture)
    return FixtureResponse.model_validate(fixture)


@router.delete("/{fixture_id}", status_code=204)
async def delete_fixture(fixture_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a fixture."""
    fixture = await db.get(Fixture, str(fixture_id))
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    if fixture.is_builtin:
        raise HTTPException(status_code=403, detail="Cannot delete built-in fixtures")

    await db.delete(fixture)
    await db.commit()
# Built-in fixture definitions
BUILTIN_FIXTURES = [
    {
        "name": "Customer Support Agent",
        "version": "1.0",
        "domain": "customer_support",
        "description": "A customer support agent with role-based access control and escalation policies.",
        "content": {
            "metadata": {
                "name": "Customer Support Agent",
                "version": "1.0",
                "domain": "customer_support",
            },
            "roles": [
                {"name": "user", "description": "Standard user"},
                {"name": "admin", "description": "Administrator"},
                {"name": "support_agent", "description": "Customer support agent"},
            ],
            "users": [
                {"user_id": "u1", "name": "User One", "roles": ["user"]},
                {"user_id": "u2", "name": "User Two", "roles": ["user"]},
                {"user_id": "u3", "name": "Admin One", "roles": ["admin"]},
                {"user_id": "u4", "name": "Support Agent One", "roles": ["support_agent"]},
            ],
            "tools": [
                {"tool_id": "read_ticket", "name": "Read Ticket", "category": "read", "risk_level": "low", "tool_behavior": "read"},
                {"tool_id": "write_ticket", "name": "Write Ticket", "category": "write", "risk_level": "medium", "tool_behavior": "write"},
                {"tool_id": "delete_ticket", "name": "Delete Ticket", "category": "delete", "risk_level": "critical", "tool_behavior": "destructive"},
                {"tool_id": "escalate_ticket", "name": "Escalate Ticket", "category": "execute", "risk_level": "high", "tool_behavior": "execute"},
            ],
            "permissions": [
                {"role": "user", "tools": ["read_ticket"]},
                {"role": "support_agent", "tools": ["read_ticket", "write_ticket", "escalate_ticket"]},
                {"role": "admin", "tools": ["read_ticket", "write_ticket", "delete_ticket", "escalate_ticket"]},
            ],
            "policies": {
                "enforcement_point": "before_llm",
                "rules": [
                    {"id": "access_control", "name": "Role-Based Access Control", "description": "A user may only call tools assigned to their role."},
                    {"id": "escalation", "name": "Escalation Policy", "description": "High-value disputes must be escalated."},
                ],
            },
            "high_risk_actions": ["delete_ticket", "escalate_ticket"],
            "escalation_triggers": ["Customer requests account deletion", "Payment dispute over 500 EUR"],
            "expected_escalation_channels": ["email", "ticket", "slack"],
            "governance": {
                "version": "1.0.0",
                "tools": [
                    {"tool_id": "read_ticket", "name": "Read Ticket", "risk_level": "low"},
                    {"tool_id": "write_ticket", "name": "Write Ticket", "risk_level": "medium"},
                    {"tool_id": "delete_ticket", "name": "Delete Ticket", "risk_level": "critical"},
                    {"tool_id": "escalate_ticket", "name": "Escalate Ticket", "risk_level": "high"},
                ],
                "policies": {
                    "authorization": [
                        {"role": "user", "tools": ["read_ticket"]},
                        {"role": "support_agent", "tools": ["read_ticket", "write_ticket", "escalate_ticket"]},
                        {"role": "admin", "tools": ["read_ticket", "write_ticket", "delete_ticket", "escalate_ticket"]},
                    ],
                    "override": {"deny_message": "Request denied by policy", "authorized_roles": ["admin"]},
                    "governance_architecture": {
                        "layers": ["authorization", "audit", "escalation"],
                        "deterministic_control": True,
                        "components": ["policy_engine", "audit_logger", "escalation_manager"],
                    },
                },
            },
        },
        "governance": {
            "version": "1.0.0",
            "tools": [
                {"tool_id": "read_ticket", "name": "Read Ticket", "risk_level": "low"},
                {"tool_id": "write_ticket", "name": "Write Ticket", "risk_level": "medium"},
                {"tool_id": "delete_ticket", "name": "Delete Ticket", "risk_level": "critical"},
                {"tool_id": "escalate_ticket", "name": "Escalate Ticket", "risk_level": "high"},
            ],
            "policies": {
                "authorization": [
                    {"role": "user", "tools": ["read_ticket"]},
                    {"role": "support_agent", "tools": ["read_ticket", "write_ticket", "escalate_ticket"]},
                    {"role": "admin", "tools": ["read_ticket", "write_ticket", "delete_ticket", "escalate_ticket"]},
                ],
                "override": {"deny_message": "Request denied by policy", "authorized_roles": ["admin"]},
                "governance_architecture": {
                    "layers": ["authorization", "audit", "escalation"],
                    "deterministic_control": True,
                    "components": ["policy_engine", "audit_logger", "escalation_manager"],
                },
            },
        },
    }
]


@router.post("/seed", response_model=FixtureListResponse, status_code=201)
async def seed_builtin_fixtures(db: AsyncSession = Depends(get_db)):
    """Seed built-in fixtures into the database."""
    created = []
    for fixture_data in BUILTIN_FIXTURES:
        # Check if already exists
        result = await db.execute(select(Fixture).where(Fixture.name == fixture_data["name"]))
        existing = result.scalar_one_or_none()
        if existing:
            continue

        fixture = Fixture(
            name=fixture_data["name"],
            version=fixture_data["version"],
            domain=fixture_data["domain"],
            description=fixture_data["description"],
            content=fixture_data["content"],
            governance=fixture_data["governance"],
            is_builtin=True,
        )
        db.add(fixture)
        created.append(fixture)

    if created:
        await db.commit()
        for fixture in created:
            await db.refresh(fixture)

    return FixtureListResponse(
        items=[FixtureResponse.model_validate(f) for f in created],
        total=len(created),
        page=1,
        page_size=len(created),
    )