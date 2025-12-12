"""
Unified logging setup for macOS applications.

Provides consistent logging configuration across all RazorBackRoar applications
with support for file logging, console output, and log rotation.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QStandardPaths


class ColoredFormatter(logging.Formatter):
    """Formatter that adds colors to console output."""
    
    COLORS = {
        logging.DEBUG: "\033[36m",      # Cyan
        logging.INFO: "\033[32m",       # Green
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        message = super().format(record)
        return f"{color}{message}{self.RESET}" if color else message


def get_log_directory(app_name: str) -> Path:
    """
    Get the appropriate log directory for the application.
    
    Uses macOS standard paths:
    - ~/Library/Application Support/{app_name}/logs/
    
    Args:
        app_name: Application name for the directory.
        
    Returns:
        Path to the log directory (created if needed).
    """
    app_data = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    )
    
    # If Qt returns empty, use fallback
    if not app_data or str(app_data) == ".":
        app_data = Path.home() / "Library" / "Application Support" / app_name
    
    log_dir = app_data / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir


def setup_logging(
    app_name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    colored_console: bool = True,
    log_filename: Optional[str] = None,
    max_log_files: int = 5,
) -> logging.Logger:
    """
    Configure application logging with consistent formatting.
    
    Sets up logging with:
    - File handler (rotating by date)
    - Console handler (with optional colors)
    - Consistent timestamp format
    
    Args:
        app_name: Name of the application (used for logger name and log directory).
        level: Logging level (default: INFO).
        log_to_file: Whether to log to a file.
        log_to_console: Whether to log to console.
        colored_console: Whether to use colored output in console.
        log_filename: Custom log filename (default: {app_name}.log).
        max_log_files: Maximum number of log files to keep.
        
    Returns:
        Configured logger instance.
        
    Example:
        from razorcore import setup_logging
        logger = setup_logging("4Charm")
        logger.info("Application started")
    """
    # Create or get logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Format strings
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    console_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # File handler
    if log_to_file:
        log_dir = get_log_directory(app_name)
        filename = log_filename or f"{app_name.lower()}.log"
        log_path = log_dir / filename
        
        # Rotate old logs
        _rotate_logs(log_dir, app_name.lower(), max_log_files)
        
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(file_format, date_format))
        logger.addHandler(file_handler)
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        if colored_console and sys.stdout.isatty():
            console_handler.setFormatter(ColoredFormatter(console_format, date_format))
        else:
            console_handler.setFormatter(logging.Formatter(console_format, date_format))
        
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the given name.
    
    This is a convenience function for modules to get a namespaced logger.
    
    Args:
        name: Logger name (usually __name__).
        
    Returns:
        Logger instance.
        
    Example:
        from razorcore import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def cleanup_logs(app_name: str, keep_days: int = 7) -> int:
    """
    Remove old log files to free up space.
    
    Args:
        app_name: Application name.
        keep_days: Number of days of logs to keep.
        
    Returns:
        Number of files removed.
    """
    log_dir = get_log_directory(app_name)
    removed = 0
    now = datetime.now()
    
    for log_file in log_dir.glob("*.log*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            age_days = (now - mtime).days
            
            if age_days > keep_days:
                log_file.unlink()
                removed += 1
        except OSError:
            continue
    
    return removed


def _rotate_logs(log_dir: Path, prefix: str, max_files: int) -> None:
    """Rotate log files, keeping only the most recent ones."""
    log_files = sorted(
        log_dir.glob(f"{prefix}*.log*"),
        key=lambda p: p.stat().st_mtime if p.exists() else 0,
        reverse=True
    )
    
    # Remove excess files
    for old_file in log_files[max_files:]:
        try:
            old_file.unlink()
        except OSError:
            pass
