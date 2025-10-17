"""
Graph utilities for generating ideal certification graphs.

The ideal graph is a random regular graph where each node has degree k.
This ensures good expansion properties which are critical for Sybil resistance.
"""

import random
import hashlib
from typing import List, Dict, Set, Tuple
import networkx as nx


def generate_seed_from_poll_id(poll_id: str, salt: str = "") -> int:
    """
    Generate a deterministic seed from poll ID for reproducible graph generation.
    
    Args:
        poll_id: The poll identifier
        salt: Optional salt for additional entropy
        
    Returns:
        Integer seed for random number generator
    """
    hash_input = f"{poll_id}{salt}".encode('utf-8')
    hash_digest = hashlib.sha256(hash_input).digest()
    # Use first 8 bytes as seed
    return int.from_bytes(hash_digest[:8], byteorder='big')


def generate_random_regular_graph(n: int, k: int, seed: int) -> Dict[int, Set[int]]:
    """
    Generate a random k-regular graph (or near-regular if not possible).
    
    A k-regular graph is one where every node has exactly k neighbors.
    This is ideal for PPE because it ensures uniform effort distribution.
    
    Args:
        n: Number of nodes (participants)
        k: Degree of each node (number of neighbors)
        seed: Random seed for deterministic generation
        
    Returns:
        Adjacency list representation: {node_index: {neighbor_indices}}
        
    Raises:
        ValueError: If k >= n or if k*n is odd (impossible to create k-regular graph)
    """
    if n < 2:
        return {}
    
    if k >= n:
        raise ValueError(f"Degree k={k} must be less than number of nodes n={n}")
    
    # For k-regular graph to exist, k*n must be even
    if (k * n) % 2 != 0:
        # If odd, we'll create a (k or k+1)-regular graph
        # Some nodes will have k edges, some k+1
        print(f"Warning: k*n is odd, creating near-regular graph")
    
    # Use NetworkX for robust random regular graph generation
    random.seed(seed)
    
    try:
        # NetworkX has a built-in random regular graph generator
        G = nx.random_regular_graph(k, n, seed=seed)
        
        # Convert to adjacency list format
        adj_list = {i: set(G.neighbors(i)) for i in range(n)}
        return adj_list
        
    except nx.NetworkXError:
        # Fallback: if exact k-regular not possible, use configuration model
        print(f"Exact {k}-regular graph not possible, using configuration model")
        degree_sequence = [k] * n
        
        # Adjust if sum is odd
        if sum(degree_sequence) % 2 != 0:
            degree_sequence[-1] += 1
        
        G = nx.configuration_model(degree_sequence, seed=seed)
        G = nx.Graph(G)  # Remove parallel edges and self-loops
        G.remove_edges_from(nx.selfloop_edges(G))
        
        # Convert to adjacency list
        adj_list = {i: set(G.neighbors(i)) for i in range(n)}
        return adj_list


def generate_ideal_graph(participant_ids: List[str], poll_id: str, k: int = 3) -> Dict[str, Set[str]]:
    """
    Generate the ideal certification graph for a poll.
    
    This maps each participant to their assigned PPE partners.
    The graph is deterministic based on poll_id and participant list.
    
    Args:
        participant_ids: List of participant user IDs
        poll_id: Poll identifier (used as seed)
        k: Target degree (number of PPE partners per participant)
        
    Returns:
        Adjacency list: {user_id: {neighbor_user_ids}}
    """
    n = len(participant_ids)
    
    if n == 0:
        return {}
    
    # Special cases
    if n == 1:
        return {participant_ids[0]: set()}
    
    if n == 2:
        # Only two participants, connect them
        return {
            participant_ids[0]: {participant_ids[1]},
            participant_ids[1]: {participant_ids[0]}
        }
    
    # Adjust k if needed
    max_k = n - 1
    effective_k = min(k, max_k)
    
    if effective_k != k:
        print(f"Adjusted k from {k} to {effective_k} for {n} participants")
    
    # Generate seed from poll_id
    seed = generate_seed_from_poll_id(poll_id)
    
    # Generate random regular graph on indices
    index_graph = generate_random_regular_graph(n, effective_k, seed)
    
    # Map indices back to user IDs
    user_graph = {}
    for idx, neighbor_indices in index_graph.items():
        user_id = participant_ids[idx]
        neighbor_ids = {participant_ids[neighbor_idx] for neighbor_idx in neighbor_indices}
        user_graph[user_id] = neighbor_ids
    
    return user_graph


def validate_graph_properties(graph: Dict[str, Set[str]]) -> Dict[str, any]:
    """
    Validate properties of the certification graph.
    
    Checks:
    - Symmetry (if A->B then B->A)
    - Connectivity
    - Degree distribution
    - Expansion properties (approximate)
    
    Args:
        graph: Adjacency list representation
        
    Returns:
        Dictionary with validation results and metrics
    """
    if not graph:
        return {
            "is_valid": True,
            "is_connected": False,
            "num_nodes": 0,
            "num_edges": 0,
            "min_degree": 0,
            "max_degree": 0,
            "avg_degree": 0,
            "is_symmetric": True
        }
    
    n = len(graph)
    
    # Check symmetry
    is_symmetric = True
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            if neighbor not in graph:
                is_symmetric = False
                break
            if node not in graph[neighbor]:
                is_symmetric = False
                break
        if not is_symmetric:
            break
    
    # Calculate degrees
    degrees = [len(neighbors) for neighbors in graph.values()]
    min_degree = min(degrees) if degrees else 0
    max_degree = max(degrees) if degrees else 0
    avg_degree = sum(degrees) / len(degrees) if degrees else 0
    
    # Count edges (each edge counted twice in adjacency list)
    total_edges = sum(degrees) // 2
    
    # Check connectivity using BFS
    is_connected = False
    if n > 0:
        start_node = next(iter(graph.keys()))
        visited = set()
        queue = [start_node]
        visited.add(start_node)
        
        while queue:
            node = queue.pop(0)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        is_connected = len(visited) == n
    
    return {
        "is_valid": is_symmetric,
        "is_connected": is_connected,
        "num_nodes": n,
        "num_edges": total_edges,
        "min_degree": min_degree,
        "max_degree": max_degree,
        "avg_degree": avg_degree,
        "is_symmetric": is_symmetric,
        "degree_distribution": {
            "min": min_degree,
            "max": max_degree,
            "avg": avg_degree
        }
    }


def get_user_neighbors(graph: Dict[str, Set[str]], user_id: str) -> Set[str]:
    """
    Get the assigned PPE neighbors for a specific user.
    
    Args:
        graph: The ideal certification graph
        user_id: The user's ID
        
    Returns:
        Set of neighbor user IDs
    """
    return graph.get(user_id, set())


def calculate_graph_metrics(graph: Dict[str, Set[str]]) -> Dict[str, any]:
    """
    Calculate detailed metrics about the graph structure.
    
    Useful for verification and debugging.
    
    Args:
        graph: Adjacency list representation
        
    Returns:
        Dictionary with various graph metrics
    """
    if not graph:
        return {
            "num_nodes": 0,
            "num_edges": 0,
            "density": 0,
            "avg_clustering": 0,
            "diameter": 0
        }
    
    # Convert to NetworkX for advanced metrics
    G = nx.Graph()
    for node, neighbors in graph.items():
        for neighbor in neighbors:
            G.add_edge(node, neighbor)
    
    n = G.number_of_nodes()
    m = G.number_of_edges()
    
    metrics = {
        "num_nodes": n,
        "num_edges": m,
        "density": nx.density(G),
    }
    
    # Calculate clustering coefficient if possible
    try:
        metrics["avg_clustering"] = nx.average_clustering(G)
    except:
        metrics["avg_clustering"] = 0
    
    # Calculate diameter if connected
    if nx.is_connected(G):
        try:
            metrics["diameter"] = nx.diameter(G)
            metrics["avg_shortest_path"] = nx.average_shortest_path_length(G)
        except:
            metrics["diameter"] = 0
            metrics["avg_shortest_path"] = 0
    else:
        metrics["diameter"] = float('inf')
        metrics["avg_shortest_path"] = float('inf')
    
    return metrics