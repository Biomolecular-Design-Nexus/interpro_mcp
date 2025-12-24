"""
General utilities for MCP scripts.

These are extracted and simplified from repo utility code to minimize dependencies.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Union


def generate_job_id() -> str:
    """Generate unique job identifier."""
    return f"job_{uuid.uuid4().hex[:8]}"


def format_timestamp(dt: datetime = None, format_type: str = "iso") -> str:
    """
    Format timestamp for logging and display.

    Args:
        dt: datetime object (uses current time if None)
        format_type: Format type ('iso', 'display', 'filename')

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()

    if format_type == "iso":
        return dt.isoformat()
    elif format_type == "display":
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "filename":
        return dt.strftime("%Y%m%d_%H%M%S")
    else:
        return dt.isoformat()


def estimate_processing_time(file_path: Union[str, Path]) -> int:
    """
    Estimate InterProScan processing time in minutes based on file size.

    Args:
        file_path: Path to input FASTA file

    Returns:
        Estimated processing time in minutes
    """
    try:
        file_path = Path(file_path)
        file_size_kb = file_path.stat().st_size // 1024

        # Simple estimation: 1 minute per KB for demo purposes
        # Real estimation would consider sequence count, length, etc.
        estimated_minutes = max(1, min(120, file_size_kb))  # Cap between 1-120 minutes

        return estimated_minutes

    except Exception:
        return 5  # Default 5 minutes if estimation fails


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string (e.g., "2m 30s")
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def validate_priority(priority: int) -> int:
    """
    Validate and clamp job priority to valid range.

    Args:
        priority: Input priority value

    Returns:
        Valid priority (1-10)
    """
    return max(1, min(10, priority))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Input filename

    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    sanitized = filename

    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')

    # Remove multiple consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')

    # Remove leading/trailing underscores and whitespace
    sanitized = sanitized.strip('_ ')

    return sanitized


def create_output_path(
    base_dir: Union[str, Path],
    prefix: str,
    extension: str,
    timestamp: bool = True
) -> Path:
    """
    Create standardized output file path.

    Args:
        base_dir: Base output directory
        prefix: Filename prefix
        extension: File extension (with or without dot)
        timestamp: Whether to include timestamp in filename

    Returns:
        Path object for output file
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    # Ensure extension starts with dot
    if not extension.startswith('.'):
        extension = f".{extension}"

    # Build filename
    if timestamp:
        ts = format_timestamp(format_type="filename")
        filename = f"{prefix}_{ts}{extension}"
    else:
        filename = f"{prefix}{extension}"

    # Sanitize filename
    filename = sanitize_filename(filename)

    return base_dir / filename


def merge_configs(*configs) -> dict:
    """
    Merge multiple configuration dictionaries with deep merging.

    Args:
        *configs: Configuration dictionaries to merge

    Returns:
        Merged configuration dictionary
    """
    merged = {}

    for config in configs:
        if not isinstance(config, dict):
            continue

        for key, value in config.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursive merge for nested dictionaries
                merged[key] = merge_configs(merged[key], value)
            else:
                # Override with later value
                merged[key] = value

    return merged