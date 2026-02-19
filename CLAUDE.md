# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP (Model Context Protocol) server for InterProScan protein domain and functional analysis. Built with FastMCP, it exposes 11 tools for synchronous protein analysis, async job submission, and job lifecycle management. **Mock mode is enabled by default** — all protein analysis is simulated without requiring an InterProScan installation.

## Common Commands

```bash
# Setup
bash quick_setup.sh

# Run MCP server
./env/bin/python src/server.py

# Dev mode with inspector
fastmcp dev src/server.py

# Register in Claude Code
claude mcp add bio-mcp-interpro -- $(pwd)/env/bin/python $(pwd)/src/server.py

# Tests (no pytest runner — scripts are executed directly)
./env/bin/python tests/test_mcp_server.py
./env/bin/python tests/run_integration_tests.py src/server.py

# Upstream tests (pytest)
cd repo/bio-mcp-interpro && pytest tests/

# Lint and format
ruff format src/ scripts/
ruff check src/ scripts/
```

## Architecture

### Two-Tier Server Design

- **Outer server** (`src/server.py`): Uses `fastmcp.FastMCP` with `@mcp.tool()` decorators. This is the production entry point.
- **Upstream server** (`repo/bio-mcp-interpro/src/`): Uses low-level `mcp.Server` API. Contains the real InterProScan integration, HPC tool detection, and Docker/Singularity support. Treated as a reference/subproject.

### Sync vs Submit API Pattern

- **Sync tools** (`analyze_protein_sequence`, `create_sample_data`): Import and call functions from `scripts/` directly, return results inline.
- **Submit tools** (`submit_protein_analysis`, `submit_batch_protein_analysis`, `submit_large_dataset_analysis`): Return a `job_id` immediately, run the script as a subprocess in a background `threading.Thread`.
- **Job management tools** (6 tools): Query/control jobs via `JobManager`.

### Job System (`src/jobs/`)

- `JobManager` spawns background threads that run scripts as subprocesses.
- `JobStore` persists all state to `jobs/<job_id>/` (log, output, data files) and `jobs/jobs_metadata.json`.
- Job lifecycle: `pending` → `running` → `completed` / `failed` / `cancelled`.
- Job IDs are 8-character UUID prefixes.

### Path Setup

`src/utils.py:setup_paths()` adds `src/` and `scripts/` to `sys.path` at import time, enabling bare imports like `from protein_domain_scan import run_protein_domain_scan` without package installation.

### Scripts as Dual-Use Modules

Scripts in `scripts/` are both CLI-runnable (`click` commands) and importable by `src/server.py`. The shared library at `scripts/lib/` provides IO, parsing, utilities, and mock data generation.

## Configuration

- `configs/default_config.json`: Global defaults including `mock_mode: true`, InterPro path, timeouts, database list, max concurrent jobs (5).
- Upstream server uses `BIO_MCP_*` environment variables (e.g., `BIO_MCP_INTERPRO_PATH`, `BIO_MCP_TIMEOUT`, `BIO_MCP_MAX_FILE_SIZE`).

## Key Dependencies

Core: `fastmcp`, `mcp>=1.1.0`, `pydantic>=2.0.0`, `httpx>=0.24.0`, `loguru`, `click`, `pandas`, `numpy`
Dev: `pytest`, `pytest-asyncio`, `ruff` (line-length 88, target py39)

## Notes

- The conda environment lives at `./env/` (Python 3.10). Always use `./env/bin/python` to run scripts.
- `.gitignore` excludes `env/`, `results/`, `examples/`, `jobs/`, `reports/`, `tests/`, `repo/`, so only `src/`, `scripts/`, `configs/`, and top-level files are tracked.
- `tests/test_mcp_server.py` accesses the private `mcp._tools` attribute to list tool names.
