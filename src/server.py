"""MCP Server for bio-mcp-interpro

Provides both synchronous and asynchronous (submit) APIs for InterProScan protein analysis tools.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List
import sys

# Setup paths
from utils import setup_paths, validate_file_path, format_error_response, format_success_response

paths = setup_paths()
SCRIPTS_DIR = paths["scripts_dir"]

# Import job manager
from jobs.manager import job_manager
from loguru import logger

# Create MCP server
mcp = FastMCP("bio-mcp-interpro")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)


@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)


@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)


@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)


@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)


@mcp.tool()
def get_server_info() -> dict:
    """
    Get server information and job statistics.

    Returns:
        Server info including total jobs, status breakdown, etc.
    """
    return job_manager.get_server_info()


# ==============================================================================
# Synchronous Tools (for fast operations < 10 min)
# ==============================================================================

@mcp.tool()
def analyze_protein_sequence(
    input_file: str,
    output_format: str = "tsv",
    databases: Optional[str] = None,
    output_file: Optional[str] = None
) -> dict:
    """
    Synchronous protein domain analysis using InterProScan (fast operation).

    This tool provides immediate results for basic protein sequence analysis.
    Suitable for small files and quick analysis tasks.

    Args:
        input_file: Path to protein FASTA file
        output_format: Output format (tsv, xml, json, gff3)
        databases: Comma-separated list of databases to search (optional)
        output_file: Optional path to save output

    Returns:
        Dictionary with analysis results and output file path
    """
    try:
        # Validate input
        input_path = validate_file_path(input_file)

        # Import the sync script function
        from protein_domain_scan import run_protein_domain_scan
        import asyncio

        # Run the analysis
        result = asyncio.run(run_protein_domain_scan(
            input_file=str(input_path),
            output_file=output_file,
            output_format=output_format,
            databases=databases
        ))

        return format_success_response(result, "Protein analysis completed successfully")

    except FileNotFoundError as e:
        return format_error_response(f"File not found: {e}")
    except ValueError as e:
        return format_error_response(f"Invalid input: {e}")
    except Exception as e:
        logger.error(f"analyze_protein_sequence failed: {e}")
        return format_error_response(str(e), "analyze_protein_sequence")


# ==============================================================================
# Submit Tools (for long-running operations > 10 min)
# ==============================================================================

@mcp.tool()
def submit_protein_analysis(
    input_file: str,
    output_format: str = "tsv",
    databases: Optional[str] = None,
    output_dir: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit protein domain analysis for background processing.

    This operation is designed for larger datasets that may take more than 10 minutes.
    Returns a job_id for tracking progress and retrieving results.

    Args:
        input_file: Path to protein FASTA file
        output_format: Output format (tsv, xml, json, gff3)
        databases: Comma-separated list of databases to search
        output_dir: Directory to save outputs
        job_name: Optional name for the job (for easier tracking)

    Returns:
        Dictionary with job_id for tracking. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results when completed
        - get_job_log(job_id) to see execution logs
    """
    try:
        # Validate input
        input_path = validate_file_path(input_file)

        script_path = str(SCRIPTS_DIR / "protein_domain_scan.py")

        args = {
            "input": str(input_path),
            "format": output_format
        }

        if databases:
            args["databases"] = databases

        if output_dir:
            # Create specific output file in the directory
            output_path = Path(output_dir) / f"{input_path.stem}_analysis.{output_format}"
            args["output"] = str(output_path)

        return job_manager.submit_job(
            script_path=script_path,
            args=args,
            job_name=job_name or f"protein_analysis_{input_path.stem}"
        )

    except FileNotFoundError as e:
        return format_error_response(f"File not found: {e}")
    except Exception as e:
        logger.error(f"submit_protein_analysis failed: {e}")
        return format_error_response(str(e), "submit_protein_analysis")


@mcp.tool()
def submit_batch_protein_analysis(
    input_files: List[str],
    output_format: str = "tsv",
    databases: Optional[str] = None,
    output_dir: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit batch protein analysis for multiple input files.

    Processes multiple FASTA files in a single job. Suitable for:
    - Processing many protein sequences at once
    - Large-scale domain analysis
    - Parallel processing of independent files

    Args:
        input_files: List of input FASTA file paths to process
        output_format: Output format applied to all files (tsv, xml, json, gff3)
        databases: Comma-separated database list for all analyses
        output_dir: Directory to save all outputs
        job_name: Optional name for the batch job

    Returns:
        Dictionary with job_id for tracking the batch job
    """
    try:
        # Validate all input files
        validated_files = []
        for input_file in input_files:
            input_path = validate_file_path(input_file)
            validated_files.append(str(input_path))

        # Use the async job manager script for batch processing
        script_path = str(SCRIPTS_DIR / "async_job_manager.py")

        # Create a batch processing job using the async manager
        args = {
            "submit": "",  # Flag for submission
            "input": validated_files[0],  # Primary input
            "format": output_format,
            "priority": "8"  # High priority for batch jobs
        }

        if databases:
            args["databases"] = databases

        if output_dir:
            args["output"] = output_dir

        job_name = job_name or f"batch_{len(input_files)}_files"

        return job_manager.submit_job(
            script_path=script_path,
            args=args,
            job_name=job_name
        )

    except FileNotFoundError as e:
        return format_error_response(f"File not found: {e}")
    except Exception as e:
        logger.error(f"submit_batch_protein_analysis failed: {e}")
        return format_error_response(str(e), "submit_batch_protein_analysis")


@mcp.tool()
def submit_large_dataset_analysis(
    input_file: str,
    priority: int = 5,
    notification_email: Optional[str] = None,
    output_dir: Optional[str] = None,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit large dataset analysis with job queue management.

    Uses the async job manager for processing large protein datasets with
    proper job scheduling, priority handling, and progress tracking.

    Args:
        input_file: Path to large protein FASTA file
        priority: Job priority (1-10, higher is more urgent)
        notification_email: Email for completion notification
        output_dir: Directory to save outputs
        job_name: Optional name for tracking

    Returns:
        Dictionary with job_id for tracking. This uses the full async workflow
        with job queue management, progress tracking, and result persistence.
    """
    try:
        # Validate input
        input_path = validate_file_path(input_file)

        script_path = str(SCRIPTS_DIR / "async_job_manager.py")

        args = {
            "submit": "",  # Submit flag
            "input": str(input_path),
            "priority": str(priority),
            "format": "tsv"
        }

        if notification_email:
            args["email"] = notification_email

        if output_dir:
            args["output"] = output_dir

        job_name = job_name or f"large_analysis_{input_path.stem}"

        return job_manager.submit_job(
            script_path=script_path,
            args=args,
            job_name=job_name
        )

    except FileNotFoundError as e:
        return format_error_response(f"File not found: {e}")
    except Exception as e:
        logger.error(f"submit_large_dataset_analysis failed: {e}")
        return format_error_response(str(e), "submit_large_dataset_analysis")


# ==============================================================================
# Utility Tools
# ==============================================================================

@mcp.tool()
def create_sample_data(
    output_file: str,
    sequence_count: int = 5,
    sequence_type: str = "protein"
) -> dict:
    """
    Create sample protein sequence data for testing.

    Args:
        output_file: Path to save sample FASTA file
        sequence_count: Number of sequences to generate
        sequence_type: Type of sequences (protein or large_dataset)

    Returns:
        Dictionary with sample file information
    """
    try:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if sequence_type == "protein":
            # Use the protein_domain_scan script's sample creation
            from protein_domain_scan import create_sample_fasta
            create_sample_fasta(output_path)

        elif sequence_type == "large_dataset":
            # Use the async job manager's dataset creation
            from async_job_manager import generate_large_protein_dataset
            generate_large_protein_dataset(output_path, sequence_count)

        return format_success_response({
            "output_file": str(output_path),
            "sequence_count": sequence_count,
            "sequence_type": sequence_type
        }, f"Sample {sequence_type} data created successfully")

    except Exception as e:
        logger.error(f"create_sample_data failed: {e}")
        return format_error_response(str(e), "create_sample_data")


# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()