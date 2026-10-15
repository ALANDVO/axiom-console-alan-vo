from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.models import AuditRun, AuditRunStatus, Fixture
from app.schemas import (
    AuditRunCreate,
    AuditRunUpdate,
    AuditRunResponse,
    AuditRunListResponse,
    ProviderConfig,
    JudgeConfig,
)
from app.services.audit_engine import AuditEngine

router = APIRouter(prefix="/audit/runs", tags=["audit-runs"])


@router.post("", response_model=AuditRunResponse, status_code=201)
async def create_audit_run(
    run_data: AuditRunCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new audit run."""
    # Validate fixture exists if provided
    if run_data.fixture_id:
        fixture = await db.get(Fixture, str(run_data.fixture_id))
        if not fixture:
            raise HTTPException(status_code=404, detail="Fixture not found")

    engine = AuditEngine(db)
    run = await engine.create_run(
        name=run_data.name,
        description=run_data.description,
        fixture_id=str(run_data.fixture_id) if run_data.fixture_id else None,
        provider_config=run_data.provider_config,
        judge_config=run_data.judge_config,
        suite=run_data.suite,
        eval_mode=run_data.eval_mode,
    )

    # Run audit in background
    background_tasks.add_task(engine.run_audit, run.id)

    return AuditRunResponse.model_validate(run)


@router.get("", response_model=AuditRunListResponse)
async def list_audit_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List audit runs with pagination."""
    engine = AuditEngine(db)
    runs, total = await engine.list_runs(page=page, page_size=page_size, status=status)

    return AuditRunListResponse(
        items=[AuditRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{run_id}", response_model=AuditRunResponse)
async def get_audit_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single audit run by ID."""
    engine = AuditEngine(db)
    run = await engine.get_run(str(run_id))
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")
    return AuditRunResponse.model_validate(run)


@router.patch("/{run_id}", response_model=AuditRunResponse)
async def update_audit_run(
    run_id: UUID,
    run_data: AuditRunUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an audit run (only name/description for pending runs)."""
    result = await db.execute(select(AuditRun).where(AuditRun.id == str(run_id)))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")

    if run.status != AuditRunStatus.PENDING:
        raise HTTPException(status_code=400, detail="Can only update pending runs")

    if run_data.name is not None:
        run.name = run_data.name
    if run_data.description is not None:
        run.description = run_data.description

    await db.commit()
    await db.refresh(run)
    return AuditRunResponse.model_validate(run)


@router.delete("/{run_id}", status_code=204)
async def delete_audit_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete an audit run."""
    result = await db.execute(select(AuditRun).where(AuditRun.id == str(run_id)))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")

    await db.delete(run)
    await db.commit()


@router.post("/{run_id}/cancel", response_model=AuditRunResponse)
async def cancel_audit_run(run_id: UUID, db: AsyncSession = Depends(get_db)):
    """Cancel a running audit run."""
    result = await db.execute(select(AuditRun).where(AuditRun.id == str(run_id)))
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Audit run not found")

    if run.status not in (AuditRunStatus.PENDING, AuditRunStatus.RUNNING):
        raise HTTPException(status_code=400, detail="Can only cancel pending or running runs")

    run.status = AuditRunStatus.CANCELLED
    await db.commit()
    await db.refresh(run)
    return AuditRunResponse.model_validate(run)