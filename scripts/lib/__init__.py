"""
Shared library for InterPro MCP scripts.

This package contains common utilities extracted and simplified from repo code
to minimize dependencies and provide self-contained functionality.
"""

__version__ = "1.0.0"

# Make key functions available at package level
from .io import load_fasta, save_tsv_output, save_json_output, load_config
from .parsers import parse_interpro_tsv, generate_summary_stats
from .utils import estimate_processing_time, generate_job_id, format_timestamp
from .mock import generate_mock_interpro_tsv, create_sample_fasta_data

__all__ = [
    # I/O functions
    'load_fasta',
    'save_tsv_output',
    'save_json_output',
    'load_config',

    # Parsers
    'parse_interpro_tsv',
    'generate_summary_stats',

    # Utilities
    'estimate_processing_time',
    'generate_job_id',
    'format_timestamp',

    # Mock functions
    'generate_mock_interpro_tsv',
    'create_sample_fasta_data'
]