"""
SQLAlchemy ORM models for TaskFlow.
Tables: users, projects, tasks
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)

    # One user owns many projects
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    # FK → users.id
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project id={self.id} name={self.name}>"


class Task(Base):
    __tablename__ = "tasks"

    __table_args__ = (
        CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_task_priority"),
        UniqueConstraint("title", "project_id", name="uq_task_title_project"),
    )

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    # Closed set: low / medium / high
    priority = Column(String, nullable=False, default="medium")
    # Stored as plain text (accepts raw phrases like "next friday")
    due_date = Column(String, nullable=True)
    # Task status: todo / in_progress / done
    status = Column(String, nullable=False, default="todo")
    # FK → projects.id
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="tasks")

    def __repr__(self):
        return f"<Task id={self.id} title={self.title} priority={self.priority}>"
