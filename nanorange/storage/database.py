"""
Database models for NanoRange persistence.

Uses SQLAlchemy with SQLite for storing:
- Sessions: User interaction sessions
- Pipelines: Pipeline definitions within sessions
- Steps: Individual steps and their status
- Results: Execution results and outputs
- SavedPipelines: Reusable pipeline templates
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from sqlalchemy import (
    create_engine,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
    Session as DBSession,
)
from nanorange.core.schemas import StepStatus


Base = declarative_base()

# Global engine and session factory
_engine = None
_SessionFactory = None


class SessionModel(Base):
    """User interaction session."""
    
    __tablename__ = "sessions"
    
    id = Column(String(36), primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="active")  # active, completed, abandoned
    
    # Relationships
    pipelines = relationship("PipelineModel", back_populates="session", cascade="all, delete-orphan")
    
    # Session metadata (renamed to avoid conflict with SQLAlchemy)
    session_metadata_json = Column(Text, default="{}")
    
    @property
    def session_metadata(self) -> Dict[str, Any]:
        return json.loads(self.session_metadata_json) if self.session_metadata_json else {}
    
    @session_metadata.setter
    def session_metadata(self, value: Dict[str, Any]):
        self.session_metadata_json = json.dumps(value)


class PipelineModel(Base):
    """Pipeline definition within a session."""
    
    __tablename__ = "pipelines"
    
    id = Column(String(36), primary_key=True)
    session_id = Column(String(36), ForeignKey("sessions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(String(20), default="draft")  # draft, validated, executed, failed
    
    # Full pipeline definition as JSON
    definition_json = Column(Text, nullable=False)
    
    # Relationships
    session = relationship("SessionModel", back_populates="pipelines")
    steps = relationship("StepModel", back_populates="pipeline", cascade="all, delete-orphan")
    
    @property
    def definition(self) -> Dict[str, Any]:
        return json.loads(self.definition_json) if self.definition_json else {}
    
    @definition.setter
    def definition(self, value: Dict[str, Any]):
        self.definition_json = json.dumps(value)


class StepModel(Base):
    """Individual pipeline step with execution status."""
    
    __tablename__ = "steps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_id = Column(String(36), ForeignKey("pipelines.id"), nullable=False)
    step_id = Column(String(36), nullable=False)
    step_name = Column(String(255), nullable=False)
    tool_id = Column(String(255), nullable=False)
    
    # Input configuration as JSON
    inputs_json = Column(Text, default="{}")
    
    # Execution status
    status = Column(
        Enum(StepStatus),
        default=StepStatus.PENDING
    )
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Relationships
    pipeline = relationship("PipelineModel", back_populates="steps")
    results = relationship("ResultModel", back_populates="step", cascade="all, delete-orphan")
    
    @property
    def inputs(self) -> Dict[str, Any]:
        return json.loads(self.inputs_json) if self.inputs_json else {}
    
    @inputs.setter
    def inputs(self, value: Dict[str, Any]):
        self.inputs_json = json.dumps(value)


class ResultModel(Base):
    """Execution result for a step output."""
    
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    step_id = Column(Integer, ForeignKey("steps.id"), nullable=False)
    output_name = Column(String(255), nullable=False)
    
    # Value storage (can be inline or file path)
    value_type = Column(String(50), nullable=False)  # string, number, path, json
    value_inline = Column(Text, nullable=True)  # For small values
    value_path = Column(String(512), nullable=True)  # For file references
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    step = relationship("StepModel", back_populates="results")
    
    def get_value(self) -> Any:
        """Get the actual value."""
        if self.value_type == "path":
            return self.value_path
        elif self.value_type == "json":
            return json.loads(self.value_inline) if self.value_inline else None
        elif self.value_type == "number":
            return float(self.value_inline) if self.value_inline else None
        else:
            return self.value_inline
    
    def set_value(self, value: Any, value_type: str = "string"):
        """Set the value with appropriate storage."""
        self.value_type = value_type
        
        if value_type == "path":
            self.value_path = str(value)
            self.value_inline = None
        elif value_type == "json":
            self.value_inline = json.dumps(value)
            self.value_path = None
        elif value_type == "number":
            self.value_inline = str(value)
            self.value_path = None
        else:
            self.value_inline = str(value) if value is not None else None
            self.value_path = None


class SavedPipelineModel(Base):
    """Saved pipeline template for reuse."""
    
    __tablename__ = "saved_pipelines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, default="")
    category = Column(String(100), default="general")
    
    # Full pipeline definition as JSON
    definition_json = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Usage tracking
    use_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Metadata
    tags_json = Column(Text, default="[]")
    
    @property
    def definition(self) -> Dict[str, Any]:
        return json.loads(self.definition_json) if self.definition_json else {}
    
    @definition.setter
    def definition(self, value: Dict[str, Any]):
        self.definition_json = json.dumps(value)
    
    @property
    def tags(self) -> list:
        return json.loads(self.tags_json) if self.tags_json else []
    
    @tags.setter
    def tags(self, value: list):
        self.tags_json = json.dumps(value)


def init_database(
    db_path: Optional[str] = None,
    echo: bool = False
) -> None:
    """
    Initialize the database.
    
    Args:
        db_path: Path to SQLite database file (defaults to ./data/nanorange.db)
        echo: Whether to echo SQL statements
    """
    global _engine, _SessionFactory
    
    if db_path is None:
        db_path = Path("./data/nanorange.db")
    else:
        db_path = Path(db_path)
    
    # Ensure directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create engine
    _engine = create_engine(
        f"sqlite:///{db_path}",
        echo=echo,
        connect_args={"check_same_thread": False}
    )
    
    # Create tables
    Base.metadata.create_all(_engine)
    
    # Create session factory
    _SessionFactory = sessionmaker(bind=_engine)


def get_engine():
    """Get the database engine."""
    global _engine
    if _engine is None:
        init_database()
    return _engine


def get_session() -> DBSession:
    """Get a new database session."""
    global _SessionFactory
    if _SessionFactory is None:
        init_database()
    return _SessionFactory()
