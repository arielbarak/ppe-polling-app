"""
Advanced graph analysis utilities for verification.

Implements algorithms to analyze graph properties and detect adversarial behavior.
"""

import networkx as nx
from typing import Dict, Set, List, Tuple, Optional
import numpy as np
from collections import defaultdict


def build_networkx_graph(adjacency_list: Dict[str, Set[str]]) -> nx.Graph:
    """
    Convert adjacency list to NetworkX graph.
    
    Args:
        adjacency_list: Dictionary mapping node IDs to sets of neighbor IDs
        
    Returns:
        NetworkX Graph object
    """
    G = nx.Graph()
    for node, neighbors in adjacency_list.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    return G


def calculate_conductance(graph: nx.Graph, node_set: Set[str]) -> float:
    """
    Calculate the conductance of a set of nodes.
    
    Conductance measures how well-connected a set is to the rest of the graph.
    Low conductance indicates a potential Sybil cluster.
    
    Conductance(S) = edges(S, V-S) / min(vol(S), vol(V-S))
    
    Args:
        graph: NetworkX graph
        node_set: Set of nodes to analyze
        
    Returns:
        Conductance value (0 to 1)
    """
    if not node_set or len(node_set) == len(graph.nodes()):
        return 0.0
    
    # Count edges crossing the cut
    cut_edges = 0
    for node in node_set:
        for neighbor in graph.neighbors(node):
            if neighbor not in node_set:
                cut_edges += 1
    
    # Calculate volumes
    vol_s = sum(graph.degree(node) for node in node_set)
    vol_total = sum(dict(graph.degree()).values())
    vol_complement = vol_total - vol_s
    
    if min(vol_s, vol_complement) == 0:
        return 0.0
    
    return cut_edges / min(vol_s, vol_complement)


def calculate_edge_expansion(graph: nx.Graph, node_set: Set[str]) -> float:
    """
    Calculate edge expansion of a set of nodes.
    
    Edge expansion measures the ratio of edges leaving a set to the set's size.
    
    Args:
        graph: NetworkX graph
        node_set: Set of nodes to analyze
        
    Returns:
        Edge expansion ratio
    """
    if not node_set or len(node_set) == len(graph.nodes()):
        return 0.0
    
    # Count edges leaving the set
    boundary_edges = 0
    for node in node_set:
        for neighbor in graph.neighbors(node):
            if neighbor not in node_set:
                boundary_edges += 1
    
    return boundary_edges / len(node_set)


def detect_low_conductance_clusters(graph: nx.Graph, 
                                    min_size: int = 3,
                                    max_conductance: float = 0.3) -> List[Set[str]]:
    """
    Detect clusters with suspiciously low conductance.
    
    These could be Sybil clusters - groups of fake identities controlled
    by an adversary that are tightly connected to each other but poorly
    connected to honest nodes.
    
    Args:
        graph: NetworkX graph
        min_size: Minimum cluster size to consider
        max_conductance: Maximum conductance to flag as suspicious
        
    Returns:
        List of suspicious node sets
    """
    suspicious_clusters = []
    
    # Use community detection to find potential clusters
    try:
        communities = nx.community.greedy_modularity_communities(graph)
        
        for community in communities:
            if len(community) >= min_size:
                conductance = calculate_conductance(graph, community)
                if conductance < max_conductance:
                    suspicious_clusters.append(community)
    except:
        # Fallback: use connected components
        for component in nx.connected_components(graph):
            if len(component) >= min_size:
                conductance = calculate_conductance(graph, component)
                if conductance < max_conductance:
                    suspicious_clusters.append(component)
    
    return suspicious_clusters


def calculate_spectral_gap(graph: nx.Graph) -> float:
    """
    Calculate the spectral gap of the graph.
    
    The spectral gap (difference between first and second eigenvalues)
    indicates expansion properties. Larger gap = better expansion.
    
    Args:
        graph: NetworkX graph
        
    Returns:
        Spectral gap value
    """
    if len(graph.nodes()) < 2:
        return 0.0
    
    try:
        # Get Laplacian eigenvalues
        eigenvalues = nx.laplacian_spectrum(graph)
        eigenvalues = sorted(eigenvalues)
        
        # Spectral gap is difference between second smallest and smallest
        if len(eigenvalues) >= 2:
            return float(eigenvalues[1] - eigenvalues[0])
        return 0.0
    except:
        return 0.0


def analyze_degree_distribution(graph: nx.Graph) -> Dict[str, float]:
    """
    Analyze the degree distribution of the graph.
    
    Suspicious patterns (e.g., all nodes with same degree) might indicate
    artificial construction.
    
    Args:
        graph: NetworkX graph
        
    Returns:
        Dictionary with degree statistics
    """
    degrees = [graph.degree(node) for node in graph.nodes()]
    
    if not degrees:
        return {
            "min": 0,
            "max": 0,
            "mean": 0,
            "std": 0,
            "median": 0
        }
    
    return {
        "min": min(degrees),
        "max": max(degrees),
        "mean": np.mean(degrees),
        "std": np.std(degrees),
        "median": np.median(degrees)
    }


def detect_isolated_components(graph: nx.Graph, 
                               max_size: int = 5) -> List[Set[str]]:
    """
    Detect small isolated components in the graph.
    
    These might indicate incomplete PPE or adversarial structures.
    
    Args:
        graph: NetworkX graph
        max_size: Maximum component size to flag
        
    Returns:
        List of isolated components
    """
    isolated = []
    
    for component in nx.connected_components(graph):
        if len(component) <= max_size and len(component) < len(graph.nodes()):
            isolated.append(component)
    
    return isolated


def calculate_clustering_coefficient(graph: nx.Graph) -> float:
    """
    Calculate average clustering coefficient.
    
    High clustering might indicate the presence of tightly-knit Sybil groups.
    
    Args:
        graph: NetworkX graph
        
    Returns:
        Average clustering coefficient
    """
    try:
        return nx.average_clustering(graph)
    except:
        return 0.0


def analyze_vote_certification_correlation(
    graph: nx.Graph,
    voters: Set[str],
    certifications: Dict[str, Set[str]]
) -> Dict[str, float]:
    """
    Analyze correlation between votes and certifications.
    
    If voters form a tight cluster that certified each other but few others,
    this might indicate collusion.
    
    Args:
        graph: NetworkX graph
        voters: Set of user IDs who voted
        certifications: Certification adjacency list
        
    Returns:
        Dictionary with correlation metrics
    """
    if not voters:
        return {
            "voter_conductance": 0.0,
            "voter_edge_expansion": 0.0,
            "internal_cert_ratio": 0.0
        }
    
    # Calculate conductance of voters as a set
    voter_conductance = calculate_conductance(graph, voters)
    voter_expansion = calculate_edge_expansion(graph, voters)
    
    # Calculate ratio of certifications within voter set vs outside
    internal_certs = 0
    external_certs = 0
    
    for voter in voters:
        if voter in certifications:
            for certified in certifications[voter]:
                if certified in voters:
                    internal_certs += 1
                else:
                    external_certs += 1
    
    total_certs = internal_certs + external_certs
    internal_ratio = internal_certs / total_certs if total_certs > 0 else 0
    
    return {
        "voter_conductance": voter_conductance,
        "voter_edge_expansion": voter_expansion,
        "internal_cert_ratio": internal_ratio
    }


def check_graph_connectivity(graph: nx.Graph) -> Dict[str, any]:
    """
    Check overall connectivity properties of the graph.
    
    Args:
        graph: NetworkX graph
        
    Returns:
        Dictionary with connectivity metrics
    """
    is_connected = nx.is_connected(graph)
    num_components = nx.number_connected_components(graph)
    
    result = {
        "is_connected": is_connected,
        "num_components": num_components,
        "nodes": len(graph.nodes()),
        "edges": len(graph.edges())
    }
    
    if is_connected:
        result["diameter"] = nx.diameter(graph)
        result["avg_shortest_path"] = nx.average_shortest_path_length(graph)
    else:
        # Get largest component
        largest = max(nx.connected_components(graph), key=len)
        largest_subgraph = graph.subgraph(largest)
        result["largest_component_size"] = len(largest)
        result["largest_component_diameter"] = nx.diameter(largest_subgraph)
    
    return result


def compute_expansion_ratio(graph: nx.Graph, sample_sizes: List[int] = None) -> List[float]:
    """
    Compute expansion ratios for different sample sizes.
    
    Good expander graphs maintain high expansion even for small sets.
    
    Args:
        graph: NetworkX graph
        sample_sizes: Sizes to test (default: [10%, 20%, 30% of nodes])
        
    Returns:
        List of expansion ratios
    """
    n = len(graph.nodes())
    if sample_sizes is None:
        sample_sizes = [max(1, int(n * p)) for p in [0.1, 0.2, 0.3]]
    
    nodes = list(graph.nodes())
    expansion_ratios = []
    
    for size in sample_sizes:
        if size >= n or size <= 0:
            continue
        
        # Sample random subset
        import random
        sample = set(random.sample(nodes, min(size, n)))
        expansion = calculate_edge_expansion(graph, sample)
        expansion_ratios.append(expansion)
    
    return expansion_ratios