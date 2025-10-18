"""
Spectral gap analysis for certification graphs.
Computes eigenvalues of graph Laplacian.

The second-smallest eigenvalue (algebraic connectivity) is a measure
of graph expansion - larger values indicate better expansion.
"""

import networkx as nx
import numpy as np
from scipy.sparse.linalg import eigsh
from scipy.sparse import csr_matrix
import logging
import time

from app.models.graph_metrics import SpectralGapResult

logger = logging.getLogger(__name__)


class SpectralAnalyzer:
    """
    Analyzes spectral properties of certification graph.
    
    The spectral gap (second eigenvalue of Laplacian) is related
    to expansion properties of the graph.
    """
    
    def __init__(self, graph: nx.Graph):
        """
        Initialize analyzer with graph.
        
        Args:
            graph: NetworkX graph
        """
        self.graph = graph
        self.m = graph.number_of_nodes()
    
    def compute_spectral_gap(
        self,
        threshold: float = 0.1,
        method: str = 'sparse'
    ) -> SpectralGapResult:
        """
        Compute spectral gap (second eigenvalue of Laplacian).
        
        Larger λ₂ indicates better expansion properties.
        
        Args:
            threshold: Required minimum λ₂
            method: 'sparse' for large graphs, 'dense' for small graphs
            
        Returns:
            SpectralGapResult with λ₂ and verification status
        """
        logger.info(f"Computing spectral gap using {method} method")
        
        start_time = time.time()
        
        if self.m == 0:
            return SpectralGapResult(
                second_eigenvalue=0.0,
                algebraic_connectivity=0.0,
                satisfies_threshold=False,
                threshold=threshold,
                computation_time_ms=0.0
            )
        
        try:
            if method == 'sparse' and self.m > 100:
                lambda_2 = self._compute_sparse_spectral_gap()
            else:
                lambda_2 = self._compute_dense_spectral_gap()
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            result = SpectralGapResult(
                second_eigenvalue=float(lambda_2),
                algebraic_connectivity=float(lambda_2),
                satisfies_threshold=(lambda_2 >= threshold),
                threshold=threshold,
                computation_time_ms=elapsed_ms
            )
            
            logger.info(f"Spectral gap computed: λ₂={lambda_2:.4f}, "
                       f"time={elapsed_ms:.2f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"Error computing spectral gap: {e}")
            return SpectralGapResult(
                second_eigenvalue=0.0,
                algebraic_connectivity=0.0,
                satisfies_threshold=False,
                threshold=threshold,
                computation_time_ms=(time.time() - start_time) * 1000
            )
    
    def _compute_sparse_spectral_gap(self) -> float:
        """
        Compute spectral gap using sparse matrix methods.
        Efficient for large graphs.
        """
        # Get Laplacian matrix as sparse matrix
        L = nx.laplacian_matrix(self.graph)
        
        # Compute smallest 3 eigenvalues
        # λ₀ = 0 always (for connected graph)
        # λ₁ is what we want (algebraic connectivity)
        try:
            eigenvalues = eigsh(L, k=min(3, self.m-1), which='SM', return_eigenvectors=False)
            eigenvalues = np.sort(eigenvalues)
            
            # Second smallest eigenvalue
            lambda_2 = eigenvalues[1] if len(eigenvalues) > 1 else 0.0
            
            return lambda_2
            
        except Exception as e:
            logger.warning(f"Sparse eigsh failed: {e}, falling back to dense")
            return self._compute_dense_spectral_gap()
    
    def _compute_dense_spectral_gap(self) -> float:
        """
        Compute spectral gap using dense matrix methods.
        Better for small graphs.
        """
        # Get Laplacian matrix as dense numpy array
        L = nx.laplacian_matrix(self.graph).toarray()
        
        # Compute all eigenvalues
        eigenvalues = np.linalg.eigvalsh(L)
        eigenvalues = np.sort(eigenvalues)
        
        # Second smallest eigenvalue
        lambda_2 = eigenvalues[1] if len(eigenvalues) > 1 else 0.0
        
        return lambda_2
    
    def compute_all_eigenvalues(self, k: int = 10) -> np.ndarray:
        """
        Compute k smallest eigenvalues of Laplacian.
        
        Args:
            k: Number of eigenvalues to compute
            
        Returns:
            Array of k smallest eigenvalues
        """
        if self.m == 0:
            return np.array([])
        
        k = min(k, self.m - 1)
        
        try:
            L = nx.laplacian_matrix(self.graph)
            eigenvalues = eigsh(L, k=k, which='SM', return_eigenvectors=False)
            return np.sort(eigenvalues)
        except:
            L = nx.laplacian_matrix(self.graph).toarray()
            eigenvalues = np.linalg.eigvalsh(L)
            return np.sort(eigenvalues)[:k]