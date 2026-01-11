"""
Session Manager - Manages user sessions and pipeline state.

Provides a high-level interface for:
- Creating and managing sessions
- Persisting pipeline state
- Saving and loading pipeline templates
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from nanorange.core.schemas import Pipeline, PipelineResult, StepStatus
from nanorange.storage.database import (
    get_session,
    SessionModel,
    PipelineModel,
    StepModel,
    ResultModel,
    SavedPipelineModel,
)


class SessionManager:
    """
    Manages sessions and pipeline persistence.
    
    Each session represents a user's interaction with the system,
    containing one or more pipelines and their execution results.
    """
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize session manager.
        
        Args:
            session_id: Existing session ID to resume, or None for new session
        """
        self._db = get_session()
        
        if session_id:
            self._session = self._db.query(SessionModel).filter_by(
                id=session_id
            ).first()
            if not self._session:
                raise ValueError(f"Session not found: {session_id}")
        else:
            self._session = None
    
    @property
    def session_id(self) -> Optional[str]:
        """Get current session ID."""
        return self._session.id if self._session else None
    
    def create_session(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new session.
        
        Args:
            metadata: Optional session metadata
            
        Returns:
            New session ID
        """
        self._session = SessionModel(
            id=str(uuid4()),
            status="active",
        )
        if metadata:
            self._session.session_metadata = metadata
        
        self._db.add(self._session)
        self._db.commit()
        
        return self._session.id
    
    def end_session(self, status: str = "completed") -> None:
        """Mark the current session as ended."""
        if self._session:
            self._session.status = status
            self._session.updated_at = datetime.utcnow()
            self._db.commit()
    
    def save_pipeline(self, pipeline: Pipeline) -> str:
        """
        Save a pipeline to the current session.
        
        Args:
            pipeline: Pipeline to save
            
        Returns:
            Pipeline ID
        """
        if not self._session:
            raise ValueError("No active session. Call create_session() first.")
        
        # Check if pipeline already exists
        existing = self._db.query(PipelineModel).filter_by(
            id=pipeline.pipeline_id
        ).first()
        
        if existing:
            # Update existing
            existing.name = pipeline.name
            existing.description = pipeline.description
            existing.definition = pipeline.model_dump()
            existing.modified_at = datetime.utcnow()
        else:
            # Create new
            pipeline_model = PipelineModel(
                id=pipeline.pipeline_id,
                session_id=self._session.id,
                name=pipeline.name,
                description=pipeline.description,
                definition_json=pipeline.model_dump_json(),
            )
            self._db.add(pipeline_model)
        
        self._db.commit()
        return pipeline.pipeline_id
    
    def load_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        """
        Load a pipeline by ID.
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            Pipeline or None if not found
        """
        pipeline_model = self._db.query(PipelineModel).filter_by(
            id=pipeline_id
        ).first()
        
        if not pipeline_model:
            return None
        
        return Pipeline.model_validate(pipeline_model.definition)
    
    def list_pipelines(self) -> List[Dict[str, Any]]:
        """List all pipelines in the current session."""
        if not self._session:
            return []
        
        pipelines = self._db.query(PipelineModel).filter_by(
            session_id=self._session.id
        ).all()
        
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "status": p.status,
                "created_at": p.created_at.isoformat(),
                "modified_at": p.modified_at.isoformat(),
            }
            for p in pipelines
        ]
    
    def save_result(self, result: PipelineResult) -> None:
        """
        Save pipeline execution results.
        
        Args:
            result: Pipeline execution result
        """
        # Get pipeline model
        pipeline_model = self._db.query(PipelineModel).filter_by(
            id=result.pipeline_id
        ).first()
        
        if not pipeline_model:
            raise ValueError(f"Pipeline not found: {result.pipeline_id}")
        
        # Update pipeline status
        if result.status == StepStatus.COMPLETED:
            pipeline_model.status = "executed"
        elif result.status == StepStatus.FAILED:
            pipeline_model.status = "failed"
        
        # Save step results
        for step_result in result.step_results:
            # Find or create step model
            step_model = self._db.query(StepModel).filter_by(
                pipeline_id=result.pipeline_id,
                step_id=step_result.step_id
            ).first()
            
            if not step_model:
                step_model = StepModel(
                    pipeline_id=result.pipeline_id,
                    step_id=step_result.step_id,
                    step_name=step_result.step_name,
                    tool_id=step_result.tool_id,
                )
                self._db.add(step_model)
            
            step_model.status = step_result.status
            step_model.error_message = step_result.error_message
            step_model.started_at = step_result.started_at
            step_model.completed_at = step_result.completed_at
            step_model.duration_seconds = step_result.duration_seconds
            step_model.inputs = step_result.resolved_inputs
            
            self._db.flush()  # Get step model ID
            
            # Save outputs as results
            for output_name, output_value in step_result.outputs.items():
                result_model = ResultModel(
                    step_id=step_model.id,
                    output_name=output_name,
                )
                
                # Determine value type
                if isinstance(output_value, str) and (
                    output_value.endswith(('.png', '.jpg', '.tif', '.tiff'))
                ):
                    result_model.set_value(output_value, "path")
                elif isinstance(output_value, (dict, list)):
                    result_model.set_value(output_value, "json")
                elif isinstance(output_value, (int, float)):
                    result_model.set_value(output_value, "number")
                else:
                    result_model.set_value(output_value, "string")
                
                self._db.add(result_model)
        
        self._db.commit()
    
    def get_result(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution results for a pipeline.
        
        Args:
            pipeline_id: Pipeline ID
            
        Returns:
            Results dictionary or None
        """
        pipeline_model = self._db.query(PipelineModel).filter_by(
            id=pipeline_id
        ).first()
        
        if not pipeline_model:
            return None
        
        steps = self._db.query(StepModel).filter_by(
            pipeline_id=pipeline_id
        ).all()
        
        step_results = []
        for step in steps:
            results = self._db.query(ResultModel).filter_by(
                step_id=step.id
            ).all()
            
            step_results.append({
                "step_id": step.step_id,
                "step_name": step.step_name,
                "tool_id": step.tool_id,
                "status": step.status.value if step.status else "pending",
                "error_message": step.error_message,
                "duration_seconds": step.duration_seconds,
                "inputs": step.inputs,
                "outputs": {r.output_name: r.get_value() for r in results},
            })
        
        return {
            "pipeline_id": pipeline_id,
            "pipeline_name": pipeline_model.name,
            "status": pipeline_model.status,
            "step_results": step_results,
        }
    
    # =========================================================================
    # Saved Pipeline Templates
    # =========================================================================
    
    def save_as_template(
        self,
        pipeline: Pipeline,
        name: str,
        description: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None
    ) -> int:
        """
        Save a pipeline as a reusable template.
        
        Args:
            pipeline: Pipeline to save
            name: Template name (must be unique)
            description: Template description
            category: Template category
            tags: Searchable tags
            
        Returns:
            Template ID
        """
        # Check for existing template with same name
        existing = self._db.query(SavedPipelineModel).filter_by(name=name).first()
        if existing:
            raise ValueError(f"Template with name '{name}' already exists")
        
        template = SavedPipelineModel(
            name=name,
            description=description,
            category=category,
            definition_json=pipeline.model_dump_json(),
        )
        if tags:
            template.tags = tags
        
        self._db.add(template)
        self._db.commit()
        
        return template.id
    
    def load_template(self, name: str) -> Optional[Pipeline]:
        """
        Load a saved pipeline template.
        
        Args:
            name: Template name
            
        Returns:
            Pipeline or None if not found
        """
        template = self._db.query(SavedPipelineModel).filter_by(name=name).first()
        if not template:
            return None
        
        # Update usage stats
        template.use_count += 1
        template.last_used_at = datetime.utcnow()
        self._db.commit()
        
        # Create new pipeline from template
        pipeline = Pipeline.model_validate(template.definition)
        pipeline.pipeline_id = str(uuid4())  # New ID for this instance
        pipeline.created_at = datetime.utcnow()
        pipeline.modified_at = datetime.utcnow()
        
        return pipeline
    
    def list_templates(
        self,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List saved pipeline templates.
        
        Args:
            category: Filter by category
            
        Returns:
            List of template summaries
        """
        query = self._db.query(SavedPipelineModel)
        if category:
            query = query.filter_by(category=category)
        
        templates = query.order_by(SavedPipelineModel.name).all()
        
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "tags": t.tags,
                "use_count": t.use_count,
                "created_at": t.created_at.isoformat(),
            }
            for t in templates
        ]
    
    def delete_template(self, name: str) -> bool:
        """Delete a saved template."""
        template = self._db.query(SavedPipelineModel).filter_by(name=name).first()
        if not template:
            return False
        
        self._db.delete(template)
        self._db.commit()
        return True
    
    def close(self) -> None:
        """Close the database session."""
        self._db.close()
