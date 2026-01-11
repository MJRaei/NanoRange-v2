"""
Main entry point for NanoRange.

This module provides:
- CLI entry point via nanorange command
- Direct execution via python -m nanorange
"""

from nanorange.cli.commands import cli


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
