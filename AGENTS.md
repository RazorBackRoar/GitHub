# RazorBackRoar GitHub Workspace

This workspace contains 5 macOS Python/PySide6 applications with a shared library called `.razorcore` (hidden folder).

## Workspace Structure

```
/Users/home/GitHub/
├── AGENTS.md                    # ← You are here (AI reads this)
├── .vscode/settings.json        # VS Code workspace settings
│
├── .razorcore/                  # SHARED LIBRARY (hidden) - use this first!
│   ├── pyproject.toml
│   ├── universal-build.sh      # Build any project
│   └── src/razorcore/
│       ├── config.py           # Version reading
│       ├── logging.py          # Unified logging
│       ├── threading.py        # BaseWorker classes
│       ├── filesystem.py       # File operations
│       ├── updates.py          # GitHub update checking
│       ├── build/dmg.py        # DMG creation
│       ├── cli/commands.py     # CLI tools
│       ├── configs/            # Shared pylintrc, pyrightconfig.json
│       └── styling/            # Themes, widgets (NeonButton, etc.)
│
├── 4Charm/                      # 4chan media downloader
│   └── src/four_charm/
│
├── Nexus/                       # Safari URL automation
│   └── src/nexus/
│
├── Papyrus/                     # HTML to PDF converter
│   └── src/papyrus/
│
├── PyPixPro/                    # Photo organization
│   └── src/pypixpro/
│
└── iSort/                       # Apple device file organizer
    └── src/isort_app/
```

---

## Quick Reference

| Project | Package | Version | Description |
|---------|---------|---------|-------------|
| 4Charm | `four_charm` | 5.2.0 | 4chan media downloader |
| Nexus | `nexus` | 5.0.0 | Safari URL automation |
| Papyrus | `papyrus` | 1.2.0 | HTML to PDF converter |
| PyPixPro | `pypixpro` | 1.0.0 | Photo organization |
| iSort | `isort_app` | 10.0.0 | Apple device file organizer |
| **.razorcore** | `razorcore` | 1.0.0 | Shared library (configs, themes, build tools) |

---

## Standard Project Structure

ALL projects follow this exact structure:

```
ProjectName/
├── pyproject.toml           # Package metadata, version, dependencies
├── .pylintrc                # Linting config (from .razorcore)
├── pyrightconfig.json       # Type checking config (from .razorcore)
├── assets/
│   └── icons/
│       └── AppName.icns     # Application icon
├── build/
│   ├── dmg-config.json      # DMG window settings
│   ├── scripts/
│   │   └── build.sh         # Build script
│   └── dist/                # Build output (gitignored)
│       └── AppName.app
├── docs/
│   └── CHANGELOG.md
└── src/
    └── package_name/        # Python package (lowercase)
        ├── __init__.py
        ├── main.py          # Entry point
        ├── core/            # Business logic
        ├── gui/             # UI components
        └── utils/           # Utilities
```

---

## .razorcore - Shared Library (Hidden)

Located at `/Users/home/GitHub/.razorcore/`

### Structure
```
.razorcore/
├── pyproject.toml
├── universal-build.sh       # Build any project: ./universal-build.sh ProjectName
└── src/razorcore/
    ├── __init__.py
    ├── config.py            # Version reading from pyproject.toml
    ├── logging.py           # Unified logging setup
    ├── threading.py         # BaseWorker classes for QThread
    ├── filesystem.py        # File operations and hashing
    ├── updates.py           # GitHub Releases API update checker
    ├── build/
    │   ├── __init__.py
    │   └── dmg.py           # DMG creation utilities
    ├── cli/
    │   ├── __init__.py
    │   ├── main.py          # CLI entry point
    │   └── commands.py      # sync-configs, verify, commit-all, list
    ├── configs/
    │   ├── __init__.py
    │   ├── pylintrc         # Shared pylint config
    │   └── pyrightconfig.json
    └── styling/
        ├── __init__.py
        ├── themes.py        # Dark theme, color palettes
        └── widgets.py       # NeonButton, StatCard, etc.
```

### CLI Commands (after `pip install -e .razorcore/`)

**IMPORTANT FOR AI ASSISTANTS**: When the user asks you to perform these tasks, run these commands in the terminal.

| Command | What it does | When to use |
|---------|-------------|-------------|
| `razorcore list` | Shows all projects with versions and git status | To see project overview |
| `razorcore verify` | Checks all projects for correct structure | After making structural changes |
| `razorcore sync-configs` | Copies pylintrc/pyrightconfig to all projects | After updating shared configs |
| `razorcore save` | Auto-generates commit message, commits, pushes | **After any code changes** |
| `razorcore save <project>` | Same but for specific project | After changing one project |
| `razorcore bump <project>` | Auto-bumps version based on commits | Before releasing |
| `razorcore build <project>` | Builds app and creates DMG | To create distributable |
| `razorcore commit-all "msg"` | Commits to all projects with same message | For synchronized updates |

### CLI Command Details

```bash
# List all projects
razorcore list

# Verify project compliance
razorcore verify                    # All projects
razorcore verify iSort              # Specific project
razorcore verify --strict           # Fail on warnings

# Sync configs from razorcore to projects
razorcore sync-configs              # All projects
razorcore sync-configs 4Charm       # Specific project
razorcore sync-configs --dry-run    # Preview only

# Commit to all projects
razorcore commit-all "feat: add feature"    # All projects
razorcore commit-all "fix: bug" --push      # Commit and push

# Save (auto-generate message, commit, push) - USE THIS AFTER CHANGES
razorcore save                      # All projects with changes
razorcore save 4Charm               # Specific project

# Auto-bump version (reads commit messages)
razorcore bump 4Charm               # Analyzes commits, bumps version
razorcore bump iSort --dry-run      # Preview what would happen

# Build project
razorcore build 4Charm              # Builds and creates DMG
razorcore build iSort               # Builds and creates DMG
```

### How Version Bumping Works

The `razorcore bump` command reads commit messages since the last git tag:
- Commits starting with `feat:` → bump MINOR (1.0.0 → 1.1.0)
- Commits starting with `fix:` → bump PATCH (1.0.0 → 1.0.1)
- Commits containing `BREAKING CHANGE` → bump MAJOR (1.0.0 → 2.0.0)

It automatically:
1. Updates `pyproject.toml` with new version
2. Updates `__init__.py` if it has `__version__`
3. Creates git commit and tag
4. Pushes commits and tags to GitHub

---

## Build System

### Building a Single Project
```bash
cd /Users/home/GitHub/.razorcore
./universal-build.sh 4Charm      # Builds 4Charm
./universal-build.sh iSort       # Builds iSort
./universal-build.sh --list      # Show all projects
```

### DMG Configuration
All projects use identical DMG settings in `build/dmg-config.json`:
- **Window**: 500x320 at position (200, 200)
- **App icon position**: x=140, y=130
- **Applications folder**: x=400, y=130
- **source_app**: `./build/dist/AppName.app`
- **volume_icon**: `./assets/icons/AppName.icns`

---

## Technology Stack

- **Language**: Python 3.10+
- **GUI Framework**: PySide6 (Qt for Python)
- **Build Tools**: py2app, PyInstaller
- **Target Platform**: macOS ARM64 (Apple Silicon)
- **Styling**: Dark theme with neon accents

---

## Coding Conventions

### Imports
Use absolute imports with the package name:
```python
from isort_app.core.metadata import check_dependencies
from isort_app.gui.main_window import MainWindow
```

### Entry Point Pattern
```python
def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    setup_dark_theme(app)
    window = MainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
```

### Dark Theme Colors
- Background: `#1e1e1e` (30, 30, 30)
- Text: `#dcdcdc` (220, 220, 220)
- Accent: `#76e648` (neon green)
- Highlight: `#4a9eff` (blue)

---

## Important Rules

1. **Never use symlinks** - All config files are real files copied from .razorcore
2. **Version in pyproject.toml only** - Single source of truth for version
3. **src/ layout required** - All Python code under `src/package_name/`
4. **DMG configs in build/** - Not at project root
5. **Consistent icon positions** - App at 140, Applications at 400

---

## When Modifying Code

1. Check if the functionality exists in .razorcore first
2. Use razorcore imports when available:
   ```python
   from razorcore import BaseWorker, setup_logging, get_version
   from razorcore.styling import get_dark_stylesheet, NeonButton
   ```
3. Follow the existing patterns in similar projects
4. Keep the dark theme consistent across all apps

---

## Common Tasks

### Add a new feature to an app
1. Check if similar functionality exists in another project
2. If it's reusable, consider adding it to .razorcore first
3. Use the standard module structure: `core/` for logic, `gui/` for UI

### Update configs across all projects
```bash
cd /Users/home/GitHub
pip install -e .razorcore/      # Install razorcore CLI (one time)
razorcore sync-configs          # Copies configs to all projects
```

### Build and create DMG
```bash
cd /Users/home/GitHub/.razorcore
./universal-build.sh 4Charm     # Replace with project name
```

### Check project compliance
```bash
razorcore verify                # Checks all projects
razorcore verify iSort          # Check specific project
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Import not found | Check `src/` is in Python path; verify package name matches folder |
| DMG window wrong size | Check `build/dmg-config.json` has correct window dimensions |
| Icons not showing | Verify `assets/icons/AppName.icns` exists |
| Build fails | Run from project root, ensure virtual env has PySide6 |
| razorcore command not found | Run `pip install -e .razorcore/` first |

---

## Git Workflow

### Branches
- **main**: Stable, releasable code only
- **feature/xyz**: New features (merge to main when done)
- **fix/xyz**: Bug fixes

### Commit Message Format

Use conventional commits - this enables automatic version bumping:

```
feat: add download queue           # Bumps MINOR version
fix: resolve crash on startup      # Bumps PATCH version
chore: update dependencies         # No version bump
refactor: restructure core module  # No version bump
docs: update README                # No version bump

# For breaking changes (bumps MAJOR):
feat!: redesign API
# or include in body:
feat: new feature

BREAKING CHANGE: old API removed
```

---

## Versioning

**Format**: MAJOR.MINOR.PATCH (e.g., 5.2.0)

| Bump | When | Example |
|------|------|--------|
| PATCH | Bug fixes, minor tweaks | 1.0.0 → 1.0.1 |
| MINOR | New features, backward compatible | 1.0.0 → 1.1.0 |
| MAJOR | Breaking changes | 1.0.0 → 2.0.0 |

**Single source of truth**: `pyproject.toml`

### Release Process

1. Write commits using conventional format (`feat:`, `fix:`, etc.)
2. Run `razorcore bump <project>` - auto bumps, commits, tags, and pushes
3. Build: `razorcore build <project>`
