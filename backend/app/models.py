import datetime
import enum

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.database import Base


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
    variants = Column(JSON, nullable=False, default=list)
    normalized_keywords = Column(JSON, nullable=False, default=list)
    detected_niche = Column(String, nullable=True)
    image_refs = Column(JSON, nullable=False, default=list)
    source_url = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    runs = relationship("Run", back_populates="product")


class Run(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    status = Column(Enum(RunStatus), nullable=False, default=RunStatus.PENDING)
    started_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    product = relationship("Product", back_populates="runs")
    agent_outputs = relationship("AgentOutput", back_populates="run")
    reports = relationship("Report", back_populates="run")


class AgentOutput(Base):
    __tablename__ = "agent_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    output_json = Column(JSON, nullable=False, default=dict)
    confidence = Column(Enum(Confidence), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    run = relationship("Run", back_populates="agent_outputs")


class Report(Base):
    """REPORT IMMUTABILITY CONSTRAINT: This table is INSERT-ONLY.

    Never add update or delete methods for this model anywhere in the codebase.
    Reports serve as an immutable audit trail for backtesting and regulatory
    review. The service layer (db_service) intentionally exposes no update or
    delete path. Any direct ORM UPDATE/DELETE on this table violates the
    architecture's design and will be rejected in code review.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("runs.id"), nullable=False)
    verdict = Column(String, nullable=False)
    composite_score = Column(Float, nullable=False)
    memo_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)

    run = relationship("Run", back_populates="reports")
