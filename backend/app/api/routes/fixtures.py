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
)

router = APIRouter(prefix="/fixtures", tags=["fixtures"])


@router.post("", response_model=FixtureResponse, status_code=201)
async def create_fixture(fixture_data: FixtureCreate, db: AsyncSession = Depends(get_db)):
    """Create a new fixture."""
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