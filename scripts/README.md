# MCP Scripts

Clean, self-contained scripts extracted from use cases for MCP tool wrapping.

## Design Principles

1. **Minimal Dependencies**: Only essential packages imported
2. **Self-Contained**: Functions inlined where possible, no repo dependencies
3. **Configurable**: Parameters in config files, not hardcoded
4. **MCP-Ready**: Each script has a main function ready for MCP wrapping

## Scripts

| Script | Description | Independent | Config |
|--------|-------------|-------------|--------|
| `protein_domain_scan.py` | Basic protein domain and family analysis | ✅ Yes | `configs/protein_domain_scan_config.json` |
| `async_job_manager.py` | Async job submission and management | ✅ Yes | `configs/async_job_manager_config.json` |
| `mcp_client_demo.py` | MCP client communication and tool discovery | ✅ Yes | `configs/mcp_client_demo_config.json` |

## Usage

```bash
# Activate environment (using the project's conda environment)
./env/bin/python scripts/protein_domain_scan.py --help

# Basic protein domain analysis
./env/bin/python scripts/protein_domain_scan.py --create-sample --input examples/data/sample.fasta
./env/bin/python scripts/protein_domain_scan.py --input examples/data/sample.fasta --output results/domains.tsv

# Async job management
./env/bin/python scripts/async_job_manager.py --create-dataset 10
./env/bin/python scripts/async_job_manager.py --submit --input examples/data/large_dataset.fasta --priority 8
./env/bin/python scripts/async_job_manager.py --status <job_id>
./env/bin/python scripts/async_job_manager.py --result <job_id> --output results/job_results.tsv

# MCP client demonstration
./env/bin/python scripts/mcp_client_demo.py --server-type basic --analyze-tools
./env/bin/python scripts/mcp_client_demo.py --server-type queue --demo --save-results results/mcp_demo.json
```

## Shared Library

Common functions are in `scripts/lib/`:

| Module | Functions | Description |
|--------|-----------|-------------|
| `io.py` | 5 | File loading/saving, config management |
| `parsers.py` | 3 | InterProScan result parsing and analysis |
| `utils.py` | 8 | General utilities (job IDs, timing, validation) |
| `mock.py` | 4 | Mock data generation for demonstrations |

**Total Functions**: 20 inlined and simplified functions

## Configuration Files

Each script supports JSON configuration files in `configs/`:

- `protein_domain_scan_config.json` - Basic analysis settings
- `async_job_manager_config.json` - Job queue and timing settings
- `mcp_client_demo_config.json` - MCP server connection settings
- `default_config.json` - Shared default configuration

## For MCP Wrapping (Step 6)

Each script exports a main function that can be wrapped:

```python
# protein_domain_scan.py
from scripts.protein_domain_scan import run_protein_domain_scan

# In MCP tool:
@mcp.tool()
def analyze_protein_domains(input_file: str, output_file: str = None):
    return await run_protein_domain_scan(input_file, output_file)
```

```python
# async_job_manager.py
from scripts.async_job_manager import submit_job, get_job_status, get_job_result

# In MCP tools:
@mcp.tool()
def submit_interpro_job(input_file: str, priority: int = 5):
    return await submit_job(input_file, priority)

@mcp.tool()
def check_job_status(job_id: str):
    return await get_job_status(job_id)
```

```python
# mcp_client_demo.py
from scripts.mcp_client_demo import connect_to_server, analyze_tool_schemas

# In MCP tools:
@mcp.tool()
def discover_server_tools(server_type: str = "basic"):
    return await connect_to_server(server_type)
```

## Dependencies Removed

- **MCP Server Imports**: All `mcp.types`, `mcp.server` dependencies removed
- **Repo-Specific Classes**: `InterproServer`, `ServerSettings` classes inlined as mock
- **Complex Parsers**: Simplified parsing logic, removed unnecessary features
- **External Queue Systems**: Replaced with JSON-based job state persistence

## Mock Mode Features

All scripts run in mock mode by default for demonstration:

- **Realistic Results**: Generate InterProScan-like TSV output
- **Job Progression**: Simulate queue → running → completed states
- **Timing Simulation**: Realistic processing delays and timeouts
- **Data Validation**: Proper FASTA parsing and error handling

## Testing

All scripts have been tested with sample data:

```bash
# Test basic analysis
./env/bin/python scripts/protein_domain_scan.py --create-sample --input examples/data/sample.fasta
./env/bin/python scripts/protein_domain_scan.py --input examples/data/sample.fasta --output results/test.tsv
# ✅ Generates realistic TSV and JSON summary

# Test async jobs
./env/bin/python scripts/async_job_manager.py --create-dataset 5
./env/bin/python scripts/async_job_manager.py --submit --input examples/data/large_dataset.fasta --priority 8
# ✅ Job submitted with ID, tracks status progression

# Test MCP demo
./env/bin/python scripts/mcp_client_demo.py --server-type queue --demo
# ✅ Demonstrates server discovery, tool schemas, and tool execution
```

## Production Deployment

To use with real InterProScan:

1. **Install InterProScan**: Download and install InterProScan 5.59+
2. **Update Configs**: Set `mock_mode: false` in config files
3. **Set Paths**: Configure `interpro_path` in configs
4. **Add MCP Integration**: Install compatible MCP library
5. **Replace Mock Functions**: Connect to real InterProScan executable

For demonstration and development, the current mock implementations provide complete functionality without external dependencies.