"""
Mock data generation functions.

These provide realistic test data and responses for demonstration purposes.
"""

import random
from datetime import datetime
from typing import List, Tuple, Dict, Any
from pathlib import Path


# Sample protein data for generating mock results
SAMPLE_PROTEINS = [
    {
        "id": "P53_HUMAN",
        "description": "Tumor suppressor p53|Homo sapiens",
        "sequence": "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP"
                   "DEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAK"
                   "SVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHC"
                   "SRCRNVSRRRCGQCRLRKCYEVFEFYREGEFVGNLAFYTDKCRRCENKLTKPCRCWRCGK"
                   "EGHQMKDCTERQANFLGKIWPSYKGRVPLNLHGSESIGMYRERQCQGDGRCSNHGCKRMN"
                   "HSWCQFCNSLGRHCPLSADHSACDCGCAHCQVCTCACGGCRQCDQHCGCHYCCAAHCTGC"
                   "PCNCKACTQGFCWHSSLAHQKQKNEQHCGLGHLKRHKKHTG",
        "domains": [
            {"name": "P53", "analysis": "Pfam", "acc": "PF00870", "start": 1, "stop": 292, "score": "1.2E-23"},
            {"name": "P53_TETRAMER", "analysis": "ProSiteProfiles", "acc": "PS50963", "start": 325, "stop": 355, "score": "8.234"}
        ],
        "families": [
            {"name": "P53", "analysis": "PRINTS", "acc": "PR00659", "start": 10, "stop": 45, "score": "-"}
        ],
        "go_terms": ["GO:0003677|DNA binding", "GO:0003700|DNA-binding transcription factor activity", "GO:0006915|apoptotic process"],
        "pathways": ["REACTOME:R-HSA-69473"]
    },
    {
        "id": "INSULIN_HUMAN",
        "description": "Insulin|Homo sapiens",
        "sequence": "MALWMRLLPLLALLALWGPDPAAAFVNQHLCGSHLVEALYLVCGERGFFYTPKTRREAED"
                   "LQVGQVELGGGPGAGSLQPLALEGSLQKRGIVEQCCTSICSLYQLENYCN",
        "domains": [
            {"name": "Insulin", "analysis": "Pfam", "acc": "PF00049", "start": 25, "stop": 110, "score": "2.1E-15"},
            {"name": "Insulin-like", "analysis": "SUPERFAMILY", "acc": "SSF57447", "start": 30, "stop": 105, "score": "1.5E-12"}
        ],
        "families": [],
        "go_terms": ["GO:0005179|hormone activity", "GO:0042593|glucose homeostasis", "GO:0016020|membrane"],
        "pathways": ["REACTOME:R-HSA-264876", "KEGG:map04910"]
    },
    {
        "id": "LYSOZYME_HUMAN",
        "description": "Lysozyme C|Homo sapiens",
        "sequence": "KVFGRCELAAAMKRHGLDNYRGYSLGNWVCAAKFESNFNTQATNRNTDGSTDYGILQINS"
                   "RWWCNDGRTPGSRNLCNIPCSALLSSDITASVNCAKKIVSDGNGMNAWVAWRNRCKGTDV"
                   "QAWIRGCRL",
        "domains": [
            {"name": "Lysozyme", "analysis": "Pfam", "acc": "PF00062", "start": 5, "stop": 142, "score": "1.5E-42"}
        ],
        "families": [],
        "go_terms": ["GO:0003796|lysozyme activity", "GO:0009253|peptidoglycan catabolic process"],
        "pathways": []
    }
]


def create_sample_fasta_data(
    num_proteins: int = 2,
    include_custom: bool = True
) -> List[Tuple[str, str]]:
    """
    Create sample FASTA data for testing.

    Args:
        num_proteins: Number of proteins to include
        include_custom: Whether to include predefined sample proteins

    Returns:
        List of (header, sequence) tuples
    """
    sequences = []

    if include_custom and num_proteins > 0:
        # Include sample proteins first
        for i, protein in enumerate(SAMPLE_PROTEINS[:num_proteins]):
            header = f">{protein['id']}|{protein['description']}"
            sequences.append((header, protein['sequence']))

    # Generate additional random proteins if needed
    if num_proteins > len(SAMPLE_PROTEINS):
        amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
        remaining = num_proteins - len(SAMPLE_PROTEINS)

        for i in range(remaining):
            protein_id = f"PROTEIN_{len(SAMPLE_PROTEINS) + i + 1:03d}"
            # Generate random sequence (100-400 amino acids)
            length = random.randint(100, 400)
            sequence = ''.join(random.choice(amino_acids) for _ in range(length))

            header = f">{protein_id}|Generated protein {i+1}|Test organism"
            sequences.append((header, sequence))

    return sequences


def generate_mock_interpro_tsv(
    num_sequences: int = 2,
    timestamp: str = None
) -> str:
    """
    Generate realistic mock InterProScan TSV output.

    Args:
        num_sequences: Number of sequences to include
        timestamp: Timestamp for analysis date (uses current if None)

    Returns:
        Mock TSV content string
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d")

    # TSV header
    lines = [
        "# InterProScan version 5.59-91.0",
        "# What is InterProScan? InterProScan is a sequence analysis application (nucleotide and protein sequences) that combines different protein signature recognition methods from the InterPro database.",
        "# Version 5.59-91.0",
        f"# Analysis Date: {timestamp}",
        "",
        "# Sequence\tMD5 checksum\tSequence length\tAnalysis\tSignature accession\tSignature description\tStart location\tStop location\tScore\tStatus\tDate\tInterPro accession\tInterPro description\tGO annotations\tPathways"
    ]

    # Generate data for each sequence
    for i in range(min(num_sequences, len(SAMPLE_PROTEINS))):
        protein = SAMPLE_PROTEINS[i]
        seq_id = protein["id"]
        md5_hash = f"hash{i+1}{'abc123' if i == 0 else 'def456' if i == 1 else 'ghi789'}"
        seq_length = len(protein["sequence"])

        # Add domain annotations
        for domain in protein["domains"]:
            interpro_acc = f"IPR{random.randint(100000, 999999)}"
            interpro_desc = f"{domain['name']} domain"
            go_terms = ",".join(protein["go_terms"][:2])  # Limit GO terms per line
            pathways = ",".join(protein["pathways"][:1]) if protein["pathways"] else "-"

            line = "\t".join([
                seq_id,
                md5_hash,
                str(seq_length),
                domain["analysis"],
                domain["acc"],
                domain["name"],
                str(domain["start"]),
                str(domain["stop"]),
                domain["score"],
                "T",
                timestamp,
                interpro_acc,
                interpro_desc,
                go_terms,
                pathways
            ])
            lines.append(line)

        # Add family annotations
        for family in protein["families"]:
            interpro_acc = f"IPR{random.randint(100000, 999999)}"
            interpro_desc = f"{family['name']} family"
            go_terms = ",".join(protein["go_terms"][2:]) if len(protein["go_terms"]) > 2 else "-"

            line = "\t".join([
                seq_id,
                md5_hash,
                str(seq_length),
                family["analysis"],
                family["acc"],
                family["name"],
                str(family["start"]),
                str(family["stop"]),
                family["score"],
                "T",
                timestamp,
                interpro_acc,
                interpro_desc,
                go_terms,
                "-"
            ])
            lines.append(line)

    # Add random proteins if needed
    if num_sequences > len(SAMPLE_PROTEINS):
        remaining = num_sequences - len(SAMPLE_PROTEINS)
        for i in range(remaining):
            seq_id = f"PROTEIN_{len(SAMPLE_PROTEINS) + i + 1:03d}"
            md5_hash = f"hash{len(SAMPLE_PROTEINS) + i + 1}xyz"
            seq_length = random.randint(100, 400)

            # Random domain
            domain_types = ["Pfam", "SMART", "GENE3D"]
            domain_type = random.choice(domain_types)
            domain_acc = f"PF{random.randint(10000, 99999)}"
            domain_name = f"Random_Domain_{i+1}"
            start_pos = random.randint(1, 50)
            stop_pos = start_pos + random.randint(100, 200)
            score = f"{random.uniform(1e-15, 1e-5):.1E}"

            line = "\t".join([
                seq_id, md5_hash, str(seq_length), domain_type, domain_acc, domain_name,
                str(start_pos), str(stop_pos), score, "T", timestamp,
                f"IPR{random.randint(100000, 999999)}", f"{domain_name} domain",
                "GO:0003824|catalytic activity", "-"
            ])
            lines.append(line)

    return "\n".join(lines)


def generate_mock_job_data() -> Dict[str, Any]:
    """Generate mock job data for async job demonstrations."""
    import uuid

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now()

    return {
        "job_id": job_id,
        "status": random.choice(["queued", "running", "completed"]),
        "submitted_at": timestamp.isoformat(),
        "input_file": random.choice(["sample.fasta", "large_dataset.fasta", "test_proteins.fasta"]),
        "priority": random.randint(1, 10),
        "estimated_minutes": random.randint(5, 60),
        "progress": random.randint(0, 100)
    }


def generate_mock_server_info(server_type: str = "basic") -> Dict[str, Any]:
    """Generate mock MCP server information."""
    if server_type == "basic":
        capabilities = {
            "tools": 2,
            "async_jobs": False,
            "result_parsing": True,
            "batch_processing": False
        }
    else:  # queue
        capabilities = {
            "tools": 5,
            "async_jobs": True,
            "result_parsing": True,
            "batch_processing": True,
            "job_management": True
        }

    return {
        "name": f"InterPro MCP Server ({server_type})",
        "version": "1.0.0",
        "protocol_version": "2024-11-05",
        "type": server_type,
        "capabilities": capabilities,
        "connected_at": datetime.now().isoformat()
    }