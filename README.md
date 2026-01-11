# NanoRange

**Agentic Microscopy Image Analysis System**

NanoRange is a modular AI-powered system for microscopy image analysis. An intelligent orchestrator agent dynamically builds, executes, and refines image analysis pipelines by connecting specialized tools.

## Features

- **Dynamic Pipeline Building**: The AI agent plans and connects tools based on your analysis goals
- **Modular Tool System**: Easily extensible with function tools or agent-as-tools
- **Full Traceability**: Review all steps, inputs, and outputs of your analysis
- **Pipeline Persistence**: Save successful pipelines for reuse
- **Type-Safe Connections**: Automatic validation of tool input/output compatibility

## Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────────────┐
│         Orchestrator Agent              │
│    (Gemini via Google ADK)              │
└─────────────────────────────────────────┘
     │
     │ Uses Meta-Tools
     ▼
┌─────────────────────────────────────────┐
│         Pipeline Engine                 │
│  • Build pipelines                      │
│  • Connect tool outputs to inputs       │
│  • Validate and execute                 │
└─────────────────────────────────────────┘
     │
     │ Executes
     ▼
┌─────────────────────────────────────────┐
│         Tool Registry                   │
│  • Preprocessing tools                  │
│  • Segmentation tools                   │
│  • Measurement tools                    │
│  • AI/Agent tools                       │
└─────────────────────────────────────────┘
```

## Installation

```bash
# Clone the repository
git clone https://github.com/nanorange/nanorange.git
cd nanorange

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Configuration

1. Get a Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

2. Create a `.env` file:
```bash
echo 'GOOGLE_API_KEY="your-api-key-here"' > .env
```

3. Initialize NanoRange:
```bash
nanorange init
```

## Usage

### Interactive Chat

Start an interactive session with the orchestrator:

```bash
nanorange chat
```

Example conversation:
```
You: I want to count cells in my fluorescence image

NanoRange: I'll help you build a cell counting pipeline. First, let me see 
what tools are available...

I'll create a pipeline with these steps:
1. Load your image
2. Apply Gaussian blur to reduce noise
3. Threshold to create a binary mask
4. Find and count the objects

Let me build this pipeline for you...
```

### List Available Tools

```bash
nanorange tools
```

### List Saved Pipelines

```bash
nanorange pipelines
```

### Using with ADK Web Interface

```bash
nanorange web --port 8000
```

Or directly with ADK:
```bash
adk web --port 8000
```

## Creating Custom Tools

### Function Tool

```python
from nanorange.tools import tool
from nanorange.core.schemas import DataType

@tool(
    tool_id="my_custom_filter",
    name="My Custom Filter",
    category="preprocessing",
    output_type=DataType.IMAGE,
    output_name="filtered_image",
)
def my_custom_filter(image_path: str, strength: float = 0.5) -> str:
    """Apply my custom filter to an image.
    
    Args:
        image_path: Path to input image
        strength: Filter strength (0-1)
    """
    # Your implementation here
    output_path = process_image(image_path, strength)
    return output_path
```

### Class-Based Tool

```python
from nanorange.tools import ToolBase
from nanorange.core.schemas import DataType, InputSchema, OutputSchema

class MyAdvancedTool(ToolBase):
    tool_id = "my_advanced_tool"
    name = "My Advanced Tool"
    description = "An advanced analysis tool"
    category = "analysis"
    
    inputs = [
        InputSchema(name="image_path", type=DataType.IMAGE, required=True),
        InputSchema(name="threshold", type=DataType.FLOAT, default=0.5),
    ]
    outputs = [
        OutputSchema(name="result_image", type=DataType.IMAGE),
        OutputSchema(name="measurements", type=DataType.MEASUREMENTS),
    ]
    
    def execute(self, image_path: str, threshold: float = 0.5):
        # Your implementation
        return {
            "result_image": output_path,
            "measurements": {"count": 42, "mean_size": 100.5}
        }
```

### Agent Tool

```python
from nanorange.tools import AgentToolBase

class AIEnhancerTool(AgentToolBase):
    tool_id = "ai_enhancer"
    name = "AI Image Enhancer"
    description = "Enhance images using AI"
    category = "ai"
    
    def setup_agent(self):
        from google.adk.agents.llm_agent import Agent
        self.agent = Agent(
            model='gemini-2.0-flash',
            name='enhancer',
            instruction="Enhance microscopy images",
        )
    
    async def execute_agent(self, image_path: str, instructions: str):
        # Use sub-agent for enhancement
        result = await self.agent.run(f"Enhance {image_path}: {instructions}")
        return {"enhanced_image": result.output_path}
```

## Project Structure

```
nanorange/
├── __init__.py
├── main.py                    # CLI entry point
├── agent.py                   # ADK root_agent
├── agent/
│   ├── orchestrator.py        # Main ADK agent
│   ├── prompts.py             # System prompts
│   └── meta_tools.py          # Pipeline manipulation tools
├── core/
│   ├── schemas.py             # Pydantic schemas
│   ├── registry.py            # Tool registry
│   ├── pipeline.py            # Pipeline models
│   ├── executor.py            # Pipeline executor
│   └── validator.py           # Pipeline validator
├── storage/
│   ├── database.py            # SQLAlchemy models
│   ├── session_manager.py     # State management
│   └── file_store.py          # File handling
├── tools/
│   ├── base.py                # Base classes
│   ├── decorators.py          # @tool decorator
│   └── builtin/               # Built-in tools
└── cli/
    └── commands.py            # CLI commands
```

## Data Types

NanoRange supports these data types for tool inputs/outputs:

| Type | Description |
|------|-------------|
| `IMAGE` | Path to an image file |
| `MASK` | Binary mask image path |
| `FLOAT` | Floating point number |
| `INT` | Integer |
| `STRING` | Text string |
| `BOOL` | Boolean |
| `LIST` | List of values |
| `DICT` | Dictionary |
| `MEASUREMENTS` | Measurement results |
| `PARAMETERS` | Parameter dictionary |
| `INSTRUCTIONS` | Text instructions (for agent tools) |

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

## Acknowledgments

- Built with [Google ADK](https://google.github.io/adk-docs/)
- Powered by [Gemini](https://ai.google.dev/)
