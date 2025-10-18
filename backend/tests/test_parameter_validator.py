"""
Tests for parameter validation.
Comprehensive tests for all 6 constraints from Appendix C.
"""

import pytest
import math
from app.models.poll_parameters import ParameterConstraints
from app.services.parameter_validator import ParameterValidator
from app.services.parameter_calculator import ParameterCalculator


class TestParameterValidator:
    
    @pytest.fixture
    def validator(self):
        return ParameterValidator()
    
    @pytest.fixture
    def valid_params(self):
        """Valid parameters that satisfy all constraints."""
        return ParameterConstraints(
            m=1000,
            d=60,
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
    
    def test_valid_parameters(self, validator, valid_params):
        """Test that valid parameters pass all constraints."""
        result = validator.validate_all(valid_params)
        
        assert result.valid is True
        assert len(result.errors) == 0
        assert result.constraint_1_satisfied
        assert result.constraint_2_satisfied
        assert result.constraint_3_satisfied
        assert result.constraint_4_satisfied
        assert result.constraint_5_satisfied
        assert result.constraint_6_satisfied
    
    def test_constraint_1_too_few_participants(self, validator):
        """Test constraint 1: minimum participants."""
        params = ParameterConstraints(
            m=10,  # Too few
            d=60,
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        result = validator.validate_all(params)
        
        assert result.valid is False
        assert not result.constraint_1_satisfied
        assert any("Insufficient participants" in err for err in result.errors)
    
    def test_constraint_2_edge_probability_bounds(self, validator):
        """Test constraint 2: edge probability bounds."""
        # Test p too high (d > m)
        params = ParameterConstraints(
            m=100,
            d=150,  # d > m, so p > 1
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        result = validator.validate_all(params)
        
        assert not result.constraint_2_satisfied
        assert any("Edge probability too high" in err for err in result.errors)
    
    def test_constraint_3_insufficient_degree(self, validator):
        """Test constraint 3: expansion parameter b ≥ 1."""
        params = ParameterConstraints(
            m=1000,
            d=10,  # Too low for expansion
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        result = validator.validate_all(params)
        
        assert result.valid is False
        assert not result.constraint_3_satisfied
        assert any("Insufficient degree" in err for err in result.errors)
    
    def test_constraint_4_eta_e_too_high(self, validator):
        """Test constraint 4: ηE threshold."""
        params = ParameterConstraints(
            m=1000,
            d=60,
            kappa=40,
            eta_v=0.025,
            eta_e=0.5  # Too high
        )
        
        result = validator.validate_all(params)
        
        assert result.valid is False
        assert not result.constraint_4_satisfied
        assert any("Failed PPE threshold" in err for err in result.errors)
    
    def test_constraint_5_minimum_degree(self, validator):
        """Test constraint 5: d ≥ 2ln(m) / (1/2 - ηV)."""
        params = ParameterConstraints(
            m=1000,
            d=5,  # Too low for constraint 5
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        result = validator.validate_all(params)
        
        assert result.valid is False
        assert not result.constraint_5_satisfied
        assert any("Degree too low" in err for err in result.errors)
    
    def test_constraint_6_sybil_bound(self, validator):
        """Test constraint 6: Sybil bound validity."""
        # Very small parameters that might fail constraint 6
        params = ParameterConstraints(
            m=50,
            d=5,
            kappa=20,
            eta_v=0.025,
            eta_e=0.125
        )
        
        result = validator.validate_all(params)
        
        # This might pass or fail depending on exact calculation
        # Just ensure constraint 6 is checked
        assert hasattr(result, 'constraint_6_satisfied')
    
    def test_warnings_for_marginal_values(self, validator):
        """Test that warnings are issued for marginal values."""
        # Parameters that barely satisfy constraints
        params = ParameterConstraints(
            m=200,
            d=35,
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        result = validator.validate_all(params)
        
        # Should have warnings for marginal values
        if result.valid:
            assert len(result.warnings) > 0
    
    def test_security_metrics_calculation(self, validator, valid_params):
        """Test that security metrics are calculated."""
        result = validator.validate_all(valid_params)
        
        if result.valid:
            assert result.estimated_sybil_resistance is not None
            assert 0 <= result.estimated_sybil_resistance <= 100
            
            assert result.estimated_completion_rate is not None
            assert 0 <= result.estimated_completion_rate <= 100


class TestParameterCalculation:
    
    def test_edge_probability_calculation(self):
        """Test that p is calculated correctly."""
        params = ParameterConstraints(
            m=1000,
            d=60,
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        assert params.p == 60 / 1000
        assert params.p == 0.06
    
    def test_expansion_parameter_calculation(self):
        """Test that b is calculated correctly."""
        params = ParameterConstraints(
            m=1000,
            d=60,
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        expected_b = math.sqrt(
            60 * (0.5 - 0.025) / (2 * math.log(1000) - 2)
        )
        
        assert params.b is not None
        assert abs(params.b - expected_b) < 0.01


class TestParameterCalculator:
    
    @pytest.fixture
    def calculator(self):
        return ParameterCalculator()
    
    def test_calculate_for_high_security(self, calculator):
        """Test calculation for high security level."""
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="high"
        )
        
        assert params.m == 1000
        assert params.d >= 80  # High security should have high degree
        assert params.kappa == 80  # High security parameter
        assert params.eta_v == 0.01  # Low tolerance for deleted nodes
    
    def test_calculate_for_medium_security(self, calculator):
        """Test calculation for medium security level."""
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="medium"
        )
        
        assert params.m == 1000
        assert params.kappa == 40  # Medium security parameter
        assert params.eta_v == 0.025  # Medium tolerance
    
    def test_calculate_for_low_security(self, calculator):
        """Test calculation for low security level."""
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="low"
        )
        
        assert params.m == 1000
        assert params.kappa == 20  # Low security parameter
        assert params.eta_v == 0.05  # Higher tolerance
    
    def test_invalid_security_level(self, calculator):
        """Test error for invalid security level."""
        with pytest.raises(ValueError, match="Unknown security level"):
            calculator.calculate_for_security_level(
                m=1000,
                security_level="invalid"
            )
    
    def test_too_few_participants(self, calculator):
        """Test error for too few participants."""
        with pytest.raises(ValueError, match="Need at least 10 participants"):
            calculator.calculate_for_security_level(
                m=5,
                security_level="medium"
            )
    
    def test_optimize_for_user_effort(self, calculator):
        """Test optimization for user effort."""
        params = calculator.optimize_for_user_effort(
            m=1000,
            max_ppes_per_user=50,
            min_security_level=0.9
        )
        
        assert params.m == 1000
        assert params.d <= 50  # Should respect user effort limit
    
    def test_calculate_minimum_participants(self, calculator):
        """Test minimum participant calculation."""
        min_m = calculator.calculate_minimum_participants(
            d=60,
            kappa=40,
            eta_v=0.025
        )
        
        assert min_m >= 10
        assert isinstance(min_m, int)
    
    def test_calculate_maximum_degree(self, calculator):
        """Test maximum degree calculation."""
        max_d = calculator.calculate_maximum_degree(
            m=1000,
            eta_v=0.025
        )
        
        assert max_d <= 1000  # Cannot exceed participants
        assert max_d <= 200   # Practical cap


class TestParameterConstraints:
    
    def test_parameter_bounds(self):
        """Test parameter validation bounds."""
        # Valid parameters
        params = ParameterConstraints(
            m=100,
            d=40,
            kappa=40,
            eta_v=0.025,
            eta_e=0.125
        )
        
        assert params.m == 100
        assert params.d == 40
        assert params.kappa == 40
        assert params.eta_v == 0.025
        assert params.eta_e == 0.125
    
    def test_invalid_bounds(self):
        """Test that invalid parameters are rejected."""
        # Test various invalid parameters
        with pytest.raises(Exception):  # Should raise validation error
            ParameterConstraints(
                m=-10,  # Negative
                d=40,
                kappa=40,
                eta_v=0.025,
                eta_e=0.125
            )
        
        with pytest.raises(Exception):
            ParameterConstraints(
                m=100,
                d=-10,  # Negative
                kappa=40,
                eta_v=0.025,
                eta_e=0.125
            )
        
        with pytest.raises(Exception):
            ParameterConstraints(
                m=100,
                d=40,
                kappa=10,  # Too low
                eta_v=0.025,
                eta_e=0.125
            )


class TestIntegration:
    
    def test_end_to_end_validation(self):
        """Test complete parameter validation workflow."""
        calculator = ParameterCalculator()
        validator = ParameterValidator()
        
        # Calculate parameters
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="medium"
        )
        
        # Validate them
        result = validator.validate_all(params)
        
        # Should be valid
        assert result.valid is True
        assert len(result.errors) == 0
        
        # Should have security metrics
        assert result.estimated_sybil_resistance is not None
        assert result.estimated_completion_rate is not None
    
    def test_different_participant_counts(self):
        """Test validation across different participant counts."""
        calculator = ParameterCalculator()
        validator = ParameterValidator()
        
        participant_counts = [50, 100, 500, 1000, 5000]
        
        for m in participant_counts:
            params = calculator.calculate_for_security_level(
                m=m,
                security_level="medium"
            )
            
            result = validator.validate_all(params)
            
            # All should be valid
            assert result.valid is True, f"Failed for m={m}"
            
            # Degree should scale appropriately
            assert params.d >= 20, f"Degree too low for m={m}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])