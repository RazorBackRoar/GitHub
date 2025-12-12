"""
Razorcore CLI - Command line tools for RazorBackRoar projects.

Commands:
    razorcore sync-configs   - Copy shared configs to all projects
    razorcore verify         - Verify project structure and compliance
    razorcore commit-all     - Commit changes across all projects
    razorcore build          - Build a project (wrapper for universal-build.sh)
"""

from .main import main

__all__ = ["main"]
