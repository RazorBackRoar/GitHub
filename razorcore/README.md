# razorcore

```text
██████╗  █████╗ ███████╗ ██████╗ ██████╗  ██████╗ ██████╗ ██████╗ ███████╗
██╔══██╗██╔══██╗╚══███╔╝██╔═══██╗██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝
██████╔╝███████║  ███╔╝ ██║   ██║██████╔╝██║     ██║   ██║██████╔╝█████╗
██╔══██╗██╔══██║ ███╔╝  ██║   ██║██╔══██╗██║     ██║   ██║██╔══██╗██╔══╝
██║  ██║██║  ██║███████╗╚██████╔╝██║  ██║╚██████╗╚██████╔╝██║  ██║███████╗
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝
```

Unified development tools and shared library for RazorBackRoar's macOS Python applications.

## Features

- **CLI Tools**: Project management commands for all repositories
- **Shared Configs**: Centralized pylintrc, pyrightconfig.json
- **Build System**: Universal DMG creation script
- **Common Modules**: Logging, threading, filesystem utilities
- **Styling**: Dark theme and custom widgets (NeonButton, StatCard)

## Installation

```bash
pip install -e .
```

## CLI Commands

```bash
razorcore list              # List all managed projects
razorcore verify            # Check project compliance
razorcore sync-configs      # Copy configs to all projects
razorcore save              # Auto-commit and push all changes
razorcore save <project>    # Save specific project
razorcore bump <project>    # Auto-bump version and release
razorcore build <project>   # Build app and create DMG
```

## Structure

```
razorcore/
├── pyproject.toml
├── universal-build.sh
└── src/razorcore/
    ├── __init__.py
    ├── config.py           # Version reading
    ├── logging.py          # Unified logging
    ├── threading.py        # BaseWorker classes
    ├── filesystem.py       # File operations
    ├── build/dmg.py        # DMG creation
    ├── cli/commands.py     # CLI implementation
    ├── configs/            # Shared configs
    └── styling/            # Themes and widgets
```

## License

MIT License - see [LICENSE](LICENSE) for details.
