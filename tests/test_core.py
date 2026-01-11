"""Tests for core NanoRange components."""

import pytest
from nanorange.core.schemas import (
    DataType,
    InputSchema,
    OutputSchema,
    ToolSchema,
    ToolType,
    Pipeline,
    PipelineStep,
    StepInput,
    InputSource,
)
from nanorange.core.registry import ToolRegistry
from nanorange.core.pipeline import PipelineManager
from nanorange.core.validator import PipelineValidator


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_input_schema_creation(self):
        """Test creating an input schema."""
        inp = InputSchema(
            name="image_path",
            type=DataType.IMAGE,
            description="Path to image",
            required=True
        )
        assert inp.name == "image_path"
        assert inp.type == DataType.IMAGE
        assert inp.required is True
    
    def test_output_schema_creation(self):
        """Test creating an output schema."""
        out = OutputSchema(
            name="result",
            type=DataType.MASK,
            description="Binary mask"
        )
        assert out.name == "result"
        assert out.type == DataType.MASK
    
    def test_tool_schema_creation(self):
        """Test creating a tool schema."""
        tool = ToolSchema(
            tool_id="test_tool",
            name="Test Tool",
            description="A test tool",
            category="testing",
            inputs=[
                InputSchema(name="input1", type=DataType.STRING, required=True)
            ],
            outputs=[
                OutputSchema(name="output1", type=DataType.STRING)
            ]
        )
        assert tool.tool_id == "test_tool"
        assert len(tool.inputs) == 1
        assert len(tool.outputs) == 1
    
    def test_step_input_static(self):
        """Test creating static step input."""
        inp = StepInput.static("hello")
        assert inp.source == InputSource.STATIC
        assert inp.value == "hello"
    
    def test_step_input_from_step(self):
        """Test creating step input from another step."""
        inp = StepInput.from_step("step1", "output_image")
        assert inp.source == InputSource.STEP_OUTPUT
        assert inp.source_step_id == "step1"
        assert inp.source_output == "output_image"


class TestRegistry:
    """Test tool registry."""
    
    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        registry.clear()
        
        schema = ToolSchema(
            tool_id="test_tool",
            name="Test Tool",
            description="Test",
            inputs=[],
            outputs=[]
        )
        
        def test_impl(**kwargs):
            return {"result": "ok"}
        
        registry.register(schema, test_impl)
        assert registry.has_tool("test_tool")
    
    def test_list_tools(self):
        """Test listing tools."""
        registry = ToolRegistry()
        registry.clear()
        
        for i in range(3):
            schema = ToolSchema(
                tool_id=f"tool_{i}",
                name=f"Tool {i}",
                description="Test",
                category="testing",
                inputs=[],
                outputs=[]
            )
            registry.register(schema, lambda **kw: {})
        
        tools = registry.list_tools()
        assert len(tools) == 3
    
    def test_list_by_category(self):
        """Test listing tools by category."""
        registry = ToolRegistry()
        registry.clear()
        
        registry.register(ToolSchema(
            tool_id="cat_a_1", name="A1", description="Test",
            category="cat_a", inputs=[], outputs=[]
        ), lambda **kw: {})
        
        registry.register(ToolSchema(
            tool_id="cat_b_1", name="B1", description="Test",
            category="cat_b", inputs=[], outputs=[]
        ), lambda **kw: {})
        
        tools_a = registry.list_tools(category="cat_a")
        assert len(tools_a) == 1
        assert tools_a[0].tool_id == "cat_a_1"


class TestPipelineManager:
    """Test pipeline manager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        self.registry.clear()
        
        # Register test tools
        self.registry.register(ToolSchema(
            tool_id="load",
            name="Load",
            description="Load image",
            inputs=[InputSchema(name="path", type=DataType.PATH, required=True)],
            outputs=[OutputSchema(name="image", type=DataType.IMAGE)]
        ), lambda path: {"image": path})
        
        self.registry.register(ToolSchema(
            tool_id="process",
            name="Process",
            description="Process image",
            inputs=[InputSchema(name="image", type=DataType.IMAGE, required=True)],
            outputs=[OutputSchema(name="result", type=DataType.IMAGE)]
        ), lambda image: {"result": image + "_processed"})
        
        self.manager = PipelineManager(registry=self.registry)
    
    def test_create_pipeline(self):
        """Test creating a new pipeline."""
        pipeline = self.manager.new_pipeline("Test Pipeline")
        assert pipeline.name == "Test Pipeline"
        assert len(pipeline.steps) == 0
    
    def test_add_step(self):
        """Test adding a step."""
        self.manager.new_pipeline()
        step = self.manager.add_step("load", "Load Image", {"path": "/test.png"})
        assert step.tool_id == "load"
        assert "path" in step.inputs
    
    def test_connect_steps(self):
        """Test connecting steps."""
        self.manager.new_pipeline()
        self.manager.add_step("load", "Load", {"path": "/test.png"})
        self.manager.add_step("process", "Process")
        
        self.manager.connect_steps("Load", "image", "Process", "image")
        
        pipeline = self.manager.current_pipeline
        process_step = pipeline.get_step_by_name("Process")
        assert process_step.inputs["image"].source == InputSource.STEP_OUTPUT


class TestValidator:
    """Test pipeline validator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        self.registry.clear()
        
        # Register test tools
        self.registry.register(ToolSchema(
            tool_id="step_a",
            name="Step A",
            description="Step A",
            inputs=[InputSchema(name="input", type=DataType.STRING, required=True)],
            outputs=[OutputSchema(name="output", type=DataType.STRING)]
        ), lambda input: {"output": input})
        
        self.registry.register(ToolSchema(
            tool_id="step_b",
            name="Step B",
            description="Step B",
            inputs=[InputSchema(name="input", type=DataType.STRING, required=True)],
            outputs=[OutputSchema(name="output", type=DataType.STRING)]
        ), lambda input: {"output": input})
        
        self.validator = PipelineValidator(self.registry)
    
    def test_valid_pipeline(self):
        """Test validating a correct pipeline."""
        pipeline = Pipeline(name="Test")
        pipeline.add_step(PipelineStep(
            step_id="s1",
            step_name="Step 1",
            tool_id="step_a",
            inputs={"input": StepInput.static("hello")}
        ))
        pipeline.add_step(PipelineStep(
            step_id="s2",
            step_name="Step 2",
            tool_id="step_b",
            inputs={"input": StepInput.from_step("s1", "output")}
        ))
        
        result = self.validator.validate(pipeline)
        assert result.is_valid
    
    def test_missing_required_input(self):
        """Test detecting missing required input."""
        pipeline = Pipeline(name="Test")
        pipeline.add_step(PipelineStep(
            step_id="s1",
            step_name="Step 1",
            tool_id="step_a",
            inputs={}  # Missing required input
        ))
        
        result = self.validator.validate(pipeline)
        assert not result.is_valid
        assert any("Missing required input" in str(e) for e in result.errors)
    
    def test_unknown_tool(self):
        """Test detecting unknown tool reference."""
        pipeline = Pipeline(name="Test")
        pipeline.add_step(PipelineStep(
            step_id="s1",
            step_name="Step 1",
            tool_id="nonexistent_tool",
            inputs={}
        ))
        
        result = self.validator.validate(pipeline)
        assert not result.is_valid
        assert any("Unknown tool" in str(e) for e in result.errors)
    
    def test_execution_order(self):
        """Test getting execution order."""
        pipeline = Pipeline(name="Test")
        pipeline.add_step(PipelineStep(
            step_id="s1",
            step_name="Step 1",
            tool_id="step_a",
            inputs={"input": StepInput.static("hello")}
        ))
        pipeline.add_step(PipelineStep(
            step_id="s2",
            step_name="Step 2",
            tool_id="step_b",
            inputs={"input": StepInput.from_step("s1", "output")}
        ))
        
        order = self.validator.get_execution_order(pipeline)
        assert order == ["s1", "s2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
