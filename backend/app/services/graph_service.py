"""
Service for managing ideal certification graphs for polls.
"""

from typing import Dict, Set, Optional, List
from ..utils.graph_utils import (
    generate_ideal_graph,
    validate_graph_properties,
    get_user_neighbors,
    calculate_graph_metrics
)


class GraphService:
    """
    Service for generating and managing ideal certification graphs.
    """
    
    def __init__(self):
        # Cache of generated graphs: {poll_id: graph}
        self._graph_cache: Dict[str, Dict[str, Set[str]]] = {}
        # Graph properties cache: {poll_id: properties}
        self._properties_cache: Dict[str, Dict] = {}
        # Configuration
        self.default_k = 3  # Default degree for regular graph
    
    def get_or_generate_graph(
        self,
        poll_id: str,
        participant_ids: List[str],
        k: Optional[int] = None
    ) -> Dict[str, Set[str]]:
        """
        Get the ideal graph for a poll, generating it if not cached.
        
        Args:
            poll_id: Poll identifier
            participant_ids: List of registered participant IDs
            k: Desired degree (None uses default)
            
        Returns:
            Adjacency list representation of the ideal graph
        """
        # Check cache first
        if poll_id in self._graph_cache:
            cached_graph = self._graph_cache[poll_id]
            # Verify cache is still valid (same participants)
            if set(cached_graph.keys()) == set(participant_ids):
                return cached_graph
        
        # Generate new graph
        effective_k = k if k is not None else self.default_k
        graph = generate_ideal_graph(participant_ids, poll_id, effective_k)
        
        # Cache it
        self._graph_cache[poll_id] = graph
        
        # Calculate and cache properties
        properties = validate_graph_properties(graph)
        self._properties_cache[poll_id] = properties
        
        return graph
    
    def get_user_neighbors(self, poll_id: str, user_id: str) -> Set[str]:
        """
        Get the assigned PPE neighbors for a user in a poll.
        
        Args:
            poll_id: Poll identifier
            user_id: User identifier
            
        Returns:
            Set of neighbor user IDs (empty if graph not generated or user not in graph)
        """
        graph = self._graph_cache.get(poll_id, {})
        return get_user_neighbors(graph, user_id)
    
    def get_graph_properties(self, poll_id: str) -> Dict:
        """
        Get validation properties for a poll's graph.
        
        Args:
            poll_id: Poll identifier
            
        Returns:
            Dictionary with graph properties and validation results
        """
        # Return cached properties if available
        if poll_id in self._properties_cache:
            return self._properties_cache[poll_id]
        
        # If graph exists but properties not cached, calculate them
        if poll_id in self._graph_cache:
            graph = self._graph_cache[poll_id]
            properties = validate_graph_properties(graph)
            self._properties_cache[poll_id] = properties
            return properties
        
        # No graph generated yet
        return {
            "is_valid": False,
            "error": "Graph not generated yet"
        }
    
    def get_graph_metrics(self, poll_id: str) -> Dict:
        """
        Get detailed metrics about a poll's certification graph.
        
        Args:
            poll_id: Poll identifier
            
        Returns:
            Dictionary with graph metrics
        """
        graph = self._graph_cache.get(poll_id, {})
        if not graph:
            return {"error": "Graph not generated yet"}
        
        return calculate_graph_metrics(graph)
    
    def invalidate_graph(self, poll_id: str):
        """
        Invalidate cached graph for a poll.
        
        Should be called when participant list changes.
        
        Args:
            poll_id: Poll identifier
        """
        if poll_id in self._graph_cache:
            del self._graph_cache[poll_id]
        if poll_id in self._properties_cache:
            del self._properties_cache[poll_id]
    
    def get_full_graph(self, poll_id: str) -> Optional[Dict[str, Set[str]]]:
        """
        Get the complete ideal graph for a poll.
        
        Args:
            poll_id: Poll identifier
            
        Returns:
            Complete adjacency list or None if not generated
        """
        return self._graph_cache.get(poll_id)


# Singleton instance
graph_service = GraphService()