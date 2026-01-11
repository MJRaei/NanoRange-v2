"""
CLI commands for NanoRange.

Provides commands for:
- Starting the orchestrator agent
- Managing pipelines
- Listing tools
"""

import asyncio
import os
import click
from dotenv import load_dotenv
from rich.console import Console

# Load environment variables from .env file
load_dotenv()
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="nanorange")
def cli():
    """NanoRange - Agentic Microscopy Image Analysis"""
    pass


@cli.command()
@click.option(
    "--model", "-m",
    default="gemini-2.0-flash",
    help="Gemini model to use"
)
@click.option(
    "--session", "-s",
    default=None,
    help="Resume an existing session"
)
def chat(model: str, session: str):
    """Start an interactive chat session with the orchestrator."""
    from nanorange.agent.orchestrator import NanoRangeOrchestrator
    from nanorange.storage.database import init_database
    
    # Initialize database
    init_database()
    
    # Create orchestrator
    orchestrator = NanoRangeOrchestrator(model=model, session_id=session)
    
    console.print(Panel.fit(
        "[bold blue]NanoRange[/bold blue] - Microscopy Image Analysis Assistant\n"
        f"Session: {orchestrator.get_session_id()}\n"
        "Type 'exit' or 'quit' to end the session.\n"
        "Type 'help' for available commands.",
        title="Welcome"
    ))
    
    async def run_chat():
        """Run the async chat loop."""
        try:
            while True:
                try:
                    user_input = console.input("\n[bold green]You:[/bold green] ")
                    
                    if user_input.lower() in ('exit', 'quit'):
                        console.print("[yellow]Goodbye![/yellow]")
                        break
                    
                    if user_input.lower() == 'help':
                        _show_help()
                        continue
                    
                    if not user_input.strip():
                        continue
                    
                    # Get response from orchestrator
                    with console.status("[bold blue]Thinking...[/bold blue]"):
                        response = await orchestrator.chat(user_input)
                    
                    console.print(f"\n[bold blue]NanoRange:[/bold blue] {response}")
                    
                except KeyboardInterrupt:
                    console.print("\n[yellow]Interrupted. Goodbye![/yellow]")
                    break
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
        finally:
            await orchestrator.close()
    
    # Run the async chat loop
    asyncio.run(run_chat())


def _show_help():
    """Show help information."""
    help_text = """
## Available Commands

In the chat, you can ask the assistant to:

- **List tools**: "Show me available preprocessing tools"
- **Build pipeline**: "Create a pipeline for nuclei segmentation"
- **Execute**: "Run the pipeline on my image"
- **Modify**: "Increase the threshold value"
- **Save**: "Save this pipeline as 'nuclei_counter'"
- **Load**: "Load my saved pipeline 'nuclei_counter'"

## Tips

- Be specific about what you want to analyze
- Ask about parameters if results aren't good
- Save successful pipelines for reuse
    """
    console.print(Markdown(help_text))


@cli.command()
@click.option(
    "--category", "-c",
    default=None,
    help="Filter by category"
)
def tools(category: str):
    """List available analysis tools."""
    from nanorange.core.registry import get_registry
    from nanorange.storage.database import init_database
    
    init_database()
    registry = get_registry()
    
    # Discover built-in tools
    registry.discover_tools()
    
    tool_list = registry.list_tools(category=category)
    
    if not tool_list:
        console.print("[yellow]No tools found. Add tools to nanorange/tools/builtin/[/yellow]")
        return
    
    table = Table(title="Available Tools")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Category", style="yellow")
    table.add_column("Description")
    
    for tool in tool_list:
        table.add_row(
            tool.tool_id,
            tool.name,
            tool.category,
            tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
        )
    
    console.print(table)


@cli.command()
def pipelines():
    """List saved pipeline templates."""
    from nanorange.storage.session_manager import SessionManager
    from nanorange.storage.database import init_database
    
    init_database()
    session = SessionManager()
    session.create_session()
    
    templates = session.list_templates()
    
    if not templates:
        console.print("[yellow]No saved pipelines found.[/yellow]")
        return
    
    table = Table(title="Saved Pipelines")
    table.add_column("Name", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Description")
    table.add_column("Uses", justify="right")
    
    for t in templates:
        table.add_row(
            t["name"],
            t["category"],
            t["description"][:40] + "..." if len(t["description"]) > 40 else t["description"],
            str(t["use_count"])
        )
    
    console.print(table)


@cli.command()
@click.argument("name")
def show(name: str):
    """Show details of a saved pipeline."""
    from nanorange.storage.session_manager import SessionManager
    from nanorange.storage.database import init_database
    
    init_database()
    session = SessionManager()
    session.create_session()
    
    pipeline = session.load_template(name)
    
    if not pipeline:
        console.print(f"[red]Pipeline '{name}' not found.[/red]")
        return
    
    console.print(Panel.fit(
        f"[bold]{pipeline.name}[/bold]\n"
        f"{pipeline.description}\n\n"
        f"Steps: {len(pipeline.steps)}",
        title="Pipeline"
    ))
    
    for i, step in enumerate(pipeline.steps, 1):
        inputs_str = ", ".join(
            f"{k}={v.value if v.source.value == 'static' else f'<{v.source_step_id}.{v.source_output}>'}"
            for k, v in step.inputs.items()
        )
        console.print(f"  {i}. [cyan]{step.step_name}[/cyan] ({step.tool_id})")
        if inputs_str:
            console.print(f"     Inputs: {inputs_str}")


@cli.command()
@click.option("--port", "-p", default=8000, help="Port for the web interface")
def web(port: int):
    """Start the ADK web interface."""
    import subprocess
    import sys
    
    console.print(f"[bold blue]Starting NanoRange web interface on port {port}...[/bold blue]")
    console.print(f"Open http://localhost:{port} in your browser")
    
    # Run adk web command
    subprocess.run([sys.executable, "-m", "google.adk.cli", "web", "--port", str(port)])


@cli.command()
def init():
    """Initialize the NanoRange database and directories."""
    from nanorange.storage.database import init_database
    from nanorange.storage.file_store import FileStore
    from pathlib import Path
    
    console.print("[bold blue]Initializing NanoRange...[/bold blue]")
    
    # Initialize database
    init_database()
    console.print("  ✓ Database initialized")
    
    # Initialize file store
    FileStore()
    console.print("  ✓ File store initialized")
    
    # Create .env file if it doesn't exist
    env_path = Path(".env")
    if not env_path.exists():
        env_path.write_text('GOOGLE_API_KEY="your-api-key-here"\n')
        console.print("  ✓ Created .env file (add your API key)")
    
    console.print("\n[green]NanoRange initialized successfully![/green]")
    console.print("\nNext steps:")
    console.print("  1. Add your Gemini API key to .env")
    console.print("  2. Run 'nanorange chat' to start")


if __name__ == "__main__":
    cli()
