#!/usr/bin/env python3
"""
Script: mcp_client_demo.py
Description: MCP client demonstration for InterPro server communication and tool discovery

Original Use Case: examples/use_case_3_mcp_client_example_patched.py
Dependencies Removed: MCP client imports, repo-specific server classes (inlined as mock functionality)

Usage:
    python scripts/mcp_client_demo.py --server-type <type> --analyze-tools
    python scripts/mcp_client_demo.py --server-type <type> --call-tool <tool_name> --args <json_args>

Example:
    python scripts/mcp_client_demo.py --server-type basic --analyze-tools
    python scripts/mcp_client_demo.py --server-type queue --call-tool interpro_run_async --args '{"input_file": "test.fasta"}'
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import asyncio
import json
import time
from pathlib import Path
from typing import Union, Optional, Dict, Any, List
from datetime import datetime

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "server_url": "stdio://interpro-mcp-server",
    "connection_timeout": 30,
    "protocol_version": "2024-11-05"
}

# ==============================================================================
# Server Tool Definitions (inlined from mock implementation)
# ==============================================================================
BASIC_SERVER_TOOLS = [
    {
        "name": "interpro_run",
        "description": "Run InterProScan analysis on protein sequences",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "string", "description": "Path to FASTA file"},
                "output_format": {"type": "string", "description": "Output format (tsv, xml, json)", "default": "tsv"},
                "databases": {"type": "string", "description": "Comma-separated databases"},
                "include_goterms": {"type": "boolean", "description": "Include GO terms", "default": True},
                "include_pathways": {"type": "boolean", "description": "Include pathway information", "default": True}
            },
            "required": ["input_file"]
        }
    },
    {
        "name": "parse_interpro_results",
        "description": "Parse InterProScan TSV output into structured format",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tsv_content": {"type": "string", "description": "Raw TSV content"},
                "include_statistics": {"type": "boolean", "description": "Include summary statistics", "default": True}
            },
            "required": ["tsv_content"]
        }
    }
]

QUEUE_SERVER_TOOLS = [
    {
        "name": "interpro_run_async",
        "description": "Submit InterProScan job to async queue",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input_file": {"type": "string", "description": "Path to FASTA file"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Job priority", "default": 5},
                "output_format": {"type": "string", "description": "Output format", "default": "tsv"},
                "notification_email": {"type": "string", "description": "Email for completion notification"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Job tags"},
                "databases": {"type": "string", "description": "Comma-separated databases"}
            },
            "required": ["input_file"]
        }
    },
    {
        "name": "get_job_status",
        "description": "Check status of submitted job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job identifier"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "get_job_result",
        "description": "Retrieve results from completed job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job identifier"},
                "output_file": {"type": "string", "description": "Optional output file path"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "cancel_job",
        "description": "Cancel a running or queued job",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job identifier"}
            },
            "required": ["job_id"]
        }
    },
    {
        "name": "list_jobs",
        "description": "List all user jobs with optional filtering",
        "inputSchema": {
            "type": "object",
            "properties": {
                "status_filter": {"type": "string", "description": "Filter by status (submitted, queued, running, completed, cancelled)"},
                "limit": {"type": "integer", "description": "Maximum number of jobs to return", "default": 100}
            }
        }
    }
]

# ==============================================================================
# Inlined Utility Functions
# ==============================================================================
def get_server_tools(server_type: str) -> List[Dict[str, Any]]:
    """Get tool definitions for specified server type."""
    if server_type == "basic":
        return BASIC_SERVER_TOOLS
    elif server_type == "queue":
        return QUEUE_SERVER_TOOLS
    else:
        raise ValueError(f"Unknown server type: {server_type}")

def save_discovery_results(data: Dict[str, Any], output_file: Path) -> None:
    """Save server discovery results to JSON file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

def validate_tool_arguments(tool_schema: Dict[str, Any], arguments: Dict[str, Any]) -> List[str]:
    """Validate tool arguments against schema and return list of errors."""
    errors = []
    properties = tool_schema.get("properties", {})
    required = tool_schema.get("required", [])

    # Check required parameters
    for param in required:
        if param not in arguments:
            errors.append(f"Missing required parameter: {param}")

    # Check parameter types (basic validation)
    for param, value in arguments.items():
        if param not in properties:
            errors.append(f"Unknown parameter: {param}")
            continue

        expected_type = properties[param].get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Parameter '{param}' should be string, got {type(value).__name__}")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"Parameter '{param}' should be integer, got {type(value).__name__}")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Parameter '{param}' should be boolean, got {type(value).__name__}")

    return errors

# ==============================================================================
# Mock Tool Execution (inlined from patched use case)
# ==============================================================================
def generate_mock_tool_response(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Generate realistic mock responses for tool calls."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if tool_name == "interpro_run":
        return {
            "status": "success",
            "output": f"""# InterProScan version 5.59-91.0 - Mock Analysis
# Analysis completed: {timestamp}
# Input: {arguments.get('input_file', 'unknown')}
#
# Sequence\tMD5 checksum\tSequence length\tAnalysis\tSignature accession\tSignature description\tStart location\tStop location\tScore\tStatus\tDate\tInterPro accession\tInterPro description\tGO annotations\tPathways
PROTEIN_1\thash1abc123\t256\tPfam\tPF00001\tTest_Domain\t15\t245\t1.2E-15\tT\t{timestamp[:10]}\tIPR001001\tTest domain\tGO:0003677|DNA binding\tREACTOME:R-HSA-12345
PROTEIN_1\thash1abc123\t256\tPRINTS\tPR00001\tTest_Family\t50\t200\t-\tT\t{timestamp[:10]}\tIPR002001\tTest family\tGO:0005515|protein binding\t-""",
            "format": arguments.get("output_format", "tsv"),
            "metadata": {
                "analysis_time": "1.2s",
                "sequences_processed": 1,
                "domains_found": 2
            }
        }

    elif tool_name == "parse_interpro_results":
        return {
            "status": "success",
            "parsed_data": {
                "sequences": {
                    "PROTEIN_1": {
                        "domains": ["Test_Domain"],
                        "families": ["Test_Family"],
                        "go_terms": ["GO:0003677", "GO:0005515"]
                    }
                },
                "summary": {
                    "total_sequences": 1,
                    "domains_found": 1,
                    "families_found": 1,
                    "go_terms_found": 2
                }
            }
        }

    elif tool_name == "interpro_run_async":
        import uuid
        job_id = f"mock_job_{uuid.uuid4().hex[:8]}"
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Job submitted successfully to queue",
            "estimated_completion": "2025-12-21 15:30:00",
            "queue_position": 3
        }

    elif tool_name == "get_job_status":
        return {
            "status": "success",
            "job_id": arguments["job_id"],
            "job_status": "completed",
            "progress": 100,
            "submitted_at": "2025-12-21 14:30:00",
            "completed_at": "2025-12-21 14:45:00",
            "execution_time": "15m 32s"
        }

    elif tool_name == "get_job_result":
        return {
            "status": "success",
            "job_id": arguments["job_id"],
            "results": "# Mock async job results\nPROTEIN_1\tresult_data_here...",
            "output_format": "tsv",
            "result_size": "2.3 MB"
        }

    elif tool_name == "cancel_job":
        return {
            "status": "success",
            "job_id": arguments["job_id"],
            "message": "Job cancelled successfully"
        }

    elif tool_name == "list_jobs":
        return {
            "status": "success",
            "jobs": [
                {
                    "job_id": "mock_job_12345",
                    "status": "completed",
                    "submitted_at": "2025-12-21 14:30:00",
                    "input_file": "example.fasta",
                    "priority": 5
                },
                {
                    "job_id": "mock_job_67890",
                    "status": "running",
                    "submitted_at": "2025-12-21 15:00:00",
                    "input_file": "large_dataset.fasta",
                    "priority": 8
                }
            ],
            "total_count": 2
        }

    else:
        return {
            "status": "error",
            "error": f"Unknown tool: {tool_name}"
        }

# ==============================================================================
# Core Functions (main logic extracted from use case)
# ==============================================================================
async def connect_to_server(
    server_type: str = "basic",
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Connect to InterPro MCP server and discover capabilities.

    Args:
        server_type: Type of server to connect to ("basic" or "queue")
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - server_info: Server metadata
            - tools: Available tools with schemas
            - connection_info: Connection details

    Example:
        >>> info = await connect_to_server("basic")
        >>> print(len(info['tools']))
    """
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    print(f"🔌 Connecting to InterPro MCP server ({server_type})")

    # Simulate connection delay
    await asyncio.sleep(1)

    # Get server tools
    tools = get_server_tools(server_type)

    # Generate server info
    server_info = {
        "name": f"InterPro MCP Server ({server_type})",
        "version": "1.0.0",
        "protocol_version": config["protocol_version"],
        "type": server_type,
        "capabilities": {
            "tools": len(tools),
            "async_jobs": server_type == "queue",
            "result_parsing": True
        }
    }

    print(f"✅ Connected to MCP server")
    print(f"📋 Server: {server_info['name']} v{server_info['version']}")
    print(f"🛠️  Available tools: {len(tools)}")

    for tool in tools:
        print(f"  • {tool['name']}: {tool['description']}")

    return {
        "server_info": server_info,
        "tools": tools,
        "connection_info": {
            "server_type": server_type,
            "connected_at": datetime.now().isoformat(),
            "protocol_version": config["protocol_version"]
        }
    }

async def analyze_tool_schemas(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze tool schemas to understand input/output requirements.

    Args:
        tools: List of tool definitions

    Returns:
        Dict containing schema analysis results
    """
    print(f"\n🔍 Analyzing Tool Schemas")

    analysis = {
        "total_tools": len(tools),
        "tools_with_schemas": len(tools),
        "schema_analysis": {}
    }

    for tool in tools:
        tool_name = tool["name"]
        schema = tool["inputSchema"]

        required_params = schema.get("required", [])
        all_params = schema.get("properties", {})

        analysis["schema_analysis"][tool_name] = {
            "required_params": len(required_params),
            "total_params": len(all_params),
            "param_details": {}
        }

        # Analyze each parameter
        for param_name, param_info in all_params.items():
            analysis["schema_analysis"][tool_name]["param_details"][param_name] = {
                "type": param_info.get("type", "unknown"),
                "required": param_name in required_params,
                "description": param_info.get("description", "No description"),
                "default": param_info.get("default", "No default")
            }

        print(f"\n  📄 {tool_name}:")
        print(f"    Description: {tool['description']}")
        print(f"    Required params: {len(required_params)}")
        print(f"    Total params: {len(all_params)}")

        for param in required_params:
            param_type = all_params.get(param, {}).get("type", "unknown")
            print(f"    • {param} ({param_type}) - Required")

    return analysis

async def call_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    tools: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Call a specific MCP tool with arguments.

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments
        tools: List of available tools (for validation)

    Returns:
        Dict containing tool execution results
    """
    # Find the tool
    tool_def = None
    for tool in tools:
        if tool["name"] == tool_name:
            tool_def = tool
            break

    if not tool_def:
        raise ValueError(f"Tool '{tool_name}' not found")

    # Validate arguments
    errors = validate_tool_arguments(tool_def["inputSchema"], arguments)
    if errors:
        raise ValueError(f"Argument validation failed: {'; '.join(errors)}")

    print(f"\n⚡ Calling tool: {tool_name}")
    print(f"📝 Arguments: {json.dumps(arguments, indent=2)}")

    # Simulate processing time
    await asyncio.sleep(1)

    # Generate mock response
    response = generate_mock_tool_response(tool_name, arguments)

    print(f"✅ Tool execution completed")
    if response["status"] == "success":
        print(f"📊 Success: Tool '{tool_name}' executed successfully")
    else:
        print(f"❌ Error: {response.get('error', 'Unknown error')}")

    return response

async def run_comprehensive_demo(
    server_type: str = "basic",
    input_file: Optional[Union[str, Path]] = None,
    save_results: Optional[Union[str, Path]] = None
) -> Dict[str, Any]:
    """
    Run a comprehensive demonstration of MCP server capabilities.

    Args:
        server_type: Type of server to demonstrate
        input_file: Optional input file for tool demonstration
        save_results: Optional path to save results

    Returns:
        Dict containing complete demonstration results
    """
    results = {
        "demonstration_start": datetime.now().isoformat(),
        "server_type": server_type,
        "steps": []
    }

    # Step 1: Connect and discover
    print("=" * 60)
    print("Step 1: Server Connection and Discovery")
    print("=" * 60)

    connection_info = await connect_to_server(server_type)
    results["steps"].append({
        "step": "connection",
        "status": "success",
        "data": connection_info
    })

    # Step 2: Schema analysis
    print("\n" + "=" * 60)
    print("Step 2: Tool Schema Analysis")
    print("=" * 60)

    schema_analysis = await analyze_tool_schemas(connection_info["tools"])
    results["steps"].append({
        "step": "schema_analysis",
        "status": "success",
        "data": schema_analysis
    })

    # Step 3: Tool demonstration
    print("\n" + "=" * 60)
    print("Step 3: Tool Demonstration")
    print("=" * 60)

    tool_results = []

    if server_type == "basic":
        # Demonstrate basic server tools
        if input_file:
            demo_args = {"input_file": str(input_file)}
        else:
            demo_args = {"input_file": "examples/data/sample.fasta"}

        tool_result = await call_tool("interpro_run", demo_args, connection_info["tools"])
        tool_results.append({"tool": "interpro_run", "result": tool_result})

    elif server_type == "queue":
        # Demonstrate async job tools
        if input_file:
            demo_args = {"input_file": str(input_file), "priority": 8}
        else:
            demo_args = {"input_file": "examples/data/sample.fasta", "priority": 5}

        # Submit job
        submit_result = await call_tool("interpro_run_async", demo_args, connection_info["tools"])
        tool_results.append({"tool": "interpro_run_async", "result": submit_result})

        # Check status
        if submit_result["status"] == "success":
            job_id = submit_result["job_id"]
            status_result = await call_tool("get_job_status", {"job_id": job_id}, connection_info["tools"])
            tool_results.append({"tool": "get_job_status", "result": status_result})

    results["steps"].append({
        "step": "tool_demonstration",
        "status": "success",
        "data": tool_results
    })

    results["demonstration_end"] = datetime.now().isoformat()

    # Save results if requested
    if save_results:
        save_path = Path(save_results)
        save_discovery_results(results, save_path)
        print(f"\n💾 Results saved to: {save_path}")

    return results

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Server configuration
    parser.add_argument('--server-type', choices=['basic', 'queue'], default='basic',
                       help='Type of MCP server to connect to')

    # Actions
    parser.add_argument('--analyze-tools', action='store_true',
                       help='Analyze server tools and schemas')
    parser.add_argument('--call-tool', help='Call specific tool by name')
    parser.add_argument('--args', help='Tool arguments as JSON string')
    parser.add_argument('--demo', action='store_true',
                       help='Run comprehensive demonstration')

    # Input/output
    parser.add_argument('--input', help='Input file for tool demonstration')
    parser.add_argument('--save-results', help='Save results to JSON file')

    args = parser.parse_args()

    async def run_commands():
        if args.demo:
            # Run comprehensive demo
            results = await run_comprehensive_demo(
                server_type=args.server_type,
                input_file=args.input,
                save_results=args.save_results
            )
            print(f"\n✅ Comprehensive demo completed!")
            print(f"📊 Demonstrated {len(results['steps'])} features")

        elif args.analyze_tools:
            # Just analyze tools
            connection_info = await connect_to_server(args.server_type)
            analysis = await analyze_tool_schemas(connection_info["tools"])

            if args.save_results:
                save_path = Path(args.save_results)
                save_discovery_results({
                    "server_info": connection_info["server_info"],
                    "tools": connection_info["tools"],
                    "schema_analysis": analysis
                }, save_path)
                print(f"\n💾 Analysis saved to: {save_path}")

        elif args.call_tool:
            # Call specific tool
            if not args.args:
                parser.error("--args required when calling tool")

            try:
                arguments = json.loads(args.args)
            except json.JSONDecodeError:
                parser.error("--args must be valid JSON")

            connection_info = await connect_to_server(args.server_type)
            result = await call_tool(args.call_tool, arguments, connection_info["tools"])

            print(f"\nTool Result:")
            print(json.dumps(result, indent=2))

        else:
            # Default: just connect and show tools
            connection_info = await connect_to_server(args.server_type)
            print(f"\n📊 Server has {len(connection_info['tools'])} tools available")

    asyncio.run(run_commands())

if __name__ == '__main__':
    main()