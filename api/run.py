#!/usr/bin/env python3
"""
Script to run the NanoRange API server.

Usage:
    python api/run.py [--host HOST] [--port PORT]
    
Example:
    python api/run.py --host 0.0.0.0 --port 8000
"""

import argparse
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, PROJECT_ROOT)


def main():
    parser = argparse.ArgumentParser(description="Run the NanoRange API server")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    args = parser.parse_args()
    
    os.chdir(PROJECT_ROOT)
    
    import uvicorn
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    NanoRange API Server                  ║
╠══════════════════════════════════════════════════════════╣
║  Starting server at http://{args.host}:{args.port}                  ║
║  API docs available at http://localhost:{args.port}/docs        ║
║  Press Ctrl+C to stop                                    ║
╚══════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run(
        "api.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()

