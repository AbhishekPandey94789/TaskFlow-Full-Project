"""
Task CRUD endpoints + statistics + sort/search (Sections 1 & 2).
All algorithm calls happen here — never Python's built-in sorted() / list.sort().
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app import models, schemas
from app.algorithms import insertion_sort, binary_search, linear_search

router = APIRouter(prefix="/tasks", tags=["tasks"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _task_to_dict(task: models.Task) -> dict:
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "due_date": task.due_date,
        "status": task.status,
        "project_id": task.project_id,
    }


PRIORITY_RANK = {"low": 1, "medium": 2, "high": 3}


# ---------------------------------------------------------------------------
# Section 2 — sorted list endpoint
# GET /tasks?sort=priority  or  GET /tasks?sort=due_date
# ---------------------------------------------------------------------------

@router.get("/search", status_code=status.HTTP_200_OK)
def search_tasks(
    title: str = Query(..., description="Exact title to search for"),
    algo: str = Query("binary", description="'binary' or 'linear'"),
    project_id: Optional[int] = Query(None, description="Limit search to a project"),
    db: Session = Depends(get_db),
):
    """
    Section 2 — Search endpoint.
    Builds an in-memory index of {id, title} pairs from real DB rows,
    then uses binary_search (after insertion_sort) or linear_search.
    Returns the matched task (200) or 404.
    """
    query = db.query(models.Task)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    all_tasks = query.all()

    index = [{"id": t.id, "title": t.title} for t in all_tasks]

    algo = algo.lower()
    if algo == "binary":
        # binary_search requires the list sorted by the key first
        insertion_sort(index, "title")
        idx = binary_search(index, title, "title")
    else:
        idx = linear_search(index, title, "title")

    if idx is None or idx == -1:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No task with title '{title}' found.")

    task_id = index[idx]["id"]
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No task with title '{title}' found.")

    return schemas.TaskResponse.model_validate(task)


@router.get("", response_model=List[schemas.TaskResponse], status_code=status.HTTP_200_OK)
def list_tasks(
    sort: Optional[str] = Query(None, description="Sort field: 'priority' or 'due_date'"),
    project_id: Optional[int] = Query(None, description="Filter by project"),
    db: Session = Depends(get_db),
):
    """
    List all tasks, optionally filtered by project and sorted via insertion_sort.
    The sort is performed by our own insertion_sort — never ORDER BY or built-in sort.
    """
    query = db.query(models.Task)
    if project_id is not None:
        query = query.filter(models.Task.project_id == project_id)
    tasks = query.all()

    records = [_task_to_dict(t) for t in tasks]

    if sort == "priority":
        # Map priority strings to numeric rank for comparison
        for r in records:
            r["_priority_rank"] = PRIORITY_RANK.get(r["priority"], 2)
        insertion_sort(records, "_priority_rank")
        for r in records:
            r.pop("_priority_rank")
    elif sort == "due_date":
        insertion_sort(records, "due_date")

    return records


# ---------------------------------------------------------------------------
# Section 1 — Task CRUD
# ---------------------------------------------------------------------------

@router.post("", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Project {payload.project_id} does not exist.",
        )
    task = models.Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=schemas.TaskResponse, status_code=status.HTTP_200_OK)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found.")
    return task


@router.put("/{task_id}", response_model=schemas.TaskResponse, status_code=status.HTTP_200_OK)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found.")
    db.delete(task)
    db.commit()
    return {"detail": f"Task {task_id} deleted."}


# ---------------------------------------------------------------------------
# Section 1 — Statistics endpoint (SQL aggregation, no Python loops)
# GET /projects/{project_id}/stats  is also registered here for convenience
# but the primary stats route lives in projects router; this one returns
# per-project stats for ALL projects at once.
# ---------------------------------------------------------------------------

@router.get("/stats/all", status_code=status.HTTP_200_OK)
def all_project_stats(db: Session = Depends(get_db)):
    """
    Returns task count and count-by-status for every project.
    Aggregation is done in SQL (COUNT + GROUP BY), never in Python.
    """
    rows = (
        db.query(
            models.Project.id.label("project_id"),
            models.Project.name.label("project_name"),
            models.Task.status.label("status"),
            func.count(models.Task.id).label("cnt"),
        )
        .outerjoin(models.Task, models.Task.project_id == models.Project.id)
        .group_by(models.Project.id, models.Project.name, models.Task.status)
        .all()
    )

    # Collect into a dict keyed by project_id
    projects: dict = {}
    for row in rows:
        pid = row.project_id
        if pid not in projects:
            projects[pid] = {
                "project_id": pid,
                "project_name": row.project_name,
                "total_tasks": 0,
                "by_status": [],
            }
        if row.status is not None:
            projects[pid]["total_tasks"] += row.cnt
            projects[pid]["by_status"].append({"status": row.status, "count": row.cnt})

    return list(projects.values())
