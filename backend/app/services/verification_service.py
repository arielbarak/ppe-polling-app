"""
Advanced verification service for polls.

Implements comprehensive verification algorithms including graph analysis,
Sybil detection, and statistical analysis.
"""

from typing import Dict, List, Set, Optional, Any
from ..models.poll import Poll
from ..models.proof_graph import ProofGraph
from ..utils.graph_analysis import (
    build_networkx_graph,
    calculate_conductance,
    detect_low_conductance_clusters,
    calculate_spectral_gap,
    analyze_degree_distribution,
    detect_isolated_components,
    calculate_clustering_coefficient,
    analyze_vote_certification_correlation,
    check_graph_connectivity,
    compute_expansion_ratio
)
from ..utils.crypto_utils import verify_signature
import networkx as nx


class VerificationResult:
    """
    Structured result from verification.
    """
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
        self.metrics = {}
        self.analysis = {}
    
    def add_error(self, message: str):
        """Add an error (makes poll invalid)."""
        self.is_valid = False
        self.errors.append(message)
    
    def add_warning(self, message: str):
        """Add a warning (doesn't invalidate poll)."""
        self.warnings.append(message)
    
    def add_metric(self, key: str, value: Any):
        """Add a verification metric."""
        self.metrics[key] = value
    
    def add_analysis(self, key: str, value: Any):
        """Add analysis result."""
        self.analysis[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "analysis": self.analysis,
            "summary": self._generate_summary()
        }
    
    def _generate_summary(self) -> str:
        """Generate human-readable summary."""
        if not self.errors and not self.warnings:
            return "✅ Poll verification passed. No issues detected."
        
        parts = []
        if self.errors:
            parts.append(f"❌ {len(self.errors)} critical errors found")
        if self.warnings:
            parts.append(f"⚠️ {len(self.warnings)} warnings")
        
        return " | ".join(parts)


class VerificationService:
    """
    Service for advanced poll verification.
    """
    
    def __init__(self):
        self.min_certifications_required = 2
        self.min_conductance_threshold = 0.2
        self.max_clustering_threshold = 0.8
        self.min_expansion_ratio = 0.3
    
    def verify_poll_comprehensive(self, poll: Poll) -> VerificationResult:
        """
        Perform comprehensive verification of a poll.
        
        This is the main verification function that runs all checks.
        
        Args:
            poll: Poll to verify
            
        Returns:
            VerificationResult with complete analysis
        """
        result = VerificationResult()
        
        # Basic checks
        self._verify_basic_structure(poll, result)
        
        # Graph analysis
        if poll.ppe_certifications:
            self._verify_graph_properties(poll, result)
            self._detect_sybil_attacks(poll, result)
        
        # Vote verification
        self._verify_votes(poll, result)
        
        # Statistical analysis
        self._perform_statistical_analysis(poll, result)
        
        return result
    
    def _verify_basic_structure(self, poll: Poll, result: VerificationResult):
        """Verify basic poll structure."""
        # Check participants
        num_participants = len(poll.registrants)
        result.add_metric("total_participants", num_participants)
        
        if num_participants == 0:
            result.add_error("Poll has no registered participants")
            return
        
        # Check certifications
        num_certifications = sum(len(certs) for certs in poll.ppe_certifications.values()) // 2
        result.add_metric("total_certifications", num_certifications)
        
        if num_certifications == 0 and num_participants > 1:
            result.add_warning("Poll has no PPE certifications")
        
        # Check votes
        num_votes = len(poll.votes)
        result.add_metric("total_votes", num_votes)
        
        participation_rate = num_votes / num_participants if num_participants > 0 else 0
        result.add_metric("participation_rate", participation_rate)
        
        if participation_rate < 0.1:
            result.add_warning("Very low participation rate (< 10%)")
    
    def _verify_graph_properties(self, poll: Poll, result: VerificationResult):
        """Verify graph expansion and connectivity properties."""
        # Build graph
        graph = build_networkx_graph(poll.ppe_certifications)
        
        # Connectivity
        connectivity = check_graph_connectivity(graph)
        result.add_analysis("connectivity", connectivity)
        
        if not connectivity["is_connected"]:
            result.add_warning(
                f"Certification graph is disconnected "
                f"({connectivity['num_components']} components)"
            )
        
        # Degree distribution
        degree_stats = analyze_degree_distribution(graph)
        result.add_analysis("degree_distribution", degree_stats)
        
        if degree_stats["min"] < self.min_certifications_required:
            result.add_error(
                f"Some users have fewer than {self.min_certifications_required} certifications"
            )
        
        # Clustering coefficient
        clustering = calculate_clustering_coefficient(graph)
        result.add_metric("clustering_coefficient", clustering)
        
        if clustering > self.max_clustering_threshold:
            result.add_warning(
                f"High clustering coefficient ({clustering:.2f}) may indicate collusion"
            )
        
        # Spectral gap
        try:
            spectral_gap = calculate_spectral_gap(graph)
            result.add_metric("spectral_gap", spectral_gap)
            
            if spectral_gap < 0.1:
                result.add_warning("Low spectral gap indicates poor expansion properties")
        except:
            result.add_warning("Could not compute spectral gap")
        
        # Expansion ratios
        try:
            expansion_ratios = compute_expansion_ratio(graph)
            result.add_analysis("expansion_ratios", expansion_ratios)
            
            if any(ratio < self.min_expansion_ratio for ratio in expansion_ratios):
                result.add_warning("Low expansion ratios detected")
        except:
            pass
    
    def _detect_sybil_attacks(self, poll: Poll, result: VerificationResult):
        """Detect potential Sybil attacks."""
        graph = build_networkx_graph(poll.ppe_certifications)
        
        # Detect low-conductance clusters
        suspicious_clusters = detect_low_conductance_clusters(
            graph, 
            min_size=3,
            max_conductance=self.min_conductance_threshold
        )
        
        if suspicious_clusters:
            result.add_warning(
                f"Detected {len(suspicious_clusters)} suspicious clusters with low conductance"
            )
            result.add_analysis("suspicious_clusters", [
                {
                    "size": len(cluster),
                    "conductance": calculate_conductance(graph, cluster),
                    "nodes": list(cluster)[:3]  # Show first 3 nodes
                }
                for cluster in suspicious_clusters
            ])
        
        # Detect isolated components
        isolated = detect_isolated_components(graph, max_size=5)
        
        if isolated:
            result.add_warning(
                f"Detected {len(isolated)} small isolated components"
            )
            result.add_analysis("isolated_components", [
                {"size": len(comp), "nodes": list(comp)}
                for comp in isolated
            ])
        
        # Analyze vote-certification correlation
        voters = set(poll.votes.keys())
        if voters:
            correlation = analyze_vote_certification_correlation(
                graph, voters, poll.ppe_certifications
            )
            result.add_analysis("vote_certification_correlation", correlation)
            
            if correlation["voter_conductance"] < self.min_conductance_threshold:
                result.add_warning("Voters form a low-conductance cluster (potential collusion)")
            
            if correlation["internal_cert_ratio"] > 0.8:
                result.add_warning("Voters primarily certified each other (potential collusion)")
    
    def _verify_votes(self, poll: Poll, result: VerificationResult):
        """Verify all votes are valid."""
        unauthorized_votes = []
        invalid_signatures = []
        
        for voter_id, vote_data in poll.votes.items():
            # Check voter is registered
            if voter_id not in poll.registrants:
                unauthorized_votes.append(voter_id)
                continue
            
            # Check voter has sufficient certifications
            if not poll.can_vote(voter_id, self.min_certifications_required):
                cert_count = len(poll.ppe_certifications.get(voter_id, set()))
                unauthorized_votes.append(f"{voter_id} (only {cert_count} certs)")
                continue
            
            # Verify signature
            try:
                if isinstance(vote_data, dict):
                    public_key = vote_data.get("publicKey", {})
                    option = vote_data.get("option", "")
                    signature = vote_data.get("signature", "")
                else:
                    public_key = vote_data.publicKey
                    option = vote_data.option
                    signature = vote_data.signature
                
                message_to_verify = f"{poll.id}:{option}"
                if not verify_signature(public_key, message_to_verify, signature):
                    invalid_signatures.append(voter_id)
            except Exception as e:
                invalid_signatures.append(f"{voter_id} (error: {str(e)})")
        
        # Report results
        if unauthorized_votes:
            result.add_error(
                f"{len(unauthorized_votes)} unauthorized votes detected"
            )
            result.add_analysis("unauthorized_votes", unauthorized_votes[:10])  # Limit to 10
        
        if invalid_signatures:
            result.add_error(
                f"{len(invalid_signatures)} votes with invalid signatures"
            )
            result.add_analysis("invalid_signatures", invalid_signatures[:10])
        
        valid_votes = len(poll.votes) - len(unauthorized_votes) - len(invalid_signatures)
        result.add_metric("valid_votes", valid_votes)
    
    def _perform_statistical_analysis(self, poll: Poll, result: VerificationResult):
        """Perform statistical analysis on the poll."""
        # Certification coverage
        num_participants = len(poll.registrants)
        if num_participants > 1:
            max_possible_edges = (num_participants * (num_participants - 1)) / 2
            actual_edges = sum(len(certs) for certs in poll.ppe_certifications.values()) / 2
            coverage = actual_edges / max_possible_edges
            result.add_metric("certification_coverage", coverage)
            
            if coverage < 0.1:
                result.add_warning("Very low certification coverage (< 10%)")
        
        # Certification uniformity (variance in certification counts)
        cert_counts = [len(certs) for certs in poll.ppe_certifications.values()]
        if cert_counts:
            import statistics
            mean_certs = statistics.mean(cert_counts)
            std_certs = statistics.stdev(cert_counts) if len(cert_counts) > 1 else 0
            
            result.add_metric("avg_certifications_per_user", mean_certs)
            result.add_metric("std_certifications_per_user", std_certs)
            
            # High variance might indicate selective certification
            if std_certs / mean_certs > 0.5:
                result.add_warning("High variance in certification distribution")


# Singleton instance
verification_service = VerificationService()