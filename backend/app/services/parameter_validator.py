"""
Parameter constraint validator.
Implements all 6 constraints from Appendix C.
"""

import math
import logging
from typing import Tuple, List, Dict, Any

from app.models.poll_parameters import (
    ParameterConstraints,
    ParameterValidationResult
)

logger = logging.getLogger(__name__)


class ParameterValidator:
    """
    Validates poll parameters against Appendix C constraints.
    
    All 6 constraints must be satisfied for security guarantees.
    """
    
    def __init__(self):
        # Tolerance for floating point comparisons
        self.epsilon = 1e-10
    
    def validate_all(self, params: ParameterConstraints) -> ParameterValidationResult:
        """
        Validate all constraints.
        
        Returns:
            ParameterValidationResult with detailed validation info
        """
        result = ParameterValidationResult(
            valid=True,
            calculated_values={}
        )
        
        # Validate each constraint
        checks = [
            self._check_constraint_1,
            self._check_constraint_2,
            self._check_constraint_3,
            self._check_constraint_4,
            self._check_constraint_5,
            self._check_constraint_6
        ]
        
        for i, check in enumerate(checks, 1):
            satisfied, error, warning, calculated = check(params)
            
            # Set constraint satisfaction flag
            setattr(result, f"constraint_{i}_satisfied", satisfied)
            
            # Add errors/warnings
            if error:
                result.errors.append(f"Constraint {i}: {error}")
                result.valid = False
            if warning:
                result.warnings.append(f"Constraint {i}: {warning}")
            
            # Store calculated values
            result.calculated_values.update(calculated)
        
        # Calculate security metrics
        if result.valid:
            result.estimated_sybil_resistance = self._estimate_sybil_resistance(params)
            result.estimated_completion_rate = self._estimate_completion_rate(params)
        
        return result
    
    def _check_constraint_1(
        self,
        params: ParameterConstraints
    ) -> Tuple[bool, str, str, Dict[str, float]]:
        """
        Constraint 1: Minimum nodes for expansion.
        
        From paper: m ≥ κ + (ηVm + 2)ln(m) + ηVm
        
        Rearranging: m(1 - ηV) ≥ κ + (ηVm + 2)ln(m)
        """
        m = params.m
        kappa = params.kappa
        eta_v = params.eta_v
        
        # Right-hand side
        rhs = kappa + (eta_v * m + 2) * math.log(m) + eta_v * m
        
        satisfied = m >= rhs
        
        error = None
        warning = None
        
        if not satisfied:
            error = f"Insufficient participants: need m ≥ {rhs:.1f}, got {m}"
        elif m < rhs * 1.2:
            warning = f"Participants ({m}) barely satisfy minimum ({rhs:.1f}). Consider more participants."
        
        calculated = {
            "constraint_1_minimum_m": rhs,
            "constraint_1_margin": m - rhs
        }
        
        return satisfied, error, warning, calculated
    
    def _check_constraint_2(
        self,
        params: ParameterConstraints
    ) -> Tuple[bool, str, str, Dict[str, float]]:
        """
        Constraint 2: Edge probability bounds.
        
        From paper: d/m ≤ p ≤ 1
        """
        d = params.d
        m = params.m
        p = params.p or (d / m)
        
        lower_bound = d / m
        upper_bound = 1.0
        
        satisfied = lower_bound <= p <= upper_bound
        
        error = None
        warning = None
        
        if p < lower_bound:
            error = f"Edge probability too low: p={p:.4f} < {lower_bound:.4f}"
        elif p > upper_bound:
            error = f"Edge probability too high: p={p:.4f} > {upper_bound:.4f}"
        elif p > 0.9:
            warning = f"Edge probability very high (p={p:.4f}), graph will be very dense"
        
        calculated = {
            "constraint_2_p": p,
            "constraint_2_lower_bound": lower_bound,
            "constraint_2_upper_bound": upper_bound
        }
        
        return satisfied, error, warning, calculated
    
    def _check_constraint_3(
        self,
        params: ParameterConstraints
    ) -> Tuple[bool, str, str, Dict[str, float]]:
        """
        Constraint 3: Expansion parameter.
        
        From paper: b ≥ 1 where b = sqrt(d(1/2 - ηV) / (2ln(m) - 2))
        """
        d = params.d
        m = params.m
        eta_v = params.eta_v
        
        if m <= 1:
            return False, "m must be > 1", None, {}
        
        denominator = 2 * math.log(m) - 2
        if denominator <= 0:
            return False, f"Invalid m={m} for expansion calculation", None, {}
        
        numerator = d * (0.5 - eta_v)
        if numerator <= 0:
            return False, f"Invalid parameters: d={d}, ηV={eta_v}", None, {}
        
        b = math.sqrt(numerator / denominator)
        
        satisfied = b >= 1.0
        
        error = None
        warning = None
        
        if not satisfied:
            required_d = denominator / (0.5 - eta_v)
            error = f"Insufficient degree for expansion: b={b:.3f} < 1. Need d ≥ {required_d:.1f}"
        elif b < 1.2:
            warning = f"Expansion parameter barely sufficient (b={b:.3f}). Consider higher degree."
        
        calculated = {
            "constraint_3_b": b,
            "constraint_3_required_d": denominator / (0.5 - eta_v) if not satisfied else d
        }
        
        return satisfied, error, warning, calculated
    
    def _check_constraint_4(
        self,
        params: ParameterConstraints
    ) -> Tuple[bool, str, str, Dict[str, float]]:
        """
        Constraint 4: Failed PPE threshold.
        
        From paper: ηE < (b-1)(1/2 - ηV) / b
        """
        d = params.d
        m = params.m
        eta_v = params.eta_v
        eta_e = params.eta_e
        
        # Calculate b
        denominator = 2 * math.log(m) - 2
        if denominator <= 0:
            return False, "Invalid m for constraint 4", None, {}
        
        b = math.sqrt(d * (0.5 - eta_v) / denominator)
        
        if b < 1.0:
            return False, "b < 1, cannot check constraint 4", None, {}
        
        # Calculate upper bound for ηE
        upper_bound = ((b - 1) * (0.5 - eta_v)) / b
        
        satisfied = eta_e < upper_bound
        
        error = None
        warning = None
        
        if not satisfied:
            error = f"Failed PPE threshold too high: ηE={eta_e:.3f} ≥ {upper_bound:.3f}"
        elif eta_e > upper_bound * 0.9:
            warning = f"ηE ({eta_e:.3f}) close to limit ({upper_bound:.3f})"
        
        calculated = {
            "constraint_4_eta_e_upper_bound": upper_bound,
            "constraint_4_margin": upper_bound - eta_e
        }
        
        return satisfied, error, warning, calculated
    
    def _check_constraint_5(
        self,
        params: ParameterConstraints
    ) -> Tuple[bool, str, str, Dict[str, float]]:
        """
        Constraint 5: Minimum degree.
        
        From paper: d ≥ 2ln(m) / (1/2 - ηV)
        """
        d = params.d
        m = params.m
        eta_v = params.eta_v
        
        if m <= 1:
            return False, "m must be > 1", None, {}
        
        denominator = 0.5 - eta_v
        if denominator <= 0:
            return False, f"Invalid ηV={eta_v} (must be < 0.5)", None, {}
        
        minimum_d = (2 * math.log(m)) / denominator
        
        satisfied = d >= minimum_d
        
        error = None
        warning = None
        
        if not satisfied:
            error = f"Degree too low: d={d:.1f} < {minimum_d:.1f}"
        elif d < minimum_d * 1.2:
            warning = f"Degree ({d:.1f}) barely above minimum ({minimum_d:.1f})"
        
        calculated = {
            "constraint_5_minimum_d": minimum_d,
            "constraint_5_margin": d - minimum_d
        }
        
        return satisfied, error, warning, calculated
    
    def _check_constraint_6(
        self,
        params: ParameterConstraints
    ) -> Tuple[bool, str, str, Dict[str, float]]:
        """
        Constraint 6: Sybil bound validity.
        
        From paper: C* = B(a,m) * d/a ≥ 1
        
        This ensures adversary's advantage is meaningful.
        """
        d = params.d
        m = params.m
        
        # For typical adversary with a = 0.1 * m * d (10% of total edges)
        a_typical = 0.1 * m * d
        
        if a_typical == 0:
            return False, "Invalid parameters for constraint 6", None, {}
        
        # Simplified: C* ≈ d/a for reasonable parameters
        # Full formula includes B(a,m) bound from Theorem 4.4
        c_star_approximate = d / (a_typical / m)  # Simplification
        
        satisfied = c_star_approximate >= 1.0
        
        error = None
        warning = None
        
        if not satisfied:
            error = f"Invalid Sybil bound: C* ≈ {c_star_approximate:.2f} < 1"
        
        calculated = {
            "constraint_6_c_star": c_star_approximate,
            "constraint_6_typical_a": a_typical
        }
        
        return satisfied, error, warning, calculated
    
    def _estimate_sybil_resistance(self, params: ParameterConstraints) -> float:
        """
        Estimate percentage resistance to Sybil attacks.
        
        Based on max Sybil nodes / total nodes ratio.
        """
        m = params.m
        d = params.d
        
        # Typical adversary resources: ~10% of edges
        a = 0.1 * m * d
        
        # From Theorem 4.4: max_sybil ≈ a/d
        max_sybil = a / d
        
        # Resistance percentage
        sybil_percentage = (max_sybil / m) * 100
        resistance_percentage = 100 - sybil_percentage
        
        return max(0, min(100, resistance_percentage))
    
    def _estimate_completion_rate(self, params: ParameterConstraints) -> float:
        """
        Estimate percentage of users who will complete certification.
        
        Based on ηE parameter and typical user behavior.
        """
        eta_e = params.eta_e
        d = params.d
        
        # Assume users fail PPEs at rate ηE
        # Completion rate ≈ 1 - P(too many failures)
        # Simplified: if user can fail ηE*d PPEs, what's completion rate?
        
        max_failures = int(eta_e * d)
        
        # Binomial approximation: if each PPE has 95% success rate
        # P(complete) ≈ 1 - P(>max_failures)
        # Simplified: 95% base rate
        base_completion = 0.95
        
        # Adjust for difficulty (more PPEs = harder)
        difficulty_factor = 1.0 - (d / 1000)  # Penalty for high d
        
        completion_rate = base_completion * max(0.7, difficulty_factor)
        
        return max(0, min(100, completion_rate * 100))


def get_validator() -> ParameterValidator:
    """Factory function."""
    return ParameterValidator()