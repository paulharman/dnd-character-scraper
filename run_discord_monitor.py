#!/usr/bin/env python3
"""
Discord Monitor Launcher

Simple launcher script for the Discord character monitor.
Automatically handles path setup and forwards arguments.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Discord monitor with proper path setup."""
    # Get the project root directory
    project_root = Path(__file__).parent
    discord_script = project_root / "discord" / "discord_monitor.py"
    
    if not discord_script.exists():
        print(f"❌ Discord monitor script not found at: {discord_script}")
        sys.exit(1)
    
    # Forward all arguments to the Discord monitor
    cmd = [sys.executable, str(discord_script)] + sys.argv[1:]
    
    try:
        # Run the Discord monitor
        result = subprocess.run(cmd, cwd=str(project_root))
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n🛑 Discord monitor stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error launching Discord monitor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()