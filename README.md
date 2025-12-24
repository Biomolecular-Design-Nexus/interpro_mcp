# bio-mcp-interpro MCP

> MCP (Model Context Protocol) server for InterProScan protein domain and functional analysis

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Local Usage (Scripts)](#local-usage-scripts)
- [MCP Server Installation](#mcp-server-installation)
- [Using with Claude Code](#using-with-claude-code)
- [Using with Gemini CLI](#using-with-gemini-cli)
- [Available Tools](#available-tools)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Overview

The bio-mcp-interpro MCP server provides access to InterProScan protein domain and functional analysis capabilities through the Model Context Protocol. It enables both synchronous (quick) and asynchronous (long-running) protein sequence analysis, with comprehensive job management for large-scale bioinformatics workflows.

### Features
- **Protein Domain Analysis**: Comprehensive domain and family identification using InterProScan
- **Async Job Management**: Background processing for large datasets with progress tracking
- **Batch Processing**: Submit multiple protein files simultaneously
- **MCP Integration**: Full Model Context Protocol support for AI assistants
- **Mock Mode**: Demonstration functionality without requiring InterProScan installation
- **Job Persistence**: Jobs survive server restarts with full state recovery

### Directory Structure
```
./
├── README.md               # This file
├── env/                    # Conda environment
├── src/
│   ├── server.py           # MCP server (main entry point)
│   ├── utils.py            # Shared utilities
│   └── jobs/               # Job management system
├── scripts/
│   ├── protein_domain_scan.py      # Basic protein analysis
│   ├── async_job_manager.py        # Async job management
│   ├── mcp_client_demo.py          # MCP client examples
│   └── lib/                        # Shared utilities
├── examples/
│   └── data/               # Demo data
│       ├── sample.fasta            # Small test dataset
│       ├── small_dataset.fasta     # Medium test dataset
│       ├── large_dataset.fasta     # Large test dataset
│       └── config_example.yaml     # Configuration template
├── configs/                # Configuration files
│   ├── default_config.json                # Default settings
│   ├── protein_domain_scan_config.json    # Domain scan config
│   ├── async_job_manager_config.json      # Job manager config
│   └── mcp_client_demo_config.json        # MCP client config
├── jobs/                   # Job storage directory
├── tests/                  # Test suite
└── repo/                   # Original repository
```

---

## Installation

### Prerequisites
- Conda or Mamba (mamba recommended for faster installation)
- Python 3.10+
- InterProScan (optional - mock mode works without it)

### Create Environment

Please strictly follow the information in `reports/step3_environment.md` to obtain the procedure to setup the environment. An example workflow is shown below.

```bash
# Navigate to the MCP directory
cd /home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/interpro_mcp

# Create conda environment (use mamba if available)
mamba create -p ./env python=3.10 -y
# or: conda create -p ./env python=3.10 -y

# Activate environment
mamba activate ./env
# or: conda activate ./env

# Install Dependencies
pip install loguru click pandas numpy tqdm
pip install "mcp>=1.1.0" "pydantic>=2.0.0" "pydantic-settings>=2.0.0" "httpx>=0.24.0"
pip install "pytest>=7.0.0" "pytest-asyncio>=0.21.0" "ruff>=0.1.0"

# Install MCP dependencies
pip install fastmcp loguru --force-reinstall --no-cache-dir
```

---

## Local Usage (Scripts)

You can use the scripts directly without MCP for local processing.

### Available Scripts

| Script | Description | Example |
|--------|-------------|---------|
| `scripts/protein_domain_scan.py` | Basic protein domain analysis using InterProScan | See below |
| `scripts/async_job_manager.py` | Async job submission and management for large datasets | See below |
| `scripts/mcp_client_demo.py` | MCP client communication examples | See below |

### Script Examples

#### Protein Domain Scan

```bash
# Activate environment
mamba activate ./env

# Basic protein analysis
python scripts/protein_domain_scan.py \
  --input examples/data/sample.fasta \
  --output results/domains.tsv \
  --format tsv

# With custom databases
python scripts/protein_domain_scan.py \
  --input examples/data/sample.fasta \
  --output results/pfam_analysis.tsv \
  --databases "Pfam,SMART,Gene3D" \
  --format tsv

# Create sample data for testing
python scripts/protein_domain_scan.py --create-sample
```

**Parameters:**
- `--input, -i`: Input protein FASTA file (required)
- `--output, -o`: Output file path (default: results/ directory)
- `--format`: Output format - tsv, xml, json, gff3 (default: tsv)
- `--databases`: Comma-separated database list (default: all available)
- `--config, -c`: Configuration file path (optional)
- `--create-sample`: Generate sample data for testing

#### Async Job Manager

```bash
# Submit a large analysis job
python scripts/async_job_manager.py \
  --submit \
  --input examples/data/large_dataset.fasta \
  --priority 8 \
  --email user@example.com

# Check job status
python scripts/async_job_manager.py \
  --status <job_id>

# Get job results
python scripts/async_job_manager.py \
  --results <job_id>

# List all jobs
python scripts/async_job_manager.py \
  --list-jobs

# Create large test dataset
python scripts/async_job_manager.py --create-dataset 100
```

**Parameters:**
- `--submit`: Submit a new analysis job
- `--input, -i`: Input FASTA file (required for submit)
- `--priority`: Job priority 1-10, higher = more urgent (default: 5)
- `--email`: Notification email (optional)
- `--status`: Check status of specific job ID
- `--results`: Get results of completed job
- `--list-jobs`: List all submitted jobs

#### MCP Client Demo

```bash
# Test basic MCP server communication
python scripts/mcp_client_demo.py \
  --server-type basic \
  --analyze-tools

# Submit analysis via MCP protocol
python scripts/mcp_client_demo.py \
  --server-type basic \
  --input examples/data/sample.fasta

# Test async job management
python scripts/mcp_client_demo.py \
  --server-type queue \
  --input examples/data/sample.fasta \
  --save-results mcp_test_results.json
```

---

## MCP Server Installation

### Option 1: Using fastmcp (Recommended)

```bash
# Install MCP server for Claude Code
fastmcp install src/server.py --name bio-mcp-interpro
```

### Option 2: Manual Installation for Claude Code

```bash
# Add MCP server to Claude Code
claude mcp add bio-mcp-interpro -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Verify installation
claude mcp list
```

### Option 3: Configure in settings.json

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "bio-mcp-interpro": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/interpro_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/interpro_mcp/src/server.py"]
    }
  }
}
```

---

## Using with Claude Code

After installing the MCP server, you can use it directly in Claude Code.

### Quick Start

```bash
# Start Claude Code
claude
```

### Example Prompts

#### Tool Discovery
```
What tools are available from bio-mcp-interpro?
```

#### Basic Analysis
```
Use analyze_protein_sequence with input_file @examples/data/sample.fasta
```

#### With Custom Parameters
```
Run analyze_protein_sequence on @examples/data/sample.fasta with output_format "json" and databases "Pfam,SMART"
```

#### Long-Running Tasks (Submit API)
```
Submit protein analysis for @examples/data/large_dataset.fasta
Then check the job status
```

#### Batch Processing
```
Submit batch protein analysis for these files:
- @examples/data/sample.fasta
- @examples/data/small_dataset.fasta
- @examples/data/large_dataset.fasta
```

#### Job Management
```
List all jobs currently running
Get results for job ID "abc12345"
Cancel job "xyz789"
```

### Using @ References

In Claude Code, use `@` to reference files and directories:

| Reference | Description |
|-----------|-------------|
| `@examples/data/sample.fasta` | Reference a specific FASTA file |
| `@configs/default_config.json` | Reference a config file |
| `@results/` | Reference output directory |

---

## Using with Gemini CLI

### Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "bio-mcp-interpro": {
      "command": "/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/interpro_mcp/env/bin/python",
      "args": ["/home/xux/Desktop/ProteinMCP/ProteinMCP/tool-mcps/interpro_mcp/src/server.py"]
    }
  }
}
```

### Example Prompts

```bash
# Start Gemini CLI
gemini

# Example prompts (same as Claude Code)
> What tools are available?
> Use analyze_protein_sequence with file examples/data/sample.fasta
> Submit batch analysis for multiple protein files
```

---

## Available Tools

### Quick Operations (Sync API)

These tools return results immediately (< 10 minutes):

| Tool | Description | Parameters |
|------|-------------|------------|
| `analyze_protein_sequence` | Basic protein domain analysis | `input_file`, `output_format`, `databases`, `output_file` |
| `create_sample_data` | Generate test protein sequences | `output_file`, `sequence_count`, `sequence_type` |

### Long-Running Tasks (Submit API)

These tools return a job_id for tracking (> 10 minutes):

| Tool | Description | Parameters |
|------|-------------|------------|
| `submit_protein_analysis` | Submit domain analysis job | `input_file`, `output_format`, `databases`, `output_dir`, `job_name` |
| `submit_batch_protein_analysis` | Submit batch analysis | `input_files`, `output_format`, `databases`, `output_dir`, `job_name` |
| `submit_large_dataset_analysis` | Submit large dataset with job queue | `input_file`, `priority`, `notification_email`, `output_dir`, `job_name` |

### Job Management Tools

| Tool | Description |
|------|-------------|
| `get_job_status` | Check job progress |
| `get_job_result` | Get results when completed |
| `get_job_log` | View execution logs |
| `cancel_job` | Cancel running job |
| `list_jobs` | List all jobs |
| `get_server_info` | Get server statistics |

---

## Examples

### Example 1: Basic Protein Analysis

**Goal:** Analyze a small protein dataset for domain identification

**Using Script:**
```bash
python scripts/protein_domain_scan.py \
  --input examples/data/sample.fasta \
  --output results/example1/ \
  --format tsv
```

**Using MCP (in Claude Code):**
```
Use analyze_protein_sequence to process @examples/data/sample.fasta and save results with output_format "tsv"
```

**Expected Output:**
- Domain and family annotations
- GO term assignments
- Structured JSON summary with parsed results
- Raw InterProScan TSV output

### Example 2: Large Dataset Processing

**Goal:** Submit a large protein dataset for background processing

**Using Script:**
```bash
python scripts/async_job_manager.py \
  --submit \
  --input examples/data/large_dataset.fasta \
  --priority 8 \
  --email researcher@university.edu
```

**Using MCP (in Claude Code):**
```
Submit large dataset analysis for @examples/data/large_dataset.fasta with priority 8 and notification_email "researcher@university.edu"
```

**Expected Output:**
- Job ID for tracking progress
- Background processing with status updates
- Email notification when complete
- Comprehensive results with all domains/families identified

### Example 3: Batch Processing

**Goal:** Process multiple files at once

**Using Script:**
```bash
for f in examples/data/*.fasta; do
  python scripts/async_job_manager.py \
    --submit \
    --input "$f" \
    --priority 5
done
```

**Using MCP (in Claude Code):**
```
Submit batch processing for these files:
- @examples/data/sample.fasta
- @examples/data/small_dataset.fasta
- @examples/data/large_dataset.fasta
```

**Expected Output:**
- Single batch job with multiple input files
- Combined progress tracking
- Unified results structure for all inputs

---

## Demo Data

The `examples/data/` directory contains sample data for testing:

| File | Description | Use With |
|------|-------------|----------|
| `sample.fasta` | 4 protein sequences with known domains | `analyze_protein_sequence`, basic testing |
| `small_dataset.fasta` | 3 real protein sequences from UniProt | Medium-scale testing |
| `large_dataset.fasta` | 50+ synthetic protein sequences | `submit_large_dataset_analysis` |
| `config_example.yaml` | Server configuration template | Script configuration |

---

## Configuration Files

The `configs/` directory contains configuration templates:

| Config | Description | Parameters |
|--------|-------------|------------|
| `default_config.json` | Default server settings | InterPro path, timeouts, output formats |
| `protein_domain_scan_config.json` | Domain scan specific config | Database selection, analysis parameters |
| `async_job_manager_config.json` | Job management config | Queue settings, priority handling |
| `mcp_client_demo_config.json` | MCP client settings | Server endpoints, connection params |

### Config Example

```json
{
  "interpro_path": "interproscan.sh",
  "default_databases": ["Pfam", "SMART", "Gene3D", "SUPERFAMILY"],
  "timeout_seconds": 3600,
  "output_formats": ["tsv", "xml", "json", "gff3"],
  "max_concurrent_jobs": 4,
  "job_priority_levels": 10
}
```

---

## Troubleshooting

### Environment Issues

**Problem:** Environment not found
```bash
# Recreate environment
mamba create -p ./env python=3.10 -y
mamba activate ./env
pip install loguru click pandas numpy tqdm
pip install "mcp>=1.1.0" "pydantic>=2.0.0" "httpx>=0.24.0"
pip install fastmcp --force-reinstall --no-cache-dir
```

**Problem:** Import errors
```bash
# Verify installation
python -c "from src.server import mcp; print('✓ MCP server imported successfully')"
```

**Problem:** MCP compatibility issues
```bash
# Check MCP version compatibility
python -c "import mcp; print('MCP available')"
# Note: Repository uses mock implementation due to MCP version differences
```

### MCP Issues

**Problem:** Server not found in Claude Code
```bash
# Check MCP registration
claude mcp list

# Re-add if needed
claude mcp remove bio-mcp-interpro
claude mcp add bio-mcp-interpro -- $(pwd)/env/bin/python $(pwd)/src/server.py
```

**Problem:** Tools not working
```bash
# Test server directly
python src/server.py --help
# Check if server starts without errors
```

**Problem:** FastMCP installation issues
```bash
# Reinstall FastMCP
pip uninstall fastmcp -y
pip install fastmcp --force-reinstall --no-cache-dir
```

### Job Issues

**Problem:** Job stuck in pending
```bash
# Check job directory
ls -la jobs/

# View job metadata
cat jobs/jobs_metadata.json
```

**Problem:** Job failed
```
Use get_job_log with job_id "<job_id>" and tail 100 to see error details
```

**Problem:** InterProScan not found
- The system operates in mock mode by default
- Install InterProScan separately for real protein analysis
- Mock mode demonstrates all functionality without requiring InterProScan

### Performance Issues

**Problem:** Slow job processing
```bash
# Check system resources
top -p $(pgrep -f "python.*server.py")

# Review job logs for bottlenecks
tail -f jobs/<job_id>/job.log
```

**Problem:** Memory issues with large datasets
- Consider splitting large FASTA files into smaller chunks
- Use batch processing tools for multiple files
- Monitor memory usage during job execution

---

## Development

### Running Tests

```bash
# Activate environment
mamba activate ./env

# Run integration tests
python tests/run_integration_tests.py

# Run MCP server tests
python tests/test_mcp_server.py
```

### Starting Dev Server

```bash
# Run MCP server in development mode
python src/server.py

# Or using fastmcp
fastmcp dev src/server.py
```

### Code Quality

```bash
# Format code
ruff format src/ scripts/

# Lint code
ruff check src/ scripts/
```

---

## License

This project builds upon the bio-mcp-interpro repository and follows the same licensing terms.

## Credits

Based on [bio-mcp-interpro](https://github.com/username/bio-mcp-interpro) repository. Enhanced with comprehensive MCP integration, job management, and batch processing capabilities.

## Support

For issues and support:
1. Check the troubleshooting section above
2. Review job logs in the `jobs/` directory
3. Test with demo data first
4. Verify environment setup matches requirements

## Version Information

- **MCP Server Version**: 1.0.0
- **FastMCP Version**: 2.14.1
- **Python Version**: 3.10.19
- **Created**: 2025-12-21