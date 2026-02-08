<h1 align="center">NanoRange</h1>

<p align="center">
  <strong>Agentic Microscopy Image Analysis System</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License">
  <img src="https://img.shields.io/badge/status-alpha-orange?style=flat-square" alt="Alpha">
  <img src="https://img.shields.io/badge/powered%20by-Gemini-4285F4?style=flat-square&logo=google&logoColor=white" alt="Powered by Gemini">
</p>

<p align="center">
  NanoRange is a modular, Gemini-powered platform for automated microscopy image analysis.<br>
  An intelligent orchestrator agent dynamically builds, executes, and refines image processing pipelines by connecting specialized tools — so you describe <em>what</em> you want to analyze, and NanoRange figures out <em>how</em>.
</p>

---

<p align="center">
  <img src="docs/media/nanorange.gif" alt="NanoRange Demo" width="720">
</p>

---

## Workflow

<p align="center">
  <img src="docs/media/workflow.png" alt="NanoRange Workflow" width="800">
</p>

---

## Video Walkthrough

<p align="center">
  <a href="https://www.youtube.com/watch?v=VIDEO_ID">
    <img src="https://img.shields.io/badge/Watch%20on%20YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white" alt="Watch on YouTube" height="40">
  </a>
</p>

---

## Key Features

- **Dynamic Pipeline Building** — The Gemini agent plans and connects tools based on your analysis goals, no manual wiring needed.
- **Iterative Refinement** — Pipelines are automatically reviewed and re-optimized until quality thresholds are met.
- **Modular Tool System** — Easily extensible with function tools, class-based tools, or agent-as-tools.
- **Full Traceability** — Every step, input, output, and parameter decision is logged and reviewable.
- **Pipeline Persistence** — Save successful pipelines as reusable templates.
- **Type-Safe Connections** — Automatic validation of tool input/output compatibility via Pydantic schemas.
- **Multi-Agent Architecture** — Coordinator, Planner, and Executor agents collaborate to handle complex requests.
- **Web & CLI Interfaces** — Use the interactive CLI or the full-stack Next.js web UI.

---

## Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────────────────┐
│           Root Coordinator Agent            │
│          (routes to sub-agents)             │
└──────────────┬──────────────┬───────────────┘
               │              │
       ┌───────▼──────┐ ┌────▼────────────┐
       │   Planner    │ │    Executor     │
       │   Agent      │ │    Agent        │
       │              │ │                 │
       │ • Analyze    │ │ • Build pipeline│
       │   request    │ │ • Validate      │
       │ • Select     │ │ • Execute       │
       │   tools      │ │ • Refine        │
       │ • Design     │ │                 │
       │   pipeline   │ │                 │
       └──────────────┘ └────────┬────────┘
                                 │
                                 ▼
               ┌─────────────────────────────┐
               │       Pipeline Engine       │
               │  • Topological execution    │
               │  • Type validation          │
               │  • Result storage           │
               └──────────────┬──────────────┘
                              │
                              ▼
               ┌─────────────────────────────┐
               │       Tool Registry         │
               ├─────────────────────────────┤
               │ Preprocessing │ Segmentation│
               │ Measurement   │ VLM / AI    │
               │ I/O           │ ML (Cellpose│
               │               │  MicroSAM)  │
               └─────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10 or higher
- A [Google Gemini API key](https://aistudio.google.com/apikey)
- Node.js 18+ (only if using the web interface)

### Installation

```bash
# Clone the repository
git clone https://github.com/nanorange/nanorange.git
cd nanorange

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install the package
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```bash
GOOGLE_API_KEY="your-api-key-here"
```

Then initialize the project:

```bash
nanorange init
```

<details>
<summary><strong>Optional environment variables</strong></summary>

| Variable              | Default                  | Description                                 |
| --------------------- | ------------------------ | ------------------------------------------- |
| `GEMINI_MODEL`        | `gemini-3-pro-preview`   | Model used by the orchestrator agents       |
| `IMAGE_MODEL`         | `gemini-2.5-flash-image` | Model used for image generation/enhancement |
| `DATABASE_PATH`       | `./data/nanorange.db`    | Path to the SQLite database                 |
| `MAX_TOOL_ITERATIONS` | `3`                      | Max refinement iterations per tool          |
| `REFINEMENT_ENABLED`  | `true`                   | Enable/disable adaptive refinement          |

</details>

---

## Usage

### Interactive Chat (CLI)

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

### Web Interface

Start the backend and frontend:

```bash
# Terminal 1 — API server
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend && npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

### CLI Commands

| Command                          | Description                                            |
| -------------------------------- | ------------------------------------------------------ |
| `nanorange chat`                 | Start an interactive chat session                      |
| `nanorange chat --mode planner`  | Planner-only mode (design pipelines without executing) |
| `nanorange chat --mode executor` | Executor-only mode (run pre-built pipelines)           |
| `nanorange tools`                | List all available tools                               |
| `nanorange pipelines`            | List saved pipelines                                   |
| `nanorange web --port 8000`      | Launch the ADK web interface                           |

---

## Creating Custom Tools

### Function Tool (Decorator)

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
        return {
            "result_image": output_path,
            "measurements": {"count": 42, "mean_size": 100.5}
        }
```

### Agent Tool

```python
from nanorange.tools import AgentToolBase

class GeminiEnhancerTool(AgentToolBase):
    tool_id = "gemini_enhancer"
    name = "Gemini Image Enhancer"
    description = "Enhance images using Gemini"
    category = "ai"

    def setup_agent(self):
        from google.adk.agents.llm_agent import Agent
        self.agent = Agent(
            model='gemini-2.0-flash',
            name='enhancer',
            instruction="Enhance microscopy images",
        )

    async def execute_agent(self, image_path: str, instructions: str):
        result = await self.agent.run(f"Enhance {image_path}: {instructions}")
        return {"enhanced_image": result.output_path}
```

---

## Data Types

NanoRange uses a typed connection system to validate tool compatibility:

| Type           | Description                               |
| -------------- | ----------------------------------------- |
| `IMAGE`        | Path to an image file                     |
| `MASK`         | Binary mask image path                    |
| `FLOAT`        | Floating point number                     |
| `INT`          | Integer                                   |
| `STRING`       | Text string                               |
| `BOOL`         | Boolean                                   |
| `LIST`         | List of values                            |
| `DICT`         | Dictionary                                |
| `MEASUREMENTS` | Measurement results (counts, areas, etc.) |
| `PARAMETERS`   | Parameter dictionary                      |
| `INSTRUCTIONS` | Text instructions (for agent tools)       |

---

## Project Structure

```
nanorange/
├── agent/
│   ├── agents.py              # Multi-agent system (root, planner, executor)
│   ├── orchestrator.py        # High-level orchestration interface
│   ├── meta_tools.py          # Pipeline manipulation tools
│   ├── planner_tools.py       # Planner agent tools
│   ├── prompts/               # System prompts for each agent
│   └── refinement/            # Adaptive refinement engine
│       ├── adaptive_executor.py
│       ├── image_reviewer.py
│       └── parameter_optimizer.py
├── core/
│   ├── schemas.py             # Pydantic models & data types
│   ├── registry.py            # Tool registry (singleton)
│   ├── pipeline.py            # Pipeline manager
│   ├── executor.py            # Pipeline executor
│   └── validator.py           # Pipeline validator
├── storage/
│   ├── database.py            # SQLAlchemy models
│   ├── session_manager.py     # Session lifecycle
│   └── file_store.py          # File management
├── tools/
│   ├── base.py                # ToolBase abstract class
│   ├── decorators.py          # @tool decorator
│   └── builtin/               # Built-in tools
│       ├── io_tools.py
│       ├── preprocessing.py
│       ├── segmentation.py
│       ├── measurement.py
│       ├── vlm_tools/         # Vision-language model tools
│       └── ml_tools/          # Deep learning tools (Cellpose, MicroSAM)
├── cli/
│   └── commands.py            # CLI entry points
└── main.py                    # CLI main
api/
├── main.py                    # FastAPI application
└── routes/                    # REST API endpoints
frontend/                      # Next.js 16 + React 19 web UI
tests/                         # Test suite
docs/
└── media/                     # Demo GIF, workflow diagram
```

---

## Tech Stack

| Layer                | Technology                          |
| -------------------- | ----------------------------------- |
| **AI / Agents**      | Google ADK, Gemini                  |
| **Backend**          | Python 3.10+, FastAPI, SQLAlchemy   |
| **Frontend**         | Next.js 16, React 19, Tailwind CSS  |
| **Image Processing** | Pillow, NumPy, SciPy                |
| **ML Models**        | Cellpose, MicroSAM                  |
| **Database**         | SQLite (via SQLAlchemy + aiosqlite) |
| **CLI**              | Click, Rich                         |

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes
4. Open a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Google ADK](https://google.github.io/adk-docs/)
- Powered by [Gemini](https://ai.google.dev/)
