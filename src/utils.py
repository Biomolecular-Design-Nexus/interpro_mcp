"""Shared utilities for bio-mcp-interpro MCP server."""

from pathlib import Path
from typing import Dict, Any, Union
import sys


def setup_paths():
    """Setup Python paths to include scripts directory."""
    script_dir = Path(__file__).parent.resolve()
    mcp_root = script_dir.parent
    scripts_dir = mcp_root / "scripts"

    # Add to path if not already there
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    return {
        "script_dir": script_dir,
        "mcp_root": mcp_root,
        "scripts_dir": scripts_dir
    }


def validate_file_path(file_path: Union[str, Path]) -> Path:
    """Validate and convert file path."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    return path


def format_error_response(error: str, context: str = None) -> Dict[str, Any]:
    """Format a standardized error response."""
    response = {"status": "error", "error": error}
    if context:
        response["context"] = context
    return response


def format_success_response(result: Dict[str, Any], message: str = None) -> Dict[str, Any]:
    """Format a standardized success response."""
    response = {"status": "success", **result}
    if message:
        response["message"] = message
    return response