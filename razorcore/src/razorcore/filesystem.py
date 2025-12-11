"""
Safe file operations and hashing utilities.

Provides:
- Filename sanitization for cross-platform safety
- Unique filename generation for collision avoidance
- File hashing (BLAKE3, xxhash, or fallback to hashlib)
- Disk space checking
- File size formatting
"""

import hashlib
import os
import re
import shutil
from pathlib import Path
from typing import Optional, Set, Tuple, Union

# Try to import fast hashers, fall back to hashlib
try:
    import blake3
    HAS_BLAKE3 = True
except ImportError:
    HAS_BLAKE3 = False

try:
    import xxhash
    HAS_XXHASH = True
except ImportError:
    HAS_XXHASH = False


# Reserved filenames on Windows (also good practice to avoid on macOS)
RESERVED_NAMES: Set[str] = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

# Characters to replace in filenames
UNSAFE_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

# System files to exclude from processing
EXCLUDE_FILES: Set[str] = {".ds_store", "thumbs.db", "desktop.ini", ".localized"}


def sanitize_filename(
    filename: str,
    max_length: int = 200,
    replacement: str = "_"
) -> str:
    """
    Sanitize a filename for safe filesystem use.
    
    Handles:
    - Illegal characters
    - Reserved names (Windows)
    - Leading/trailing spaces and dots
    - Maximum length
    
    Args:
        filename: The original filename.
        max_length: Maximum allowed length.
        replacement: Character to replace unsafe chars with.
        
    Returns:
        Safe filename string.
        
    Example:
        >>> sanitize_filename('my:file?.txt')
        'my_file_.txt'
    """
    if not filename:
        return "unnamed_file"
    
    # Replace unsafe characters
    sanitized = UNSAFE_CHARS_PATTERN.sub(replacement, filename)
    
    # Collapse multiple spaces/underscores
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    sanitized = re.sub(r'_+', '_', sanitized)
    
    # Handle reserved names
    name_part = sanitized.split('.')[0].upper()
    if name_part in RESERVED_NAMES:
        sanitized = f"_{sanitized}"
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Enforce max length
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_len = max_length - len(ext)
        sanitized = name[:max_name_len] + ext
    
    return sanitized or "unnamed_file"


def generate_unique_filename(
    filename: str,
    directory: Union[str, Path],
    separator: str = "_"
) -> str:
    """
    Generate a unique filename by appending a counter if collision exists.
    
    Args:
        filename: Desired filename.
        directory: Directory to check for collisions.
        separator: Separator before the counter.
        
    Returns:
        Unique filename (may be same as input if no collision).
        
    Example:
        >>> generate_unique_filename("photo.jpg", "/path/to/dir")
        'photo_1.jpg'  # if photo.jpg already exists
    """
    directory = Path(directory)
    
    if not (directory / filename).exists():
        return filename
    
    # Split name and extension
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        ext = "." + ext
    else:
        name = filename
        ext = ""
    
    counter = 1
    while True:
        new_filename = f"{name}{separator}{counter}{ext}"
        if not (directory / new_filename).exists():
            return new_filename
        counter += 1


def compute_file_hash(
    filepath: Union[str, Path],
    algorithm: str = "auto",
    chunk_size: int = 65536
) -> str:
    """
    Compute hash of a file.
    
    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm ("blake3", "xxhash", "sha256", or "auto").
                   "auto" uses the fastest available.
        chunk_size: Size of chunks to read.
        
    Returns:
        Hexadecimal hash string, or empty string on error.
        
    Example:
        >>> compute_file_hash("/path/to/file.jpg")
        'a1b2c3d4...'
    """
    filepath = Path(filepath)
    
    if not filepath.exists() or not filepath.is_file():
        return ""
    
    # Select algorithm
    if algorithm == "auto":
        if HAS_BLAKE3:
            algorithm = "blake3"
        elif HAS_XXHASH:
            algorithm = "xxhash"
        else:
            algorithm = "sha256"
    
    try:
        if algorithm == "blake3" and HAS_BLAKE3:
            hasher = blake3.blake3()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        
        elif algorithm == "xxhash" and HAS_XXHASH:
            hasher = xxhash.xxh3_64()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        
        else:
            # Fallback to hashlib
            hasher = hashlib.sha256()
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(chunk_size), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
    
    except (OSError, IOError):
        return ""


def check_disk_space(
    path: Union[str, Path],
    required_mb: float = 100.0
) -> Tuple[bool, float]:
    """
    Check available disk space.
    
    Args:
        path: Path to check (uses the filesystem containing this path).
        required_mb: Minimum required space in MB.
        
    Returns:
        Tuple of (is_sufficient, available_mb).
        
    Example:
        >>> is_ok, available = check_disk_space("/Users/me", required_mb=500)
        >>> if not is_ok:
        ...     print(f"Only {available:.1f} MB available!")
    """
    try:
        usage = shutil.disk_usage(path)
        available_mb = usage.free / (1024 * 1024)
        is_sufficient = available_mb >= required_mb
        return is_sufficient, available_mb
    except OSError:
        return False, 0.0


def format_file_size(bytes_size: int) -> str:
    """
    Convert bytes to human-readable format.
    
    Args:
        bytes_size: Size in bytes.
        
    Returns:
        Human-readable string (e.g., "1.5 MB").
        
    Example:
        >>> format_file_size(1536000)
        '1.5 MB'
    """
    if bytes_size < 0:
        return "0 B"
    
    if bytes_size >= 1073741824:  # 1 GB
        return f"{bytes_size / 1073741824:.1f} GB"
    elif bytes_size >= 1048576:  # 1 MB
        return f"{bytes_size / 1048576:.1f} MB"
    elif bytes_size >= 1024:  # 1 KB
        return f"{bytes_size / 1024:.1f} KB"
    else:
        return f"{bytes_size} B"


def is_excluded_file(filename: str) -> bool:
    """
    Check if a file should be excluded from processing.
    
    Args:
        filename: Filename to check.
        
    Returns:
        True if file should be excluded.
    """
    name_lower = filename.lower()
    return (
        name_lower in EXCLUDE_FILES
        or name_lower.startswith(".")
        or name_lower.startswith("icon")
    )


def get_file_extension(filepath: Union[str, Path]) -> str:
    """
    Get lowercase file extension without dot.
    
    Args:
        filepath: Path to file.
        
    Returns:
        Extension (e.g., "jpg") or empty string.
    """
    filename = os.path.basename(str(filepath))
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def safe_move(
    source: Union[str, Path],
    destination: Union[str, Path],
    create_dirs: bool = True
) -> bool:
    """
    Safely move a file with error handling.
    
    Args:
        source: Source file path.
        destination: Destination file path.
        create_dirs: Whether to create destination directories.
        
    Returns:
        True if successful, False otherwise.
    """
    source = Path(source)
    destination = Path(destination)
    
    if not source.exists():
        return False
    
    try:
        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.move(str(source), str(destination))
        return destination.exists()
    except (OSError, shutil.Error):
        return False


def safe_copy(
    source: Union[str, Path],
    destination: Union[str, Path],
    create_dirs: bool = True
) -> bool:
    """
    Safely copy a file with error handling.
    
    Args:
        source: Source file path.
        destination: Destination file path.
        create_dirs: Whether to create destination directories.
        
    Returns:
        True if successful, False otherwise.
    """
    source = Path(source)
    destination = Path(destination)
    
    if not source.exists():
        return False
    
    try:
        if create_dirs:
            destination.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(str(source), str(destination))
        return destination.exists()
    except (OSError, shutil.Error):
        return False
