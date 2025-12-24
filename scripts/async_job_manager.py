#!/usr/bin/env python3
"""
Script: async_job_manager.py
Description: Async InterPro job submission and management for large datasets

Original Use Case: examples/use_case_2_async_job_submission_patched.py
Dependencies Removed: MCP server imports, repo-specific queue classes (inlined as mock functionality)

Usage:
    python scripts/async_job_manager.py --submit --input <input_file> --priority <priority>
    python scripts/async_job_manager.py --status <job_id>
    python scripts/async_job_manager.py --result <job_id>

Example:
    python scripts/async_job_manager.py --submit --input examples/data/large_dataset.fasta --priority 8
    python scripts/async_job_manager.py --status job_abc12345
    python scripts/async_job_manager.py --result job_abc12345
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
from datetime import datetime, timedelta

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "queue_url": "http://localhost:8000",
    "output_format": "tsv",
    "priority": 5,
    "include_goterms": True,
    "include_pathways": True,
    "databases": None,  # None means all databases
    "timeout": 1800
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def load_job_state(state_file: Path) -> Dict[str, Any]:
    """Load persistent job state from JSON file."""
    if not state_file.exists():
        return {"jobs": {}, "history": []}

    try:
        with open(state_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"jobs": {}, "history": []}

def save_job_state(state: Dict[str, Any], state_file: Path) -> None:
    """Save persistent job state to JSON file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)

def generate_large_protein_dataset(output_path: Path, num_sequences: int = 20) -> None:
    """Generate a large protein dataset for testing async jobs."""
    import random

    amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
    sequences = []

    for i in range(num_sequences):
        # Generate random protein sequence (100-500 amino acids)
        length = random.randint(100, 500)
        sequence = ''.join(random.choice(amino_acids) for _ in range(length))

        header = f">PROTEIN_{i+1:03d}|Generated protein {i+1}|Test organism"
        sequences.append((header, sequence))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for header, sequence in sequences:
            f.write(f"{header}\n{sequence}\n")

def estimate_processing_time(input_file: Path) -> int:
    """Estimate processing time in minutes based on file size."""
    try:
        file_size_kb = input_file.stat().st_size // 1024
        # Simple estimation: 1 minute per KB for demo purposes
        return max(1, min(60, file_size_kb))  # Cap between 1-60 minutes
    except:
        return 5  # Default 5 minutes

# ==============================================================================
# Job Management Functions (inlined from patched use case)
# ==============================================================================
def generate_job_id() -> str:
    """Generate unique job identifier."""
    return f"job_{uuid.uuid4().hex[:8]}"

def get_job_state_file() -> Path:
    """Get path to persistent job state file."""
    return Path("results/job_state.json")

def generate_mock_results(input_file: str, job_id: str) -> str:
    """Generate realistic mock TSV results for completed job."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""# InterProScan version 5.59-91.0 - Async Results
# Analysis completed via background queue
# Job ID: {job_id}
# Input: {input_file}
# Completion time: {timestamp}
#
# Sequence	MD5 checksum	Sequence length	Analysis	Signature accession	Signature description	Start location	Stop location	Score	Status	Date	InterPro accession	InterPro description	GO annotations	Pathways
PROTEIN_001	hash1abc123	256	Pfam	PF00001	Test_Domain_1	15	245	1.2E-15	T	{timestamp[:10]}	IPR001001	Test domain 1	GO:0003677|DNA binding	REACTOME:R-HSA-12345
PROTEIN_001	hash1abc123	256	PRINTS	PR00001	Test_Family_1	50	200	-	T	{timestamp[:10]}	IPR002001	Test family 1	GO:0005515|protein binding	-
PROTEIN_002	hash2def456	189	Pfam	PF00002	Test_Domain_2	20	180	3.4E-12	T	{timestamp[:10]}	IPR001002	Test domain 2	GO:0016740|transferase activity	KEGG:map00010
PROTEIN_003	hash3ghi789	342	SUPERFAMILY	SSF50001	Test_Superfamily	10	320	2.1E-18	T	{timestamp[:10]}	IPR003001	Test superfamily	GO:0003824|catalytic activity	-
"""

async def simulate_job_progression(job_info: Dict[str, Any]) -> str:
    """Simulate realistic job status progression over time."""
    submitted_time = datetime.fromisoformat(job_info["submitted_at"])
    elapsed_minutes = (datetime.now() - submitted_time).total_seconds() / 60

    # Status progression based on elapsed time
    if elapsed_minutes < 1:
        return "queued"
    elif elapsed_minutes < 3:
        return "running"
    else:
        return "completed"

def calculate_progress(job_info: Dict[str, Any]) -> int:
    """Calculate job progress percentage."""
    submitted_time = datetime.fromisoformat(job_info["submitted_at"])
    elapsed_minutes = (datetime.now() - submitted_time).total_seconds() / 60

    if job_info["status"] == "queued":
        return 0
    elif job_info["status"] == "running":
        # Progress linearly from 5% to 95% during running phase
        return min(95, max(5, int(elapsed_minutes * 30)))
    elif job_info["status"] == "completed":
        return 100
    else:
        return 0

# ==============================================================================
# Core Functions (main logic extracted from use case)
# ==============================================================================
async def submit_job(
    input_file: Union[str, Path],
    priority: int = 5,
    output_format: str = "tsv",
    databases: Optional[str] = None,
    notification_email: Optional[str] = None,
    tags: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Submit an InterProScan job to the background queue.

    Args:
        input_file: Path to protein FASTA file
        priority: Job priority (1-10, higher is more important)
        output_format: Output format (tsv, xml, json, gff3)
        databases: Comma-separated list of databases to search
        notification_email: Email for completion notification
        tags: List of tags for job organization
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - job_id: Unique job identifier
            - estimated_completion: Estimated completion time
            - status: Submission status

    Example:
        >>> result = await submit_job("input.fasta", priority=8)
        >>> print(result['job_id'])
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Validate priority
    priority = max(1, min(10, priority))

    # Generate job ID and timing
    job_id = generate_job_id()
    estimated_minutes = estimate_processing_time(input_file)
    estimated_completion = datetime.now() + timedelta(minutes=estimated_minutes)

    # Create job record
    job_info = {
        "job_id": job_id,
        "status": "submitted",
        "input_file": str(input_file),
        "output_format": output_format,
        "databases": databases,
        "priority": priority,
        "tags": tags or [],
        "notification_email": notification_email,
        "submitted_at": datetime.now().isoformat(),
        "estimated_completion": estimated_completion.isoformat(),
        "progress": 0
    }

    # Load and update job state
    state_file = get_job_state_file()
    state = load_job_state(state_file)
    state["jobs"][job_id] = job_info
    state["history"].append(job_id)
    save_job_state(state, state_file)

    print(f"🚀 Job submitted successfully!")
    print(f"📋 Job configuration:")
    print(f"  • Job ID: {job_id}")
    print(f"  • Priority: {priority}/10")
    print(f"  • Output format: {output_format}")
    print(f"  • Databases: {databases or 'all'}")
    print(f"  • Estimated time: {estimated_minutes} minutes")
    print(f"  • Estimated completion: {estimated_completion.strftime('%Y-%m-%d %H:%M:%S')}")

    return {
        "job_id": job_id,
        "estimated_completion": estimated_completion.isoformat(),
        "status": "submitted",
        "message": "Job submitted successfully to queue"
    }

async def get_job_status(job_id: str) -> Dict[str, Any]:
    """
    Get status of a submitted job.

    Args:
        job_id: Job identifier

    Returns:
        Dict containing job status information

    Example:
        >>> status = await get_job_status("job_abc12345")
        >>> print(status['job_status'])
    """
    state_file = get_job_state_file()
    state = load_job_state(state_file)

    if job_id not in state["jobs"]:
        raise ValueError(f"Job {job_id} not found")

    job_info = state["jobs"][job_id]

    # Update job status based on time progression
    current_status = await simulate_job_progression(job_info)
    job_info["status"] = current_status
    job_info["progress"] = calculate_progress(job_info)

    # Save updated state
    save_job_state(state, state_file)

    print(f"📊 Job {job_id} status: {current_status} ({job_info['progress']}%)")

    return {
        "job_id": job_id,
        "job_status": current_status,
        "progress": job_info["progress"],
        "submitted_at": job_info["submitted_at"],
        "input_file": job_info["input_file"],
        "priority": job_info["priority"],
        "estimated_completion": job_info.get("estimated_completion")
    }

async def get_job_result(job_id: str, output_file: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Get results from a completed job.

    Args:
        job_id: Job identifier
        output_file: Optional path to save results

    Returns:
        Dict containing job results

    Example:
        >>> result = await get_job_result("job_abc12345", "results.tsv")
        >>> print(result['output_file'])
    """
    # Check job status first
    status_info = await get_job_status(job_id)

    if status_info["job_status"] != "completed":
        raise ValueError(f"Job {job_id} is not completed yet (status: {status_info['job_status']})")

    state_file = get_job_state_file()
    state = load_job_state(state_file)
    job_info = state["jobs"][job_id]

    # Generate results
    results = generate_mock_results(job_info["input_file"], job_id)

    # Save results if output file specified
    output_path = None
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(results)

        print(f"💾 Results saved to: {output_path}")

    print(f"📁 Job {job_id} results ready")

    return {
        "job_id": job_id,
        "results": results,
        "output_format": job_info["output_format"],
        "output_file": str(output_path) if output_path else None,
        "metadata": {
            "submitted_at": job_info["submitted_at"],
            "completed_at": datetime.now().isoformat(),
            "input_file": job_info["input_file"]
        }
    }

async def cancel_job(job_id: str) -> Dict[str, Any]:
    """
    Cancel a submitted job.

    Args:
        job_id: Job identifier

    Returns:
        Dict containing cancellation status
    """
    state_file = get_job_state_file()
    state = load_job_state(state_file)

    if job_id not in state["jobs"]:
        raise ValueError(f"Job {job_id} not found")

    job_info = state["jobs"][job_id]

    if job_info["status"] == "completed":
        raise ValueError(f"Cannot cancel completed job {job_id}")

    job_info["status"] = "cancelled"
    job_info["cancelled_at"] = datetime.now().isoformat()

    save_job_state(state, state_file)

    print(f"🚫 Job {job_id} cancelled successfully")

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully"
    }

async def list_jobs(status_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    List all submitted jobs with optional status filter.

    Args:
        status_filter: Optional status filter (submitted, queued, running, completed, cancelled)

    Returns:
        Dict containing list of jobs
    """
    state_file = get_job_state_file()
    state = load_job_state(state_file)

    jobs = []
    for job_id, job_info in state["jobs"].items():
        # Update status before filtering
        current_status = await simulate_job_progression(job_info)
        job_info["status"] = current_status

        if status_filter and job_info["status"] != status_filter:
            continue

        jobs.append({
            "job_id": job_id,
            "status": job_info["status"],
            "submitted_at": job_info["submitted_at"],
            "input_file": job_info["input_file"],
            "priority": job_info["priority"],
            "progress": calculate_progress(job_info)
        })

    # Save updated state
    save_job_state(state, state_file)

    print(f"📋 Found {len(jobs)} jobs" + (f" with status '{status_filter}'" if status_filter else ""))

    return {
        "jobs": jobs,
        "total_count": len(jobs)
    }

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Job management actions
    parser.add_argument('--submit', action='store_true', help='Submit new job')
    parser.add_argument('--status', type=str, help='Get job status by job ID')
    parser.add_argument('--result', type=str, help='Get job result by job ID')
    parser.add_argument('--cancel', type=str, help='Cancel job by job ID')
    parser.add_argument('--list', action='store_true', help='List all jobs')

    # Job submission parameters
    parser.add_argument('--input', '-i', help='Input protein FASTA file path')
    parser.add_argument('--output', '-o', help='Output file path for results')
    parser.add_argument('--priority', type=int, default=5, help='Job priority (1-10)')
    parser.add_argument('--format', default='tsv', choices=['tsv', 'xml', 'json', 'gff3'],
                       help='Output format')
    parser.add_argument('--databases', help='Comma-separated database list')
    parser.add_argument('--email', help='Notification email')
    parser.add_argument('--tags', help='Comma-separated tags')

    # Utility functions
    parser.add_argument('--create-dataset', type=int, metavar='SIZE',
                       help='Create test dataset with specified number of sequences')
    parser.add_argument('--status-filter', choices=['submitted', 'queued', 'running', 'completed', 'cancelled'],
                       help='Filter jobs by status when listing')

    args = parser.parse_args()

    async def run_command():
        if args.create_dataset:
            # Create test dataset
            output_path = Path("examples/data/large_dataset.fasta")
            print(f"📝 Creating test dataset with {args.create_dataset} sequences")
            generate_large_protein_dataset(output_path, args.create_dataset)
            print(f"✅ Dataset created at: {output_path}")
            return

        elif args.submit:
            # Submit job
            if not args.input:
                parser.error("--input required when submitting job")

            tags = args.tags.split(',') if args.tags else None
            result = await submit_job(
                input_file=args.input,
                priority=args.priority,
                output_format=args.format,
                databases=args.databases,
                notification_email=args.email,
                tags=tags
            )
            print(f"✅ Job submitted: {result['job_id']}")

        elif args.status:
            # Get job status
            result = await get_job_status(args.status)
            print(f"Job Status: {result['job_status']}")
            print(f"Progress: {result['progress']}%")

        elif args.result:
            # Get job result
            result = await get_job_result(args.result, args.output)
            if result['output_file']:
                print(f"✅ Results saved to: {result['output_file']}")
            else:
                print("Results:")
                print(result['results'][:500] + "..." if len(result['results']) > 500 else result['results'])

        elif args.cancel:
            # Cancel job
            result = await cancel_job(args.cancel)
            print(f"✅ Job cancelled: {result['job_id']}")

        elif args.list:
            # List jobs
            result = await list_jobs(args.status_filter)
            print(f"Jobs ({result['total_count']} total):")
            for job in result['jobs']:
                print(f"  {job['job_id']}: {job['status']} ({job['progress']}%) - {job['input_file']}")

        else:
            parser.print_help()

    asyncio.run(run_command())

if __name__ == '__main__':
    main()