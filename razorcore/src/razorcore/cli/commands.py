"""
Razorcore CLI Commands Implementation.
"""

import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

# ANSI colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color

# Managed projects
MANAGED_PROJECTS = [
    "4Charm",
    "Nexus",
    "Papyrus",
    "PyPixPro",
    "iSort",
    "LibraLog",
    "czkawka-macos-guide",
]


def log_success(msg: str) -> None:
    print(f"{GREEN}✓{NC} {msg}")


def log_warning(msg: str) -> None:
    print(f"{YELLOW}⚠{NC} {msg}")


def log_error(msg: str) -> None:
    print(f"{RED}✗{NC} {msg}")


def log_info(msg: str) -> None:
    print(f"{CYAN}→{NC} {msg}")


def get_projects(workspace: Path, specified: Optional[List[str]] = None) -> List[Path]:
    """Get list of project directories to operate on."""
    if specified:
        projects = []
        for name in specified:
            proj_path = workspace / name
            if proj_path.exists():
                projects.append(proj_path)
            else:
                log_warning(f"Project not found: {name}")
        return projects
    
    # Return all managed projects that exist
    return [
        workspace / name
        for name in MANAGED_PROJECTS
        if (workspace / name).exists()
    ]


def get_config_files() -> dict[str, Path]:
    """Get paths to razorcore config files."""
    configs_dir = Path(__file__).parent.parent / "configs"
    return {
        ".pylintrc": configs_dir / "pylintrc",
        "pyrightconfig.json": configs_dir / "pyrightconfig.json",
    }


def sync_configs(
    workspace: Path,
    projects: Optional[List[str]] = None,
    dry_run: bool = False
) -> int:
    """Sync shared configuration files to projects."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Config Sync")
    print(f"{'=' * 60}\n")
    
    config_files = get_config_files()
    project_dirs = get_projects(workspace, projects)
    
    if not project_dirs:
        log_error("No projects found to sync")
        return 1
    
    errors = 0
    
    for proj_dir in project_dirs:
        proj_name = proj_dir.name
        print(f"\n{CYAN}[{proj_name}]{NC}")
        
        # Skip non-Python projects
        if not (proj_dir / "pyproject.toml").exists():
            log_info("Skipping (no pyproject.toml)")
            continue
        
        for dest_name, src_path in config_files.items():
            dest_path = proj_dir / dest_name
            
            # Remove symlink if exists
            if dest_path.is_symlink():
                if dry_run:
                    log_info(f"Would remove symlink: {dest_name}")
                else:
                    dest_path.unlink()
                    log_success(f"Removed symlink: {dest_name}")
            
            # Copy config file
            if src_path.exists():
                if dry_run:
                    log_info(f"Would copy: {dest_name}")
                else:
                    shutil.copy2(src_path, dest_path)
                    log_success(f"Copied: {dest_name}")
            else:
                log_error(f"Source not found: {src_path}")
                errors += 1
    
    print(f"\n{'=' * 60}")
    if dry_run:
        print("  Dry run complete - no changes made")
    elif errors == 0:
        print(f"  {GREEN}✓ All configs synced successfully{NC}")
    else:
        print(f"  {RED}✗ Completed with {errors} errors{NC}")
    print(f"{'=' * 60}\n")
    
    return 1 if errors > 0 else 0


def verify(
    workspace: Path,
    projects: Optional[List[str]] = None,
    strict: bool = False
) -> int:
    """Verify project structure and compliance."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Project Verification")
    print(f"{'=' * 60}\n")
    
    project_dirs = get_projects(workspace, projects)
    
    if not project_dirs:
        log_error("No projects found to verify")
        return 1
    
    errors = 0
    warnings = 0
    
    for proj_dir in project_dirs:
        proj_name = proj_dir.name
        print(f"\n{CYAN}[{proj_name}]{NC}")
        
        # Check for pyproject.toml
        if (proj_dir / "pyproject.toml").exists():
            log_success("pyproject.toml exists")
        else:
            if proj_name != "czkawka-macos-guide":
                log_error("pyproject.toml missing")
                errors += 1
            else:
                log_info("Skipping pyproject.toml check (documentation project)")
        
        # Check for symlinks (should NOT exist anymore)
        for config_name in [".pylintrc", "pyrightconfig.json"]:
            config_path = proj_dir / config_name
            if config_path.is_symlink():
                log_error(f"{config_name} is still a symlink!")
                errors += 1
            elif config_path.exists():
                log_success(f"{config_name} is a regular file")
            else:
                if proj_name != "czkawka-macos-guide":
                    log_warning(f"{config_name} missing")
                    warnings += 1
        
        # Check for PORTFOLIO.md symlink (should NOT exist)
        portfolio_path = proj_dir / "docs" / "PORTFOLIO.md"
        if portfolio_path.is_symlink():
            log_error("docs/PORTFOLIO.md is still a symlink!")
            errors += 1
        elif portfolio_path.exists():
            log_success("docs/PORTFOLIO.md is a regular file")
        
        # Check for .dev-tools references
        gitignore = proj_dir / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text()
            if ".dev-tools" in content:
                log_warning(".gitignore still references .dev-tools")
                warnings += 1
        
        # Check README exists
        if (proj_dir / "README.md").exists():
            log_success("README.md exists")
        else:
            log_error("README.md missing")
            errors += 1
        
        # Check LICENSE exists
        has_license = (
            (proj_dir / "LICENSE").exists() or
            (proj_dir / "LICENSE.txt").exists()
        )
        if has_license:
            log_success("LICENSE exists")
        else:
            log_error("LICENSE missing")
            errors += 1
    
    # Check that .dev-tools doesn't exist
    dev_tools = workspace / ".dev-tools"
    print(f"\n{CYAN}[Workspace Checks]{NC}")
    if dev_tools.exists():
        log_error(".dev-tools directory still exists!")
        errors += 1
    else:
        log_success(".dev-tools directory removed")
    
    # Check razorcore exists
    if (workspace / "razorcore").exists():
        log_success("razorcore directory exists")
    else:
        log_error("razorcore directory missing")
        errors += 1
    
    # Summary
    print(f"\n{'=' * 60}")
    if errors == 0 and (warnings == 0 or not strict):
        print(f"  {GREEN}✓ All verifications passed{NC}")
        if warnings > 0:
            print(f"  {YELLOW}  ({warnings} warnings){NC}")
    else:
        print(f"  {RED}✗ Verification failed{NC}")
        print(f"  {RED}  {errors} errors, {warnings} warnings{NC}")
    print(f"{'=' * 60}\n")
    
    if strict and warnings > 0:
        return 1
    return 1 if errors > 0 else 0


def commit_all(
    workspace: Path,
    message: str,
    projects: Optional[List[str]] = None,
    push: bool = False
) -> int:
    """Commit changes across all projects."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Multi-Project Commit")
    print(f"{'=' * 60}\n")
    
    project_dirs = get_projects(workspace, projects)
    
    if not project_dirs:
        log_error("No projects found")
        return 1
    
    errors = 0
    committed = 0
    skipped = 0
    
    for proj_dir in project_dirs:
        proj_name = proj_dir.name
        print(f"\n{CYAN}[{proj_name}]{NC}")
        
        # Check if git repo
        if not (proj_dir / ".git").exists():
            log_info("Not a git repository, skipping")
            skipped += 1
            continue
        
        # Check for changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=proj_dir,
            capture_output=True,
            text=True
        )
        
        if not result.stdout.strip():
            log_info("No changes to commit")
            skipped += 1
            continue
        
        # Stage all changes
        subprocess.run(["git", "add", "-A"], cwd=proj_dir, check=True)
        
        # Commit
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            cwd=proj_dir,
            capture_output=True,
            text=True
        )
        
        if commit_result.returncode == 0:
            log_success(f"Committed: {message[:50]}...")
            committed += 1
            
            # Push if requested
            if push:
                push_result = subprocess.run(
                    ["git", "push"],
                    cwd=proj_dir,
                    capture_output=True,
                    text=True
                )
                if push_result.returncode == 0:
                    log_success("Pushed to remote")
                else:
                    log_error(f"Push failed: {push_result.stderr}")
                    errors += 1
        else:
            if "nothing to commit" in commit_result.stdout:
                log_info("Nothing to commit")
                skipped += 1
            else:
                log_error(f"Commit failed: {commit_result.stderr}")
                errors += 1
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Committed: {committed}, Skipped: {skipped}, Errors: {errors}")
    if errors == 0:
        print(f"  {GREEN}✓ All commits successful{NC}")
    else:
        print(f"  {RED}✗ Some commits failed{NC}")
    print(f"{'=' * 60}\n")
    
    return 1 if errors > 0 else 0


def list_projects(workspace: Path) -> int:
    """List all managed projects and their status."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Managed Projects")
    print(f"  Workspace: {workspace}")
    print(f"{'=' * 60}\n")
    
    for name in MANAGED_PROJECTS:
        proj_dir = workspace / name
        
        if not proj_dir.exists():
            print(f"  {RED}✗{NC} {name} (not found)")
            continue
        
        # Get version if available
        version = "n/a"
        pyproject = proj_dir / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    version = data.get("project", {}).get("version", "n/a")
            except Exception:
                pass
        
        # Check git status
        git_status = ""
        if (proj_dir / ".git").exists():
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=proj_dir,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                git_status = f" {YELLOW}(uncommitted changes){NC}"
            else:
                git_status = f" {GREEN}(clean){NC}"
        
        print(f"  {GREEN}✓{NC} {name} v{version}{git_status}")
    
    print()
    return 0
