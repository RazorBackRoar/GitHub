#!/usr/bin/env python3
"""
Razorcore CLI - Main entry point.

Unified command-line tool for managing RazorBackRoar projects.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .commands import build_project, bump_version, commit_all, list_projects, sync_configs, verify


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for razorcore CLI."""
    parser = argparse.ArgumentParser(
        prog="razorcore",
        description="Unified development tools for RazorBackRoar projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    razorcore sync-configs              # Sync configs to all projects
    razorcore sync-configs 4Charm       # Sync configs to specific project
    razorcore verify                    # Verify all projects
    razorcore commit-all "Fix bug"      # Commit to all projects
    razorcore bump 4Charm               # Auto-bump version based on commits
    razorcore build iSort               # Build project and create DMG
    razorcore list                      # List all managed projects
        """
    )

    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show razorcore version"
    )

    parser.add_argument(
        "--workspace", "-w",
        type=Path,
        default=None,
        help="Path to GitHub workspace (default: auto-detect)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sync-configs command
    sync_parser = subparsers.add_parser(
        "sync-configs",
        aliases=["sync"],
        help="Copy shared configuration files to projects"
    )
    sync_parser.add_argument(
        "projects",
        nargs="*",
        help="Specific projects to sync (default: all)"
    )
    sync_parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without making changes"
    )

    # verify command
    verify_parser = subparsers.add_parser(
        "verify",
        aliases=["check"],
        help="Verify project structure and compliance"
    )
    verify_parser.add_argument(
        "projects",
        nargs="*",
        help="Specific projects to verify (default: all)"
    )
    verify_parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error on any warning"
    )

    # commit-all command
    commit_parser = subparsers.add_parser(
        "commit-all",
        aliases=["commit"],
        help="Commit changes across all projects"
    )
    commit_parser.add_argument(
        "message",
        help="Commit message"
    )
    commit_parser.add_argument(
        "projects",
        nargs="*",
        help="Specific projects to commit (default: all)"
    )
    commit_parser.add_argument(
        "--push", "-p",
        action="store_true",
        help="Push after committing"
    )

    # list command
    subparsers.add_parser(
        "list",
        aliases=["ls"],
        help="List all managed projects"
    )

    # bump command
    bump_parser = subparsers.add_parser(
        "bump",
        help="Auto-bump version based on commit messages"
    )
    bump_parser.add_argument(
        "project",
        help="Project to bump version for"
    )
    bump_parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Show what would be done without making changes"
    )

    # build command
    build_parser = subparsers.add_parser(
        "build",
        help="Build a project and create DMG"
    )
    build_parser.add_argument(
        "project",
        help="Project to build"
    )

    return parser


def get_workspace(specified: Optional[Path] = None) -> Path:
    """Get the workspace path, auto-detecting if not specified."""
    if specified:
        return specified.resolve()

    # Try to find workspace from razorcore location
    razorcore_dir = Path(__file__).parent.parent.parent.parent.parent
    if (razorcore_dir / "razorcore").exists():
        return razorcore_dir

    # Try common locations
    home = Path.home()
    for candidate in [
        home / "GitHub",
        home / "Projects",
        home / "Developer",
        Path.cwd(),
    ]:
        if candidate.exists() and (candidate / "razorcore").exists():
            return candidate

    # Default to current directory
    return Path.cwd()


def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for razorcore CLI."""
    parser = create_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        from razorcore import __version__
        print(f"razorcore {__version__}")
        return 0

    workspace = get_workspace(parsed.workspace)

    if not parsed.command:
        parser.print_help()
        return 0

    # Route to command handlers
    try:
        if parsed.command in ("sync-configs", "sync"):
            return sync_configs(
                workspace=workspace,
                projects=parsed.projects or None,
                dry_run=parsed.dry_run
            )
        elif parsed.command in ("verify", "check"):
            return verify(
                workspace=workspace,
                projects=parsed.projects or None,
                strict=parsed.strict
            )
        elif parsed.command in ("commit-all", "commit"):
            return commit_all(
                workspace=workspace,
                message=parsed.message,
                projects=parsed.projects or None,
                push=parsed.push
            )
        elif parsed.command in ("list", "ls"):
            return list_projects(workspace=workspace)
        elif parsed.command == "bump":
            return bump_version(
                workspace=workspace,
                project=parsed.project,
                dry_run=parsed.dry_run
            )
        elif parsed.command == "build":
            return build_project(
                workspace=workspace,
                project=parsed.project
            )
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
