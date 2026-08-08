"""
User CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Email '{payload.email}' is already registered.",
        )
    user = models.User(name=payload.name, email=payload.email)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("", response_model=List[schemas.UserResponse], status_code=status.HTTP_200_OK)
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()


@router.get("/{user_id}", response_model=schemas.UserResponse, status_code=status.HTTP_200_OK)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found.")
    return user


@router.put("/{user_id}", response_model=schemas.UserResponse, status_code=status.HTTP_200_OK)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found.")
    db.delete(user)
    db.commit()
    return {"detail": f"User {user_id} deleted."}
