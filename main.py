#!/usr/bin/env python3
"""Hybrid Telecom Agent - Main entrypoint."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

def init():
    """Initialize data stores."""
    from src.data_loader import init_sqlite_db, build_vector_store
    print("Building SQLite database...")
    init_sqlite_db()
    print("Building FAISS index...")
    build_vector_store()
    print("Done.")

def cli():
    """Interactive CLI."""
    from src.agent import invoke
    print("Telecom Agent CLI - Type 'quit' to exit\n")
    while True:
        try:
            q = input("You: ").strip()
            if q.lower() in ('quit', 'exit', 'q'):
                break
            if q:
                print(f"\nAgent: {invoke(q)}\n")
        except (KeyboardInterrupt, EOFError):
            break

def serve():
    """Run AgentCore server."""
    from src.agentcore_runtime import app
    app.run()

if __name__ == "__main__":
    cmds = {"init": init, "cli": cli, "serve": serve}
    if len(sys.argv) < 2 or sys.argv[1] not in cmds:
        print(f"Usage: python main.py [{'/'.join(cmds.keys())}]")
        sys.exit(1)
    cmds[sys.argv[1]]()
