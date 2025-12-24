"""
InterProScan result parsers.

These are extracted and simplified from repo parsing code to minimize dependencies.
"""

from typing import Dict, Any, List, Set


def parse_interpro_tsv(tsv_content: str) -> Dict[str, Any]:
    """
    Parse InterProScan TSV results into structured format.

    Simplified from repo/bio-mcp-interpro/src/parsers.py

    Args:
        tsv_content: Raw TSV content from InterProScan

    Returns:
        Dict with parsed sequences, domains, families, and GO terms
    """
    lines = tsv_content.strip().split('\n')
    sequences = {}
    domains = set()
    families = set()
    go_terms = set()
    pathways = set()

    for line in lines:
        if line.startswith('#') or not line.strip():
            continue

        parts = line.split('\t')
        if len(parts) < 15:
            continue

        # Extract fields
        seq_id = parts[0]
        md5 = parts[1]
        seq_length = parts[2]
        analysis = parts[3]
        signature_acc = parts[4]
        signature_desc = parts[5]
        start_loc = parts[6]
        stop_loc = parts[7]
        score = parts[8]
        status = parts[9]
        date = parts[10]
        interpro_acc = parts[11] if len(parts) > 11 and parts[11] != '-' else None
        interpro_desc = parts[12] if len(parts) > 12 and parts[12] != '-' else None
        go_annotation = parts[13] if len(parts) > 13 and parts[13] != '-' else None
        pathway_annotation = parts[14] if len(parts) > 14 and parts[14] != '-' else None

        # Initialize sequence record
        if seq_id not in sequences:
            sequences[seq_id] = {
                'md5': md5,
                'length': seq_length,
                'domains': set(),
                'families': set(),
                'go_terms': set(),
                'pathways': set(),
                'annotations': []
            }

        # Add annotation record
        annotation = {
            'analysis': analysis,
            'signature_acc': signature_acc,
            'signature_desc': signature_desc,
            'start': start_loc,
            'stop': stop_loc,
            'score': score,
            'interpro_acc': interpro_acc,
            'interpro_desc': interpro_desc
        }
        sequences[seq_id]['annotations'].append(annotation)

        # Classify domains vs families based on analysis type
        if analysis in ['Pfam', 'SMART', 'GENE3D', 'SUPERFAMILY']:
            domains.add(signature_desc)
            sequences[seq_id]['domains'].add(signature_desc)
        elif analysis in ['PRINTS', 'PANTHER', 'ProSiteProfiles']:
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

        # Parse pathways
        if pathway_annotation and pathway_annotation != '-':
            pathways.add(pathway_annotation)
            sequences[seq_id]['pathways'].add(pathway_annotation)

    # Convert sets to lists for JSON serialization
    for seq_id in sequences:
        sequences[seq_id]['domains'] = list(sequences[seq_id]['domains'])
        sequences[seq_id]['families'] = list(sequences[seq_id]['families'])
        sequences[seq_id]['go_terms'] = list(sequences[seq_id]['go_terms'])
        sequences[seq_id]['pathways'] = list(sequences[seq_id]['pathways'])

    return {
        'sequences': sequences,
        'domains': list(domains),
        'families': list(families),
        'go_terms': list(go_terms),
        'pathways': list(pathways)
    }


def generate_summary_stats(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate summary statistics from parsed InterProScan results.

    Args:
        parsed_data: Result from parse_interpro_tsv()

    Returns:
        Dict with summary statistics
    """
    sequences = parsed_data.get('sequences', {})

    if not sequences:
        return {
            'total_sequences': 0,
            'domains_found': 0,
            'families_found': 0,
            'go_terms_found': 0,
            'pathways_found': 0,
            'sequences_with_annotations': 0,
            'avg_annotations_per_sequence': 0
        }

    # Basic counts
    total_sequences = len(sequences)
    domains_found = len(parsed_data.get('domains', []))
    families_found = len(parsed_data.get('families', []))
    go_terms_found = len(parsed_data.get('go_terms', []))
    pathways_found = len(parsed_data.get('pathways', []))

    # Sequence-level statistics
    sequences_with_annotations = 0
    total_annotations = 0
    domains_per_sequence = []
    families_per_sequence = []

    for seq_id, seq_data in sequences.items():
        annotations = seq_data.get('annotations', [])
        if annotations:
            sequences_with_annotations += 1
            total_annotations += len(annotations)

        domains_per_sequence.append(len(seq_data.get('domains', [])))
        families_per_sequence.append(len(seq_data.get('families', [])))

    avg_annotations_per_sequence = (
        total_annotations / total_sequences if total_sequences > 0 else 0
    )

    return {
        'total_sequences': total_sequences,
        'domains_found': domains_found,
        'families_found': families_found,
        'go_terms_found': go_terms_found,
        'pathways_found': pathways_found,
        'sequences_with_annotations': sequences_with_annotations,
        'total_annotations': total_annotations,
        'avg_annotations_per_sequence': round(avg_annotations_per_sequence, 2),
        'avg_domains_per_sequence': round(sum(domains_per_sequence) / len(domains_per_sequence), 2) if domains_per_sequence else 0,
        'avg_families_per_sequence': round(sum(families_per_sequence) / len(families_per_sequence), 2) if families_per_sequence else 0,
        'annotation_coverage': round(sequences_with_annotations / total_sequences * 100, 1) if total_sequences > 0 else 0
    }


def filter_results_by_score(
    parsed_data: Dict[str, Any],
    min_score: float = None,
    analysis_types: List[str] = None
) -> Dict[str, Any]:
    """
    Filter InterProScan results by score threshold and analysis types.

    Args:
        parsed_data: Result from parse_interpro_tsv()
        min_score: Minimum score threshold (for annotations with numerical scores)
        analysis_types: List of analysis types to include (e.g., ['Pfam', 'SMART'])

    Returns:
        Filtered parsed data with same structure
    """
    if not parsed_data.get('sequences'):
        return parsed_data

    filtered_sequences = {}
    all_domains = set()
    all_families = set()
    all_go_terms = set()
    all_pathways = set()

    for seq_id, seq_data in parsed_data['sequences'].items():
        filtered_annotations = []
        seq_domains = set()
        seq_families = set()
        seq_go_terms = set()
        seq_pathways = set()

        for annotation in seq_data.get('annotations', []):
            # Filter by analysis type
            if analysis_types and annotation['analysis'] not in analysis_types:
                continue

            # Filter by score
            if min_score is not None:
                try:
                    score = float(annotation['score'])
                    if score > min_score:  # Lower scores are better in InterPro
                        continue
                except ValueError:
                    # Non-numerical score, keep the annotation
                    pass

            filtered_annotations.append(annotation)

            # Re-classify domains and families
            if annotation['analysis'] in ['Pfam', 'SMART', 'GENE3D', 'SUPERFAMILY']:
                seq_domains.add(annotation['signature_desc'])
                all_domains.add(annotation['signature_desc'])
            elif annotation['analysis'] in ['PRINTS', 'PANTHER', 'ProSiteProfiles']:
                seq_families.add(annotation['signature_desc'])
                all_families.add(annotation['signature_desc'])

        # Only include sequences with remaining annotations
        if filtered_annotations:
            filtered_sequences[seq_id] = {
                **seq_data,
                'annotations': filtered_annotations,
                'domains': list(seq_domains),
                'families': list(seq_families),
                'go_terms': list(seq_go_terms),
                'pathways': list(seq_pathways)
            }

            # Collect GO terms and pathways from original data for filtered sequences
            all_go_terms.update(seq_data.get('go_terms', []))
            all_pathways.update(seq_data.get('pathways', []))

    return {
        'sequences': filtered_sequences,
        'domains': list(all_domains),
        'families': list(all_families),
        'go_terms': list(all_go_terms),
        'pathways': list(all_pathways)
    }