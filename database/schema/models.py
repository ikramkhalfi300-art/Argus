"""
Reference copy of the SQLAlchemy ORM models.

The canonical definitions live in backend/app/models.py.
This file is kept in sync for documentation and schema-review purposes.
"""

import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class Confidence(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    subcategory = Column(String, nullable=False)
    normalized_keywords = Column(JSON, nullable=False, default=list)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.PENDING)
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    output_json = Column(JSON, nullable=False, default=dict)
    confidence = Column(Enum(Confidence), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class Report(Base):
    """REPORT IMMUTABILITY CONSTRAINT: This table is INSERT-ONLY.

    Never add update or delete methods for this model anywhere in the codebase.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    verdict = Column(String, nullable=False)
    composite_score = Column(Float, nullable=False)
    memo_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
