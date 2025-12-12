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


def bump_version(
    workspace: Path,
    project: str,
    dry_run: bool = False
) -> int:
    """Automatically bump version based on commit messages."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Version Bump: {project}")
    print(f"{'=' * 60}\n")

    proj_dir = workspace / project
    if not proj_dir.exists():
        log_error(f"Project not found: {project}")
        return 1

    pyproject = proj_dir / "pyproject.toml"
    if not pyproject.exists():
        log_error("No pyproject.toml found")
        return 1

    # Get current version
    try:
        import tomllib
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            current_version = data.get("project", {}).get("version", "0.0.0")
    except Exception as e:
        log_error(f"Failed to read version: {e}")
        return 1

    log_info(f"Current version: {current_version}")

    # Get commits since last tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        last_tag = result.stdout.strip()
        log_info(f"Last tag: {last_tag}")
        commit_range = f"{last_tag}..HEAD"
    else:
        log_info("No previous tags found, analyzing all commits")
        commit_range = "HEAD"

    # Get commit messages
    result = subprocess.run(
        ["git", "log", commit_range, "--pretty=format:%s"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )

    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []

    if not commits or commits == [""]:
        log_info("No new commits since last tag")
        return 0

    log_info(f"Analyzing {len(commits)} commits...")

    # Determine bump type
    bump_type = "patch"  # default

    for commit in commits:
        commit_lower = commit.lower()
        if "breaking change" in commit_lower or commit.startswith("!"):
            bump_type = "major"
            break
        elif commit.startswith("feat:") or commit.startswith("feat("):
            if bump_type != "major":
                bump_type = "minor"

    # Parse and bump version
    parts = current_version.split(".")
    if len(parts) != 3:
        log_error(f"Invalid version format: {current_version}")
        return 1

    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])

    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"

    print(f"\n  {CYAN}Bump type:{NC} {bump_type}")
    print(f"  {CYAN}New version:{NC} {current_version} → {new_version}")

    if dry_run:
        log_info("Dry run - no changes made")
        return 0

    # Update pyproject.toml
    content = pyproject.read_text()
    updated = content.replace(
        f'version = "{current_version}"',
        f'version = "{new_version}"'
    )
    pyproject.write_text(updated)
    log_success(f"Updated pyproject.toml to {new_version}")

    # Also update __init__.py if it has __version__
    for init_file in proj_dir.glob("src/*/__init__.py"):
        init_content = init_file.read_text()
        if "__version__" in init_content:
            updated_init = init_content.replace(
                f'__version__ = "{current_version}"',
                f'__version__ = "{new_version}"'
            )
            init_file.write_text(updated_init)
            log_success(f"Updated {init_file.name}")

    # Git commit and tag
    subprocess.run(["git", "add", "-A"], cwd=proj_dir)
    subprocess.run(
        ["git", "commit", "-m", f"chore: bump version to {new_version}"],
        cwd=proj_dir
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release {new_version}"],
        cwd=proj_dir
    )
    log_success(f"Created tag v{new_version}")

    # Auto-push commits and tags
    log_info("Pushing to remote...")
    push_result = subprocess.run(
        ["git", "push"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )
    if push_result.returncode == 0:
        log_success("Pushed commits")
    else:
        log_error(f"Push failed: {push_result.stderr}")
        return 1

    tags_result = subprocess.run(
        ["git", "push", "--tags"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )
    if tags_result.returncode == 0:
        log_success("Pushed tags")
    else:
        log_error(f"Tag push failed: {tags_result.stderr}")
        return 1

    print(f"\n{'=' * 60}")
    print(f"  {GREEN}✓ Version {new_version} released!{NC}")
    print(f"{'=' * 60}\n")

    return 0


def build_project(
    workspace: Path,
    project: str,
    create_dmg: bool = True
) -> int:
    """Build a project using universal-build.sh."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Build: {project}")
    print(f"{'=' * 60}\n")

    razorcore_dir = workspace / "razorcore"
    build_script = razorcore_dir / "universal-build.sh"

    if not build_script.exists():
        log_error("universal-build.sh not found in razorcore/")
        return 1

    proj_dir = workspace / project
    if not proj_dir.exists():
        log_error(f"Project not found: {project}")
        return 1

    log_info(f"Building {project}...")

    result = subprocess.run(
        [str(build_script), project],
        cwd=razorcore_dir
    )

    return result.returncode
