"""
Mathematical utilities for parameter calculations.
"""

import math
from typing import Optional, Tuple


def calculate_edge_probability(d: float, m: int) -> float:
    """Calculate edge probability p = d/m."""
    if m <= 0:
        raise ValueError("m must be positive")
    return d / m


def calculate_expansion_parameter(d: float, m: int, eta_v: float) -> Optional[float]:
    """
    Calculate expansion parameter b.
    
    From paper: b = sqrt(d(1/2 - ηV) / (2ln(m) - 2))
    
    Returns None if calculation is invalid.
    """
    if m <= 1:
        return None
    
    denominator = 2 * math.log(m) - 2
    if denominator <= 0:
        return None
    
    numerator = d * (0.5 - eta_v)
    if numerator <= 0:
        return None
    
    return math.sqrt(numerator / denominator)


def calculate_minimum_degree(m: int, eta_v: float) -> float:
    """
    Calculate minimum degree from constraint 5.
    
    d ≥ 2ln(m) / (1/2 - ηV)
    """
    if m <= 1:
        raise ValueError("m must be > 1")
    
    denominator = 0.5 - eta_v
    if denominator <= 0:
        raise ValueError("eta_v must be < 0.5")
    
    return (2 * math.log(m)) / denominator


def calculate_eta_e_upper_bound(d: float, m: int, eta_v: float) -> Optional[float]:
    """
    Calculate upper bound for eta_e from constraint 4.
    
    ηE < (b-1)(1/2 - ηV) / b
    """
    b = calculate_expansion_parameter(d, m, eta_v)
    
    if b is None or b <= 1:
        return None
    
    return ((b - 1) * (0.5 - eta_v)) / b


def calculate_minimum_participants_for_constraint_1(
    d: float, 
    kappa: int, 
    eta_v: float, 
    max_iterations: int = 1000
) -> int:
    """
    Calculate minimum participants satisfying constraint 1.
    
    Constraint 1: m ≥ κ + (ηVm + 2)ln(m) + ηVm
    
    Uses binary search to find minimum m.
    """
    def constraint_1_satisfied(m: int) -> bool:
        if m <= 1:
            return False
        rhs = kappa + (eta_v * m + 2) * math.log(m) + eta_v * m
        return m >= rhs
    
    # Binary search
    m_min = 10
    m_max = 100000
    
    for _ in range(max_iterations):
        if m_max - m_min <= 1:
            break
        
        m_mid = (m_min + m_max) // 2
        
        if constraint_1_satisfied(m_mid):
            m_max = m_mid
        else:
            m_min = m_mid
    
    return m_max


def estimate_sybil_resistance_percentage(m: int, d: float) -> float:
    """
    Estimate Sybil resistance as percentage.
    
    Based on adversary with ~10% of total edges.
    """
    # Typical adversary resources
    adversary_edges = 0.1 * m * d
    
    # Max Sybil nodes ≈ adversary_edges / d
    max_sybil_nodes = adversary_edges / d if d > 0 else 0
    
    # Resistance percentage
    sybil_percentage = (max_sybil_nodes / m) * 100 if m > 0 else 0
    resistance_percentage = 100 - sybil_percentage
    
    return max(0, min(100, resistance_percentage))


def estimate_completion_rate_percentage(d: float, eta_e: float) -> float:
    """
    Estimate user completion rate as percentage.
    
    Based on expected failures and user behavior.
    """
    # Base completion rate (assuming 95% success per PPE)
    base_rate = 0.95
    
    # Adjust for number of PPEs (more PPEs = harder)
    difficulty_penalty = min(0.3, d / 1000)  # Max 30% penalty
    
    # Adjust for failure rate
    failure_penalty = eta_e * 0.5  # Partial penalty for allowed failures
    
    completion_rate = base_rate * (1 - difficulty_penalty - failure_penalty)
    
    return max(0, min(100, completion_rate * 100))


def validate_parameter_bounds(
    m: int, 
    d: float, 
    kappa: int, 
    eta_v: float, 
    eta_e: float
) -> Tuple[bool, str]:
    """
    Validate basic parameter bounds.
    
    Returns (is_valid, error_message).
    """
    if m <= 0:
        return False, "m must be positive"
    
    if d <= 0:
        return False, "d must be positive"
    
    if kappa < 20 or kappa > 128:
        return False, "kappa must be between 20 and 128"
    
    if eta_v <= 0 or eta_v >= 0.5:
        return False, "eta_v must be between 0 and 0.5"
    
    if eta_e <= 0 or eta_e >= 0.5:
        return False, "eta_e must be between 0 and 0.5"
    
    if d > m:
        return False, "d cannot exceed m (degree > participants)"
    
    return True, ""


def calculate_graph_density(d: float, m: int) -> float:
    """Calculate graph density (fraction of possible edges)."""
    if m <= 1:
        return 0.0
    
    max_edges = m * (m - 1) / 2  # Complete graph
    expected_edges = m * d / 2  # Each node has degree d
    
    return expected_edges / max_edges if max_edges > 0 else 0.0


def solve_transcendental_equation(
    func, 
    x_min: float, 
    x_max: float, 
    tolerance: float = 1e-6,
    max_iterations: int = 100
) -> Optional[float]:
    """
    Solve transcendental equation using bisection method.
    
    Args:
        func: Function that should equal zero at solution
        x_min, x_max: Search bounds
        tolerance: Convergence tolerance
        max_iterations: Maximum iterations
        
    Returns:
        Solution x where func(x) ≈ 0, or None if not found
    """
    # Check if bounds bracket a root
    f_min = func(x_min)
    f_max = func(x_max)
    
    if f_min * f_max > 0:
        return None  # No root in interval
    
    for _ in range(max_iterations):
        x_mid = (x_min + x_max) / 2
        f_mid = func(x_mid)
        
        if abs(f_mid) < tolerance or abs(x_max - x_min) < tolerance:
            return x_mid
        
        if f_min * f_mid < 0:
            x_max = x_mid
            f_max = f_mid
        else:
            x_min = x_mid
            f_min = f_mid
    
    return x_mid if 'x_mid' in locals() else None