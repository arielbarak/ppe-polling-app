"""
Automatic parameter calculation.
Given constraints, calculate valid parameters.
"""

import math
import logging
from typing import Dict, Any, Optional

from app.models.poll_parameters import ParameterConstraints, SecurityLevel

logger = logging.getLogger(__name__)


class ParameterCalculator:
    """
    Calculates valid parameters automatically.
    
    Given:
    - Expected participants (m)
    - Security level (high/medium/low)
    
    Calculates:
    - Optimal d, κ, ηV, ηE
    """
    
    def calculate_for_security_level(
        self,
        m: int,
        security_level: str,
        custom_constraints: Optional[Dict[str, float]] = None
    ) -> ParameterConstraints:
        """
        Calculate parameters for given security level.
        
        Args:
            m: Expected number of participants
            security_level: 'high', 'medium', or 'low'
            custom_constraints: Optional custom constraints
            
        Returns:
            ParameterConstraints with calculated values
        """
        if m < 10:
            raise ValueError("Need at least 10 participants")
        
        # Get base parameters for security level
        if security_level == "high":
            base_d = 80
            base_kappa = 80
            base_eta_v = 0.01
            base_eta_e = 0.1
        elif security_level == "medium":
            base_d = 60
            base_kappa = 40
            base_eta_v = 0.025
            base_eta_e = 0.125
        elif security_level == "low":
            base_d = 40
            base_kappa = 20
            base_eta_v = 0.05
            base_eta_e = 0.15
        else:
            raise ValueError(f"Unknown security level: {security_level}")
        
        # Apply custom constraints if provided
        if custom_constraints:
            base_d = custom_constraints.get('d', base_d)
            base_kappa = custom_constraints.get('kappa', base_kappa)
            base_eta_v = custom_constraints.get('eta_v', base_eta_v)
            base_eta_e = custom_constraints.get('eta_e', base_eta_e)
        
        # Ensure d satisfies constraint 5: d ≥ 2ln(m) / (1/2 - ηV)
        min_d_constraint_5 = (2 * math.log(m)) / (0.5 - base_eta_v)
        d = max(base_d, min_d_constraint_5 * 1.1)  # 10% margin
        
        # Ensure constraint 3: b ≥ 1
        # b = sqrt(d(1/2 - ηV) / (2ln(m) - 2))
        # Need: d(1/2 - ηV) ≥ 2ln(m) - 2
        denominator = 2 * math.log(m) - 2
        if denominator > 0:
            min_d_constraint_3 = denominator / (0.5 - base_eta_v)
            d = max(d, min_d_constraint_3 * 1.1)
        
        # Calculate b
        b = math.sqrt(d * (0.5 - base_eta_v) / denominator) if denominator > 0 else 1.0
        
        # Ensure constraint 4: ηE < (b-1)(1/2 - ηV) / b
        if b > 1:
            max_eta_e = ((b - 1) * (0.5 - base_eta_v)) / b
            eta_e = min(base_eta_e, max_eta_e * 0.9)  # 90% of limit
        else:
            eta_e = base_eta_e
        
        params = ParameterConstraints(
            m=m,
            d=d,
            kappa=base_kappa,
            eta_v=base_eta_v,
            eta_e=eta_e
        )
        
        logger.info(f"Calculated parameters for {security_level} security: "
                   f"m={m}, d={d:.1f}, κ={base_kappa}, ηV={base_eta_v}, ηE={eta_e:.3f}")
        
        return params
    
    def optimize_for_user_effort(
        self,
        m: int,
        max_ppes_per_user: int,
        min_security_level: float = 0.9
    ) -> ParameterConstraints:
        """
        Calculate parameters minimizing user effort while maintaining security.
        
        Args:
            m: Expected participants
            max_ppes_per_user: Maximum PPEs user willing to do
            min_security_level: Minimum Sybil resistance (0-1)
            
        Returns:
            ParameterConstraints optimized for UX
        """
        # Constraint: d ≤ max_ppes_per_user
        d = min(max_ppes_per_user, 100)  # Cap at 100
        
        # Standard values for other params
        kappa = 40
        eta_v = 0.025
        
        # Calculate required d from constraint 5
        min_d = (2 * math.log(m)) / (0.5 - eta_v)
        if d < min_d:
            logger.warning(f"Requested d={d} < minimum {min_d:.1f}, using minimum")
            d = min_d * 1.1
        
        # Calculate b and ensure constraint 4
        denominator = 2 * math.log(m) - 2
        b = math.sqrt(d * (0.5 - eta_v) / denominator) if denominator > 0 else 1.0
        
        if b > 1:
            eta_e = ((b - 1) * (0.5 - eta_v)) / b * 0.9
        else:
            eta_e = 0.125
        
        params = ParameterConstraints(
            m=m,
            d=d,
            kappa=kappa,
            eta_v=eta_v,
            eta_e=eta_e
        )
        
        return params
    
    def calculate_minimum_participants(
        self,
        d: float,
        kappa: int = 40,
        eta_v: float = 0.025
    ) -> int:
        """
        Calculate minimum participants for given degree.
        
        From constraint 1: m ≥ κ + (ηVm + 2)ln(m) + ηVm
        
        This is transcendental, solve numerically.
        """
        def equation(m):
            if m <= 1:
                return float('inf')
            return m - kappa - (eta_v * m + 2) * math.log(m) - eta_v * m
        
        # Binary search for minimum m
        m_min = 10
        m_max = 10000
        
        while m_max - m_min > 1:
            m_mid = (m_min + m_max) // 2
            if equation(m_mid) >= 0:
                m_max = m_mid
            else:
                m_min = m_mid
        
        return m_max
    
    def calculate_maximum_degree(
        self,
        m: int,
        eta_v: float = 0.025
    ) -> float:
        """
        Calculate maximum practical degree.
        
        Upper bound: p ≤ 1 implies d ≤ m
        Practical bound: d ≤ m/2 (avoid too dense graph)
        """
        return min(m / 2, 200)  # Cap at 200 for practicality


def get_calculator() -> ParameterCalculator:
    """Factory function."""
    return ParameterCalculator()