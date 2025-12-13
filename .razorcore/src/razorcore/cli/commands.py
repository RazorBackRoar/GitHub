"""
Razorcore CLI Commands Implementation.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# ANSI colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
NC = "\033[0m"  # No Color

# Managed projects (note: .razorcore is hidden)
MANAGED_PROJECTS = [
    "4Charm",
    "Nexus",
    "Papyrus",
    "PyPixPro",
    "iSort",
    "czkawka-macos-guide",
    ".razorcore",
]

# Projects that can be built into apps (excludes documentation and library projects)
BUILDABLE_PROJECTS = [
    "4Charm",
    "Nexus",
    "Papyrus",
    "PyPixPro",
    "iSort",
]

DOC_ONLY_PROJECTS = {"czkawka-macos-guide"}


def log_success(msg: str) -> None:
    print(f"{GREEN}✓{NC} {msg}")


def log_warning(msg: str) -> None:
    print(f"{YELLOW}⚠{NC} {msg}")


def log_error(msg: str) -> None:
    print(f"{RED}✗{NC} {msg}")


def log_info(msg: str) -> None:
    print(f"{CYAN}→{NC} {msg}")


def get_projects(workspace: Path, specified: list[str] | None = None) -> list[Path]:
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
    projects: list[str] | None = None,
    dry_run: bool = False
) -> int:
    """Sync shared configuration files to projects."""
    print(f"\n{'=' * 60}")
    print("  Razorcore Config Sync")
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
    projects: list[str] | None = None,
    strict: bool = False
) -> int:
    """Verify project structure and compliance."""
    print(f"\n{'=' * 60}")
    print("  Razorcore Project Verification")
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
            log_error("pyproject.toml missing")
            errors += 1

        # Check for symlinks (should NOT exist anymore)
        for config_name in [".pylintrc", "pyrightconfig.json"]:
            config_path = proj_dir / config_name
            if config_path.is_symlink():
                log_error(f"{config_name} is still a symlink!")
                errors += 1
            elif config_path.exists():
                log_success(f"{config_name} is a regular file")
            else:
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
        has_license = (proj_dir / "LICENSE").exists()
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

    # Check .razorcore exists
    if (workspace / ".razorcore").exists():
        log_success(".razorcore directory exists")
    else:
        log_error(".razorcore directory missing")
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
    projects: list[str] | None = None,
    push: bool = False
) -> int:
    """Commit changes across all projects."""
    print(f"\n{'=' * 60}")
    print("  Razorcore Multi-Project Commit")
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
    print("  Razorcore Managed Projects")
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

    # Check if project is buildable
    if project not in BUILDABLE_PROJECTS:
        log_error(f"{project} is not a buildable app (documentation or library project)")
        log_info(f"Buildable projects: {', '.join(BUILDABLE_PROJECTS)}")
        return 1

    razorcore_dir = workspace / ".razorcore"
    build_script = razorcore_dir / "universal-build.sh"

    if not build_script.exists():
        log_error("universal-build.sh not found in .razorcore/")
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


def auto_bump_version(
    workspace: Path,
    project: str
) -> int:
    """
    Automatically bump version based on commit messages (silent version).
    Called by save_project after a successful commit.
    Returns 0 on success, 1 if no bump needed or error.
    """
    proj_dir = workspace / project
    pyproject = proj_dir / "pyproject.toml"

    if not pyproject.exists():
        return 1

    # Get current version
    try:
        import tomllib
        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            current_version = data.get("project", {}).get("version", "0.0.0")
    except Exception:
        return 1

    # Get commits since last tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        last_tag = result.stdout.strip()
        commit_range = f"{last_tag}..HEAD"
    else:
        # No tags yet, analyze last commit only
        commit_range = "-1"

    # Get commit messages
    if commit_range == "-1":
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=format:%s"],
            cwd=proj_dir,
            capture_output=True,
            text=True
        )
    else:
        result = subprocess.run(
            ["git", "log", commit_range, "--pretty=format:%s"],
            cwd=proj_dir,
            capture_output=True,
            text=True
        )

    commits = result.stdout.strip().split("\n") if result.stdout.strip() else []

    if not commits or commits == [""]:
        return 1  # No commits to analyze

    # Determine bump type from the most recent commit
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
        return 1

    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return 1

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

    log_info(f"Version: {current_version} → {new_version} ({bump_type})")

    # Update pyproject.toml
    content = pyproject.read_text()
    updated = content.replace(
        f'version = "{current_version}"',
        f'version = "{new_version}"'
    )
    pyproject.write_text(updated)

    # Also update __init__.py if it has __version__
    for init_file in proj_dir.glob("src/*/__init__.py"):
        init_content = init_file.read_text()
        if "__version__" in init_content:
            updated_init = init_content.replace(
                f'__version__ = "{current_version}"',
                f'__version__ = "{new_version}"'
            )
            init_file.write_text(updated_init)

    # Also update dmg-config.json if it exists
    dmg_config = proj_dir / "build" / "dmg-config.json"
    if dmg_config.exists():
        import json
        try:
            with open(dmg_config, "r") as f:
                dmg_data = json.load(f)
            dmg_data["version"] = new_version
            with open(dmg_config, "w") as f:
                json.dump(dmg_data, f, indent=2)
        except Exception:
            pass  # Non-critical, continue

    # Git commit and tag
    subprocess.run(["git", "add", "-A"], cwd=proj_dir)
    subprocess.run(
        ["git", "commit", "-m", f"chore: bump version to {new_version}"],
        cwd=proj_dir,
        capture_output=True
    )
    subprocess.run(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release {new_version}"],
        cwd=proj_dir,
        capture_output=True
    )
    log_success(f"Created tag v{new_version}")

    # Push commits and tags
    subprocess.run(["git", "push"], cwd=proj_dir, capture_output=True)
    subprocess.run(["git", "push", "--tags"], cwd=proj_dir, capture_output=True)
    log_success("Pushed version bump and tags")

    return 0


def save_project(
    workspace: Path,
    project: str,
    auto_bump: bool = True
) -> int:
    """Auto-generate commit message, commit, push, and auto-bump version."""
    print(f"\n{'=' * 60}")
    print(f"  Razorcore Save: {project}")
    print(f"{'=' * 60}\n")

    proj_dir = workspace / project
    if not proj_dir.exists():
        log_error(f"Project not found: {project}")
        return 1

    # Check for changes
    status_result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )

    if not status_result.stdout.strip():
        log_info("No changes to commit")
        return 0

    # Analyze changes to generate commit message
    changes = status_result.stdout.strip().split("\n")

    # Categorize changes
    added = []
    modified = []
    deleted = []

    for change in changes:
        if not change.strip():
            continue
        status = change[:2].strip()
        filename = change[3:].strip()

        if 'A' in status or '?' in status:
            added.append(filename)
        elif 'D' in status:
            deleted.append(filename)
        else:
            modified.append(filename)

    # Generate commit message
    # Check if it's a feature, fix, or general change
    all_files = added + modified + deleted

    # Detect type based on files changed
    commit_type = "chore"
    scope = ""

    for f in all_files:
        if "test" in f.lower():
            commit_type = "test"
            break
        elif "fix" in f.lower() or "bug" in f.lower():
            commit_type = "fix"
            break
        elif any(x in f.lower() for x in ["feature", "new", "add"]):
            commit_type = "feat"
            break
        elif f.endswith(".py"):
            # Check diff for clues
            diff_result = subprocess.run(
                ["git", "diff", "--cached", f, "--", f],
                cwd=proj_dir,
                capture_output=True,
                text=True
            )
            diff_text = diff_result.stdout.lower()
            if "def " in diff_text and "+" in diff_text:
                commit_type = "feat"
            elif "fix" in diff_text or "bug" in diff_text:
                commit_type = "fix"

    # Determine scope from most common directory
    dirs = set()
    for f in all_files:
        parts = f.split("/")
        if len(parts) > 1:
            dirs.add(parts[-2] if parts[-1].endswith(".py") else parts[-1].split(".")[0])

    if len(dirs) == 1:
        scope = f"({list(dirs)[0]})"

    # Build description
    if len(added) > 0 and len(modified) == 0 and len(deleted) == 0:
        desc = f"add {', '.join([f.split('/')[-1] for f in added[:3]])}"
        if len(added) > 3:
            desc += f" and {len(added) - 3} more"
    elif len(deleted) > 0 and len(added) == 0 and len(modified) == 0:
        desc = f"remove {', '.join([f.split('/')[-1] for f in deleted[:3]])}"
    elif len(modified) > 0:
        desc = f"update {', '.join([f.split('/')[-1] for f in modified[:3]])}"
        if len(modified) > 3:
            desc += f" and {len(modified) - 3} more"
    else:
        desc = f"update {len(all_files)} files"

    commit_msg = f"{commit_type}{scope}: {desc}"

    log_info(f"Generated message: {commit_msg}")

    # Stage all changes
    subprocess.run(["git", "add", "-A"], cwd=proj_dir)

    # Commit
    commit_result = subprocess.run(
        ["git", "commit", "-m", commit_msg],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )

    if commit_result.returncode != 0:
        log_error(f"Commit failed: {commit_result.stderr}")
        return 1

    log_success(f"Committed: {commit_msg}")

    # Push
    log_info("Pushing to remote...")
    push_result = subprocess.run(
        ["git", "push"],
        cwd=proj_dir,
        capture_output=True,
        text=True
    )

    if push_result.returncode == 0:
        log_success("Pushed to GitHub")
    else:
        log_error(f"Push failed: {push_result.stderr}")
        return 1

    # Auto-bump version if enabled and project has pyproject.toml
    pyproject = proj_dir / "pyproject.toml"
    if auto_bump and pyproject.exists():
        log_info("Auto-bumping version...")
        bump_result = auto_bump_version(workspace, project)
        if bump_result != 0:
            log_warning("Version bump skipped (no commits since last tag or error)")

    print(f"\n{'=' * 60}")
    print(f"  {GREEN}✓ Saved and pushed!{NC}")
    print(f"{'=' * 60}\n")

    return 0


def save_all(workspace: Path) -> int:
    """Save all projects with changes."""
    print(f"\n{'=' * 60}")
    print("  Razorcore Save All")
    print(f"{'=' * 60}\n")

    saved = 0
    skipped = 0
    errors = 0

    for name in MANAGED_PROJECTS:
        proj_dir = workspace / name
        if not proj_dir.exists():
            continue

        # Check for changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=proj_dir,
            capture_output=True,
            text=True
        )

        if not status_result.stdout.strip():
            skipped += 1
            continue

        print(f"\n{CYAN}[{name}]{NC}")
        result = save_project(workspace, name)
        if result == 0:
            saved += 1
        else:
            errors += 1

    print(f"\n{'=' * 60}")
    print(f"  Saved: {saved}, Skipped: {skipped}, Errors: {errors}")
    print(f"{'=' * 60}\n")

    return 1 if errors > 0 else 0
