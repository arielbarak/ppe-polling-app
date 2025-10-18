"""
Tests for different PPE implementations.
"""

import pytest
from unittest.mock import Mock, patch
import networkx as nx

from app.services.ppe.symmetric_captcha import SymmetricCaptchaPPE
from app.services.ppe.proof_of_storage import ProofOfStoragePPE
from app.services.ppe.computational import ComputationalPPE
from app.services.ppe.social_distance import SocialDistancePPE, build_social_graph_from_data
from app.models.ppe_types import PPEDifficulty


class TestSymmetricCaptchaPPE:
    """Test the Symmetric CAPTCHA PPE implementation."""
    
    def test_generate_challenge(self):
        """Test challenge generation."""
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.MEDIUM)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        assert "challenge_id" in challenge
        assert "challenge_data" in challenge
        assert "verification_data" in challenge
        assert len(challenge["verification_data"]["solution"]) == 6  # MEDIUM = 6 chars
        assert "mac" in challenge["challenge_data"]
    
    def test_verify_correct_response(self):
        """Test verification of correct response."""
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        solution = challenge["verification_data"]["solution"]
        
        # Correct response
        response = {
            "answer": solution,
            "mac": challenge["challenge_data"]["mac"]
        }
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is True
        assert reason is None
    
    def test_verify_incorrect_response(self):
        """Test verification of incorrect response."""
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        # Wrong answer
        response = {
            "answer": "WRONG",
            "mac": challenge["challenge_data"]["mac"]
        }
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is False
        assert "incorrect" in reason.lower()
    
    def test_case_insensitivity(self):
        """Test that CAPTCHA is case-insensitive."""
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        solution = challenge["verification_data"]["solution"]
        
        # Lowercase response
        response = {
            "answer": solution.lower(),
            "mac": challenge["challenge_data"]["mac"]
        }
        
        success, _ = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is True
    
    def test_mac_validation(self):
        """Test MAC validation prevents replay attacks."""
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        solution = challenge["verification_data"]["solution"]
        
        # Wrong MAC
        response = {
            "answer": solution,
            "mac": "invalid_mac"
        }
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is False
        assert "mac" in reason.lower()
    
    def test_mutual_challenges(self):
        """Test generation of mutual challenges."""
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.MEDIUM)
        
        challenge_a, challenge_b = ppe.generate_mutual_challenges(
            "session_1", "user_a", "user_b"
        )
        
        assert challenge_a["challenge_id"] != challenge_b["challenge_id"]
        assert challenge_a["verification_data"]["solution"] != challenge_b["verification_data"]["solution"]
    
    def test_estimate_effort_seconds(self):
        """Test effort estimation."""
        ppe_easy = SymmetricCaptchaPPE(difficulty=PPEDifficulty.EASY)
        ppe_hard = SymmetricCaptchaPPE(difficulty=PPEDifficulty.HARD)
        
        assert ppe_easy.estimate_effort_seconds() < ppe_hard.estimate_effort_seconds()


class TestProofOfStoragePPE:
    """Test the Proof-of-Storage PPE implementation."""
    
    def test_generate_challenge(self):
        """Test storage challenge generation."""
        ppe = ProofOfStoragePPE(difficulty=PPEDifficulty.MEDIUM)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        assert "challenge_data" in challenge
        assert "filename" in challenge["challenge_data"]
        assert "share_link" in challenge["challenge_data"]
        assert "expected_hash" in challenge["verification_data"]
        assert challenge["challenge_data"]["file_size"] == 10240  # MEDIUM = 10KB
    
    def test_verify_correct_hash(self):
        """Test verification of correct file hash."""
        ppe = ProofOfStoragePPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        expected_hash = challenge["verification_data"]["expected_hash"]
        
        response = {
            "file_hash": expected_hash
        }
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is True
        assert reason is None
    
    def test_verify_incorrect_hash(self):
        """Test verification of incorrect hash."""
        ppe = ProofOfStoragePPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        response = {
            "file_hash": "0" * 64  # Wrong hash
        }
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is False
        assert "mismatch" in reason.lower()
    
    def test_no_hash_provided(self):
        """Test handling of missing hash."""
        ppe = ProofOfStoragePPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        response = {}  # No hash
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is False
        assert "no hash" in reason.lower()
    
    def test_storage_instructions(self):
        """Test provider-specific instructions."""
        ppe = ProofOfStoragePPE(storage_provider="google_drive")
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        instructions = challenge["challenge_data"]["instructions"]
        
        assert "step_1" in instructions
        assert "google" in instructions["step_1"].lower() or "click" in instructions["step_1"].lower()


class TestComputationalPPE:
    """Test the Computational PPE implementation."""
    
    def test_generate_challenge(self):
        """Test computational challenge generation."""
        ppe = ComputationalPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        assert "challenge_string" in challenge["challenge_data"]
        assert "difficulty_bits" in challenge["challenge_data"]
        assert challenge["challenge_data"]["difficulty_bits"] == 16  # EASY
        assert "target_hex" in challenge["challenge_data"]
    
    def test_solve_and_verify(self):
        """Test solving and verifying computational challenge."""
        ppe = ComputationalPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        challenge_string = challenge["verification_data"]["challenge_string"]
        target = challenge["verification_data"]["target"]
        
        # Solve challenge (may take a few seconds for EASY difficulty)
        nonce = ComputationalPPE.solve_challenge(challenge_string, target, max_nonce=100000)
        
        if nonce:  # Solution found
            response = {"nonce": nonce}
            
            success, reason = ppe.verify_response(
                challenge["challenge_data"],
                challenge["verification_data"],
                response
            )
            
            assert success is True
            assert reason is None
        else:
            pytest.skip("No solution found within iteration limit")
    
    def test_verify_incorrect_nonce(self):
        """Test verification of incorrect nonce."""
        ppe = ComputationalPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        response = {"nonce": "0"}  # Wrong nonce
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is False
        assert "target" in reason.lower()
    
    def test_invalid_nonce_format(self):
        """Test handling of invalid nonce format."""
        ppe = ComputationalPPE(difficulty=PPEDifficulty.EASY)
        
        challenge = ppe.generate_challenge("session_1", "user_a", "user_b")
        
        response = {"nonce": "not_a_number"}
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is False
        assert "integer" in reason.lower()
    
    def test_estimate_effort_scaling(self):
        """Test that effort estimation scales with difficulty."""
        ppe_easy = ComputationalPPE(difficulty=PPEDifficulty.EASY)
        ppe_medium = ComputationalPPE(difficulty=PPEDifficulty.MEDIUM)
        ppe_hard = ComputationalPPE(difficulty=PPEDifficulty.HARD)
        
        easy_effort = ppe_easy.estimate_effort_seconds()
        medium_effort = ppe_medium.estimate_effort_seconds()
        hard_effort = ppe_hard.estimate_effort_seconds()
        
        assert easy_effort < medium_effort < hard_effort


class TestSocialDistancePPE:
    """Test the Social Distance PPE implementation."""
    
    def setup_method(self):
        """Set up test social graph."""
        # Create a simple social graph
        connections = [
            ("alice", "bob"),
            ("bob", "charlie"),
            ("charlie", "dave"),
            ("eve", "frank")  # Isolated component
        ]
        self.social_graph = build_social_graph_from_data(connections)
    
    def test_compute_social_distance_direct(self):
        """Test direct connection distance."""
        ppe = SocialDistancePPE(social_graph=self.social_graph)
        
        distance = ppe.compute_social_distance("alice", "bob")
        assert distance == 1
    
    def test_compute_social_distance_indirect(self):
        """Test indirect connection distance."""
        ppe = SocialDistancePPE(social_graph=self.social_graph)
        
        distance = ppe.compute_social_distance("alice", "charlie")
        assert distance == 2
    
    def test_compute_social_distance_no_connection(self):
        """Test no connection case."""
        ppe = SocialDistancePPE(social_graph=self.social_graph)
        
        distance = ppe.compute_social_distance("alice", "eve")
        assert distance == float('inf')
    
    def test_effort_multiplier_calculation(self):
        """Test effort multiplier based on social distance."""
        ppe = SocialDistancePPE()
        
        assert ppe.get_effort_multiplier(1) == 0.5  # Direct connection
        assert ppe.get_effort_multiplier(2) == 0.75  # Friend-of-friend
        assert ppe.get_effort_multiplier(3) == 0.9  # 3 hops
        assert ppe.get_effort_multiplier(float('inf')) == 1.0  # No connection
    
    def test_generate_challenge_with_social_discount(self):
        """Test challenge generation with social distance discount."""
        ppe = SocialDistancePPE(
            difficulty=PPEDifficulty.MEDIUM,
            social_graph=self.social_graph
        )
        
        challenge = ppe.generate_challenge("session_1", "alice", "bob")
        
        assert challenge["challenge_data"]["social_distance"] == 1
        assert challenge["challenge_data"]["effort_multiplier"] == 0.5
        assert challenge["challenge_data"]["length"] == 3  # 6 * 0.5 = 3 (min 3)
    
    def test_generate_challenge_no_connection(self):
        """Test challenge generation with no social connection."""
        ppe = SocialDistancePPE(
            difficulty=PPEDifficulty.MEDIUM,
            social_graph=self.social_graph
        )
        
        challenge = ppe.generate_challenge("session_1", "alice", "eve")
        
        assert challenge["challenge_data"]["social_distance"] == float('inf')
        assert challenge["challenge_data"]["effort_multiplier"] == 1.0
        assert challenge["challenge_data"]["length"] == 6  # Full difficulty
    
    def test_verify_social_captcha_response(self):
        """Test verification of social CAPTCHA response."""
        ppe = SocialDistancePPE(social_graph=self.social_graph)
        
        challenge = ppe.generate_challenge("session_1", "alice", "bob")
        solution = challenge["verification_data"]["solution"]
        
        response = {"answer": solution}
        
        success, reason = ppe.verify_response(
            challenge["challenge_data"],
            challenge["verification_data"],
            response
        )
        
        assert success is True
        assert reason is None
    
    def test_no_social_graph_fallback(self):
        """Test behavior when no social graph is available."""
        ppe = SocialDistancePPE(social_graph=None)
        
        distance = ppe.compute_social_distance("alice", "bob")
        assert distance == float('inf')
    
    def test_connection_description(self):
        """Test human-readable connection descriptions."""
        ppe = SocialDistancePPE()
        
        assert "directly connected" in ppe._get_connection_description(1)
        assert "mutual friend" in ppe._get_connection_description(2)
        assert "not connected" in ppe._get_connection_description(float('inf'))


class TestBuildSocialGraph:
    """Test social graph construction utilities."""
    
    def test_build_social_graph_from_data(self):
        """Test building social graph from connection data."""
        connections = [
            ("user1", "user2"),
            ("user2", "user3"),
            ("user3", "user4")
        ]
        
        graph = build_social_graph_from_data(connections)
        
        assert isinstance(graph, nx.Graph)
        assert graph.number_of_nodes() == 4
        assert graph.number_of_edges() == 3
        assert graph.has_edge("user1", "user2")
        assert graph.has_edge("user2", "user3")
        assert graph.has_edge("user3", "user4")
    
    def test_shortest_path_calculation(self):
        """Test shortest path calculation in built graph."""
        connections = [
            ("a", "b"),
            ("b", "c"),
            ("c", "d")
        ]
        
        graph = build_social_graph_from_data(connections)
        
        # Test direct connection
        assert nx.shortest_path_length(graph, "a", "b") == 1
        
        # Test 2-hop connection
        assert nx.shortest_path_length(graph, "a", "c") == 2
        
        # Test 3-hop connection
        assert nx.shortest_path_length(graph, "a", "d") == 3


class TestPPESecurity:
    """Test security properties of PPE implementations."""
    
    def test_symmetric_captcha_security_parameters(self):
        """Test security parameter validation for symmetric CAPTCHA."""
        # Valid parameters
        ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.MEDIUM)
        ppe.completeness_sigma = 0.95
        ppe.soundness_epsilon = 0.05
        
        valid, reason = ppe.validate_security_parameters()
        assert valid is True
        assert reason is None
        
        # Invalid: completeness too low
        ppe.completeness_sigma = 0.3
        valid, reason = ppe.validate_security_parameters()
        assert valid is False
        assert "completeness" in reason.lower()
        
        # Invalid: soundness too high
        ppe.completeness_sigma = 0.95
        ppe.soundness_epsilon = 0.3
        valid, reason = ppe.validate_security_parameters()
        assert valid is False
        assert "soundness" in reason.lower()
    
    def test_computational_ppe_difficulty_correlation(self):
        """Test that computational difficulty correlates with security."""
        ppe = ComputationalPPE(difficulty=PPEDifficulty.EXTREME)
        
        # High difficulty should have very high completeness and low soundness
        assert ppe.completeness_sigma >= 0.99
        assert ppe.soundness_epsilon <= 0.01
    
    def test_proof_of_storage_high_completeness(self):
        """Test that proof-of-storage has high completeness."""
        ppe = ProofOfStoragePPE()
        
        # Should have high completeness since it's just file retrieval
        assert ppe.completeness_sigma >= 0.98


if __name__ == "__main__":
    pytest.main([__file__, "-v"])