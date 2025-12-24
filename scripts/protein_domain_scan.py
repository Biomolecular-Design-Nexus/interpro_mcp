#!/usr/bin/env python3
"""
Script: protein_domain_scan.py
Description: Basic InterProScan functionality for protein domain and family analysis

Original Use Case: examples/use_case_1_basic_protein_scan_patched.py
Dependencies Removed: MCP server imports, repo-specific classes (inlined as mock functionality)

Usage:
    python scripts/protein_domain_scan.py --input <input_file> --output <output_file>

Example:
    python scripts/protein_domain_scan.py --input examples/data/sample.fasta --output results/domains.tsv
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

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "interpro_path": "interproscan.sh",
    "timeout": 1800,
    "output_format": "tsv",
    "include_goterms": True,
    "include_pathways": True,
    "databases": None  # None means all databases
}

# ==============================================================================
# Inlined Utility Functions (simplified from repo)
# ==============================================================================
def load_fasta(file_path: Path) -> List[tuple]:
    """Load FASTA file and return list of (header, sequence) tuples."""
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

def save_tsv_output(data: str, file_path: Path) -> None:
    """Save TSV data to file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(data)

def save_json_output(data: Dict[str, Any], file_path: Path) -> None:
    """Save JSON data to file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)

def create_sample_fasta(output_path: Path) -> None:
    """Create a sample protein FASTA file with known domains."""
    sample_sequences = [
        (">P53_HUMAN|Tumor suppressor p53|Homo sapiens",
         "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP"
         "DEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAK"
         "SVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHC"
         "SRCRNVSRRRCGQCRLRKCYEVFEFYREGEFVGNLAFYTDKCRRCENKLTKPCRCWRCGK"
         "EGHQMKDCTERQANFLGKIWPSYKGRVPLNLHGSESIGMYRERQCQGDGRCSNHGCKRMN"
         "HSWCQFCNSLGRHCPLSADHSACDCGCAHCQVCTCACGGCRQCDQHCGCHYCCAAHCTGC"
         "PCNCKACTQGFCWHSSLAHQKQKNEQHCGLGHLKRHKKHTG"),

        (">INSULIN_HUMAN|Insulin|Homo sapiens",
         "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAED"
         "LQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN")
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        for header, sequence in sample_sequences:
            f.write(f"{header}\n{sequence}\n")

# ==============================================================================
# InterPro Analysis Functions (inlined from patched use case)
# ==============================================================================
def generate_mock_tsv(sequence_count: int = 2) -> str:
    """Generate realistic mock TSV output for demonstration."""
    tsv_data = [
        "# InterProScan version 5.59-91.0",
        "# What is InterProScan? InterProScan is a sequence analysis application (nucleotide and protein sequences) that combines different protein signature recognition methods from the InterPro database.",
        "# Version 5.59-91.0",
        "# Analysis Date: 2025-12-21",
        "",
        "# Sequence\tMD5 checksum\tSequence length\tAnalysis\tSignature accession\tSignature description\tStart location\tStop location\tScore\tStatus\tDate\tInterPro accession\tInterPro description\tGO annotations\tPathways",
        "P53_HUMAN\tabc123def456\t393\tPfam\tPF00870\tP53\t1\t292\t1.2E-23\tT\t21-12-2025\tIPR011615\tP53 DNA-binding domain\tGO:0003677|DNA binding,GO:0003700|DNA-binding transcription factor activity\tREACTOME:R-HSA-69473",
        "P53_HUMAN\tabc123def456\t393\tPRINTS\tPR00659\tP53\t10\t45\t-\tT\t21-12-2025\tIPR002117\tP53 tumor suppressor\tGO:0006915|apoptotic process,GO:0030330|DNA damage response\t-",
        "P53_HUMAN\tabc123def456\t393\tProSiteProfiles\tPS50963\tP53_TETRAMER\t325\t355\t8.234\tT\t21-12-2025\tIPR010991\tP53 tetramerisation motif\tGO:0046982|protein heterodimerization activity\t-",
        "INSULIN_HUMAN\tdef789ghi012\t110\tPfam\tPF00049\tInsulin\t25\t110\t2.1E-15\tT\t21-12-2025\tIPR022353\tInsulin\tGO:0005179|hormone activity,GO:0042593|glucose homeostasis\tREACTOME:R-HSA-264876",
        "INSULIN_HUMAN\tdef789ghi012\t110\tSUPERFAMILY\tSSF57447\tInsulin-like\t30\t105\t1.5E-12\tT\t21-12-2025\tIPR022353\tInsulin\tGO:0016020|membrane\tKEGG:map04910"
    ]
    return "\n".join(tsv_data)

def parse_tsv_results(tsv_content: str) -> Dict[str, Any]:
    """Parse TSV results into structured format."""
    lines = tsv_content.strip().split('\n')
    sequences = {}
    domains = set()
    families = set()
    go_terms = set()

    for line in lines:
        if line.startswith('#') or not line.strip():
            continue

        parts = line.split('\t')
        if len(parts) < 15:
            continue

        seq_id = parts[0]
        analysis = parts[3]
        signature_acc = parts[4]
        signature_desc = parts[5]
        interpro_acc = parts[11] if len(parts) > 11 and parts[11] != '-' else None
        interpro_desc = parts[12] if len(parts) > 12 and parts[12] != '-' else None
        go_annotation = parts[13] if len(parts) > 13 and parts[13] != '-' else None

        if seq_id not in sequences:
            sequences[seq_id] = {
                'domains': set(),
                'families': set(),
                'go_terms': set()
            }

        # Classify based on analysis type
        if analysis in ['Pfam', 'SMART', 'GENE3D']:
            domains.add(signature_desc)
            sequences[seq_id]['domains'].add(signature_desc)
        elif analysis in ['PRINTS', 'PANTHER']:
            families.add(signature_desc)
            sequences[seq_id]['families'].add(signature_desc)

        # Parse GO terms
        if go_annotation and go_annotation != '-':
            go_list = go_annotation.split(',')
            for go in go_list:
                if '|' in go:
                    go_id = go.split('|')[0]
                    go_terms.add(go_id)
                    sequences[seq_id]['go_terms'].add(go_id)

    # Convert sets to lists for JSON serialization
    for seq_id in sequences:
        sequences[seq_id]['domains'] = list(sequences[seq_id]['domains'])
        sequences[seq_id]['families'] = list(sequences[seq_id]['families'])
        sequences[seq_id]['go_terms'] = list(sequences[seq_id]['go_terms'])

    return {
        'sequences': sequences,
        'domains': list(domains),
        'families': list(families),
        'go_terms': list(go_terms)
    }

async def run_interpro_analysis(input_file: Path, config: Dict[str, Any]) -> Dict[str, Any]:
    """Run InterProScan analysis (mock implementation for demonstration)."""
    print(f"🔬 Starting InterProScan analysis of {input_file}")
    print(f"📁 Output format: {config['output_format']}")

    if config.get('databases'):
        print(f"🗂️ Databases: {config['databases']}")

    # Load and validate input
    sequences = load_fasta(input_file)
    print(f"📊 Found {len(sequences)} protein sequences")

    # Simulate processing time
    print("⏳ Processing sequences...")
    await asyncio.sleep(1)  # Simulate analysis

    # Generate results
    mock_tsv = generate_mock_tsv(len(sequences))

    print("✅ Analysis complete")
    return {
        "status": "success",
        "output": mock_tsv,
        "format": config['output_format'],
        "sequence_count": len(sequences),
        "mock": True
    }

# ==============================================================================
# Core Function (main logic extracted from use case)
# ==============================================================================
async def run_protein_domain_scan(
    input_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for protein domain scanning using InterProScan.

    Args:
        input_file: Path to protein FASTA file
        output_file: Path to save output (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: Main computation result with parsed domains
            - output_file: Path to output file (if saved)
            - metadata: Execution metadata

    Example:
        >>> result = await run_protein_domain_scan("input.fasta", "output.tsv")
        >>> print(result['output_file'])
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    start_time = time.time()

    # Run InterProScan analysis
    analysis_result = await run_interpro_analysis(input_file, config)

    if analysis_result["status"] != "success":
        raise RuntimeError(f"InterProScan analysis failed: {analysis_result.get('error', 'Unknown error')}")

    # Parse results
    parsed_results = parse_tsv_results(analysis_result["output"])

    # Save output if requested
    output_paths = {}
    if output_file:
        output_file = Path(output_file)

        # Save raw TSV output
        save_tsv_output(analysis_result["output"], output_file)
        output_paths["tsv_file"] = str(output_file)

        # Save parsed JSON summary
        json_file = output_file.with_suffix('.summary.json')
        save_json_output(parsed_results, json_file)
        output_paths["json_file"] = str(json_file)

        print(f"💾 Results saved:")
        print(f"   - TSV: {output_file}")
        print(f"   - Summary: {json_file}")

    execution_time = time.time() - start_time

    # Generate summary statistics
    stats = {
        "sequences_analyzed": len(parsed_results["sequences"]),
        "domains_found": len(parsed_results["domains"]),
        "families_found": len(parsed_results["families"]),
        "go_terms_found": len(parsed_results["go_terms"]),
        "execution_time": f"{execution_time:.2f}s"
    }

    print(f"📊 Analysis Summary:")
    print(f"   - Sequences analyzed: {stats['sequences_analyzed']}")
    print(f"   - Domains found: {stats['domains_found']}")
    print(f"   - Families identified: {stats['families_found']}")
    print(f"   - GO terms: {stats['go_terms_found']}")
    print(f"   - Execution time: {stats['execution_time']}")

    return {
        "result": parsed_results,
        "output_files": output_paths,
        "stats": stats,
        "metadata": {
            "input_file": str(input_file),
            "config": config,
            "execution_time": execution_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--input', '-i', required=True, help='Input protein FASTA file path')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--format', default='tsv', choices=['tsv', 'xml', 'json', 'gff3'],
                       help='Output format (default: tsv)')
    parser.add_argument('--databases', help='Comma-separated database list')
    parser.add_argument('--interpro-path', help='Path to InterProScan executable')
    parser.add_argument('--timeout', type=int, help='Analysis timeout in seconds')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample input file')

    args = parser.parse_args()

    # Create sample data if requested
    if args.create_sample:
        input_path = Path(args.input)
        print(f"📝 Creating sample protein FASTA at {input_path}")
        create_sample_fasta(input_path)
        print(f"✅ Sample file created with 2 example protein sequences")
        return

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI args
    config_overrides = {}
    if args.format:
        config_overrides['output_format'] = args.format
    if args.databases:
        config_overrides['databases'] = args.databases
    if args.interpro_path:
        config_overrides['interpro_path'] = args.interpro_path
    if args.timeout:
        config_overrides['timeout'] = args.timeout

    # Run analysis
    async def run_analysis():
        result = await run_protein_domain_scan(
            input_file=args.input,
            output_file=args.output,
            config=config,
            **config_overrides
        )
        return result

    result = asyncio.run(run_analysis())
    print(f"✅ Analysis completed successfully!")

    if args.output:
        print(f"📁 Output files: {result['output_files']}")

    return result

if __name__ == '__main__':
    main()