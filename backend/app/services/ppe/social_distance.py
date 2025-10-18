"""
Social Network Distance PPE.

From Appendix B: "Leverage existing social connections to reduce
PPE effort for users who are socially connected."

Concept:
- If two users are connected on social network (e.g., mutual friends)
- PPE effort is reduced proportionally to their social distance
- Closer connections = easier PPE

This maintains Sybil resistance while improving UX for legitimate users.
"""

import networkx as nx
from typing import Dict, Any, Tuple, Optional, List
import logging

from app.services.ppe.base import PPEProtocol
from app.models.ppe_types import PPEType, PPEDifficulty

logger = logging.getLogger(__name__)


class SocialDistancePPE(PPEProtocol):
    """
    Social network distance-based PPE.
    
    Protocol:
    1. Compute graph distance between users on social network
    2. Reduce PPE difficulty based on distance:
       - Distance 1 (direct friends): 50% effort
       - Distance 2 (friend-of-friend): 75% effort  
       - Distance 3+: 100% effort (full PPE)
    3. Execute reduced-effort PPE (e.g., easier CAPTCHA)
    
    Security: Social connections must be from established networks
    (e.g., Facebook, LinkedIn) to prevent Sybil attacks.
    """
    
    def __init__(
        self,
        difficulty: PPEDifficulty = PPEDifficulty.MEDIUM,
        social_graph: Optional[nx.Graph] = None
    ):
        super().__init__(
            ppe_type=PPEType.SOCIAL_DISTANCE,
            difficulty=difficulty,
            completeness_sigma=0.97,
            soundness_epsilon=0.03
        )
        
        self.social_graph = social_graph  # NetworkX graph of social connections
        
        # Effort reduction based on social distance
        self.effort_multipliers = {
            1: 0.5,   # Direct connection: 50% effort
            2: 0.75,  # 2 hops: 75% effort
            3: 0.9,   # 3 hops: 90% effort
            float('inf'): 1.0  # No connection: 100% effort
        }
    
    def compute_social_distance(self, user_a: str, user_b: str) -> int:
        """
        Compute shortest path distance between users in social graph.
        
        Returns:
            Distance (number of hops), or infinity if not connected
        """
        if self.social_graph is None:
            logger.warning("No social graph available, using full effort")
            return float('inf')
        
        try:
            distance = nx.shortest_path_length(
                self.social_graph,
                source=user_a,
                target=user_b
            )
            return distance
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return float('inf')
    
    def get_effort_multiplier(self, distance: int) -> float:
        """Get effort multiplier for given social distance."""
        for threshold, multiplier in sorted(self.effort_multipliers.items()):
            if distance <= threshold:
                return multiplier
        return 1.0
    
    def generate_challenge(self, session_id: str, prover_id: str, verifier_id: str) -> Dict[str, Any]:
        """
        Generate challenge with difficulty adjusted by social distance.
        """
        # Compute social distance
        distance = self.compute_social_distance(prover_id, verifier_id)
        effort_multiplier = self.get_effort_multiplier(distance)
        
        # Adjust difficulty
        base_effort = self._get_base_effort_seconds()
        adjusted_effort = int(base_effort * effort_multiplier)
        
        # Generate challenge (could be any PPE type, simplified CAPTCHA here)
        challenge_length = max(3, int(6 * effort_multiplier))  # Shorter CAPTCHA if connected
        
        import random
        import string
        solution = ''.join(random.choices(string.ascii_uppercase + string.digits, k=challenge_length))
        
        return {
            "challenge_id": f"{session_id}_{prover_id[:8]}_{verifier_id[:8]}",
            "challenge_data": {
                "type": "captcha",
                "text": solution,  # In production: generate image
                "length": challenge_length,
                "social_distance": distance,
                "effort_multiplier": effort_multiplier,
                "adjusted_effort_seconds": adjusted_effort,
                "connection_info": self._get_connection_description(distance)
            },
            "verification_data": {
                "solution": solution,
                "social_distance": distance,
                "session_id": session_id
            }
        }
    
    def verify_response(
        self,
        challenge_data: Dict[str, Any],
        verification_data: Dict[str, Any],
        prover_response: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Verify response (same as CAPTCHA verification)."""
        user_answer = prover_response.get("answer", "")
        correct_solution = verification_data["solution"]
        
        if user_answer.strip().upper() != correct_solution.strip().upper():
            return False, "Incorrect solution"
        
        return True, None
    
    def estimate_effort_seconds(self) -> int:
        """Estimate base effort (before social distance adjustment)."""
        return self._get_base_effort_seconds()
    
    def _get_base_effort_seconds(self) -> int:
        """Get base effort for this difficulty level."""
        effort_map = {
            PPEDifficulty.EASY: 15,
            PPEDifficulty.MEDIUM: 30,
            PPEDifficulty.HARD: 60,
            PPEDifficulty.EXTREME: 120
        }
        return effort_map[self.difficulty]
    
    def _get_connection_description(self, distance: int) -> str:
        """Get human-readable description of connection."""
        if distance == 1:
            return "You are directly connected (friends)"
        elif distance == 2:
            return "You have a mutual friend (friend-of-friend)"
        elif distance == 3:
            return "You are connected through 2 intermediaries"
        elif distance < float('inf'):
            return f"You are connected through {distance-1} intermediaries"
        else:
            return "You are not connected on the social network"


def build_social_graph_from_data(connections: List[Tuple[str, str]]) -> nx.Graph:
    """
    Build social graph from connection data.
    
    Args:
        connections: List of (user_a, user_b) tuples representing friendships
        
    Returns:
        NetworkX graph
    """
    G = nx.Graph()
    G.add_edges_from(connections)
    return G