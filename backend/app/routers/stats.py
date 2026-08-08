"""
Per-project statistics endpoint — SQL aggregation via COUNT + GROUP BY.
GET /projects/{project_id}/stats
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/projects", tags=["statistics"])


@router.get("/{project_id}/stats", response_model=schemas.ProjectStatsResponse, status_code=status.HTTP_200_OK)
def project_stats(project_id: int, db: Session = Depends(get_db)):
    """
    Returns total task count and a breakdown by status for one project.
    The COUNT + GROUP BY aggregation runs entirely in SQL — no Python-side counting.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")

    rows = (
        db.query(
            models.Task.status.label("status"),
            func.count(models.Task.id).label("cnt"),
        )
        .filter(models.Task.project_id == project_id)
        .group_by(models.Task.status)
        .all()
    )

    total = sum(r.cnt for r in rows)
    by_status = [schemas.StatusCount(status=r.status, count=r.cnt) for r in rows]

    return schemas.ProjectStatsResponse(
        project_id=project_id,
        project_name=project.name,
        total_tasks=total,
        by_status=by_status,
    )
