"""
Project CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)):
    owner = db.query(models.User).filter(models.User.id == payload.owner_id).first()
    if not owner:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User {payload.owner_id} does not exist.",
        )
    project = models.Project(
        name=payload.name,
        description=payload.description,
        owner_id=payload.owner_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[schemas.ProjectResponse], status_code=status.HTTP_200_OK)
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).all()


@router.get("/{project_id}", response_model=schemas.ProjectResponse, status_code=status.HTTP_200_OK)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")
    return project


@router.put("/{project_id}", response_model=schemas.ProjectResponse, status_code=status.HTTP_200_OK)
def update_project(project_id: int, payload: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Project {project_id} not found.")
    db.delete(project)
    db.commit()
    return {"detail": f"Project {project_id} deleted."}
