"""
I/O functions for MCP scripts.

These are extracted and simplified from repo code to minimize dependencies.
"""

import json
from pathlib import Path
from typing import Union, List, Tuple, Dict, Any


def load_fasta(file_path: Union[str, Path]) -> List[Tuple[str, str]]:
    """
    Load FASTA file and return list of (header, sequence) tuples.

    Simplified from repo/bio-mcp-interpro/src/parsers.py
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {file_path}")

    sequences = []
    header = None
    sequence = ""

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if header is not None:
                    sequences.append((header, sequence))
                header = line
                sequence = ""
            else:
                sequence += line

        if header is not None:
            sequences.append((header, sequence))

    return sequences


def save_tsv_output(data: str, file_path: Union[str, Path]) -> None:
    """Save TSV data to file."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        f.write(data)


def save_json_output(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save JSON data to file with pretty formatting."""
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)


def load_config(config_path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON configuration file."""
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    try:
        with open(config_path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file {config_path}: {e}")


def save_execution_log(
    log_data: Dict[str, Any],
    output_dir: Union[str, Path],
    filename: str = "execution.log"
) -> Path:
    """Save execution log with timing and metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log_file = output_dir / filename

    # Convert to JSON-serializable format
    log_content = {
        "timestamp": log_data.get("timestamp"),
        "script": log_data.get("script"),
        "execution_time": log_data.get("execution_time"),
        "input_files": log_data.get("input_files", []),
        "output_files": log_data.get("output_files", []),
        "config": log_data.get("config", {}),
        "stats": log_data.get("stats", {}),
        "errors": log_data.get("errors", [])
    }

    save_json_output(log_content, log_file)
    return log_file


def validate_fasta_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate FASTA file format and return basic statistics.

    Returns:
        Dict with validation results and basic statistics
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return {
            "valid": False,
            "error": f"File not found: {file_path}",
            "stats": {}
        }

    try:
        sequences = load_fasta(file_path)

        if not sequences:
            return {
                "valid": False,
                "error": "No sequences found in file",
                "stats": {}
            }

        # Calculate statistics
        sequence_lengths = [len(seq) for _, seq in sequences]

        stats = {
            "sequence_count": len(sequences),
            "total_length": sum(sequence_lengths),
            "avg_length": sum(sequence_lengths) / len(sequence_lengths),
            "min_length": min(sequence_lengths),
            "max_length": max(sequence_lengths),
            "file_size": file_path.stat().st_size
        }

        return {
            "valid": True,
            "error": None,
            "stats": stats
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"Error reading FASTA file: {str(e)}",
            "stats": {}
        }