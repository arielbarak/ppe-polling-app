"""
Tests for parameter calculation service.
"""

import pytest
from app.services.parameter_calculator import ParameterCalculator
from app.models.poll_parameters import ParameterConstraints


class TestParameterCalculator:
    
    @pytest.fixture
    def calculator(self):
        return ParameterCalculator()
    
    def test_high_security_parameters(self, calculator):
        """Test high security level calculations."""
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="high"
        )
        
        # High security should have:
        # - High degree (80+)
        # - High security parameter (80)
        # - Low tolerance for deleted nodes (0.01)
        # - Low tolerance for failed PPEs (0.1)
        
        assert params.m == 1000
        assert params.d >= 80
        assert params.kappa == 80
        assert params.eta_v == 0.01
        assert params.eta_e <= 0.1
        
        # Should automatically calculate p and b
        assert params.p is not None
        assert params.b is not None
    
    def test_medium_security_parameters(self, calculator):
        """Test medium security level calculations."""
        params = calculator.calculate_for_security_level(
            m=500,
            security_level="medium"
        )
        
        assert params.m == 500
        assert params.kappa == 40
        assert params.eta_v == 0.025
        assert params.eta_e <= 0.125
    
    def test_low_security_parameters(self, calculator):
        """Test low security level calculations."""
        params = calculator.calculate_for_security_level(
            m=200,
            security_level="low"
        )
        
        assert params.m == 200
        assert params.kappa == 20
        assert params.eta_v == 0.05
        assert params.eta_e <= 0.15
    
    def test_custom_constraints_override(self, calculator):
        """Test that custom constraints override defaults."""
        custom_constraints = {
            'd': 100,
            'kappa': 60,
            'eta_v': 0.02,
            'eta_e': 0.1
        }
        
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="medium",
            custom_constraints=custom_constraints
        )
        
        # Should use custom values where applicable
        assert params.kappa == 60  # Custom override
        assert params.eta_v == 0.02  # Custom override
        
        # d might be adjusted upward to satisfy constraints
        assert params.d >= 100
    
    def test_constraint_5_enforcement(self, calculator):
        """Test that constraint 5 (minimum degree) is enforced."""
        # For small m, constraint 5 requires higher d
        params = calculator.calculate_for_security_level(
            m=50,
            security_level="low"
        )
        
        # Calculate what constraint 5 requires
        import math
        min_d_required = (2 * math.log(50)) / (0.5 - 0.05)
        
        # Should meet or exceed constraint 5 requirement
        assert params.d >= min_d_required * 1.1  # With 10% margin
    
    def test_constraint_3_enforcement(self, calculator):
        """Test that constraint 3 (expansion parameter) is enforced."""
        params = calculator.calculate_for_security_level(
            m=1000,
            security_level="medium"
        )
        
        # Calculate expansion parameter
        import math
        denominator = 2 * math.log(params.m) - 2
        b = math.sqrt(params.d * (0.5 - params.eta_v) / denominator)
        
        # Should satisfy b >= 1
        assert b >= 1.0
    
    def test_effort_optimization(self, calculator):
        """Test optimization for user effort."""
        params = calculator.optimize_for_user_effort(
            m=1000,
            max_ppes_per_user=50,
            min_security_level=0.9
        )
        
        assert params.m == 1000
        # Should try to keep d <= 50 if constraints allow
        # But may be higher if constraints require it
        assert params.d >= 20  # Reasonable minimum
    
    def test_minimum_participants_calculation(self, calculator):
        """Test minimum participants calculation."""
        # For a given degree, what's minimum m?
        min_m = calculator.calculate_minimum_participants(
            d=60,
            kappa=40,
            eta_v=0.025
        )
        
        assert min_m >= 10
        assert isinstance(min_m, int)
        
        # Should satisfy constraint 1
        import math
        rhs = 40 + (0.025 * min_m + 2) * math.log(min_m) + 0.025 * min_m
        assert min_m >= rhs
    
    def test_maximum_degree_calculation(self, calculator):
        """Test maximum degree calculation."""
        max_d = calculator.calculate_maximum_degree(
            m=1000,
            eta_v=0.025
        )
        
        # Should be reasonable
        assert max_d <= 1000  # Can't exceed participants
        assert max_d <= 200   # Practical limit
        assert max_d >= 20    # Reasonable minimum
    
    def test_small_participant_counts(self, calculator):
        """Test calculations with small participant counts."""
        params = calculator.calculate_for_security_level(
            m=20,  # Very small
            security_level="low"
        )
        
        assert params.m == 20
        # Should still satisfy all constraints
        assert params.d >= 10  # Reasonable minimum
        assert params.kappa >= 20
    
    def test_large_participant_counts(self, calculator):
        """Test calculations with large participant counts."""
        params = calculator.calculate_for_security_level(
            m=10000,  # Very large
            security_level="medium"
        )
        
        assert params.m == 10000
        # Degree should scale with log(m)
        assert params.d >= 50
        assert params.d <= 200  # But not excessive
    
    def test_invalid_inputs(self, calculator):
        """Test error handling for invalid inputs."""
        # Too few participants
        with pytest.raises(ValueError):
            calculator.calculate_for_security_level(
                m=5,  # Below minimum
                security_level="medium"
            )
        
        # Invalid security level
        with pytest.raises(ValueError):
            calculator.calculate_for_security_level(
                m=100,
                security_level="invalid"
            )
    
    def test_parameter_consistency(self, calculator):
        """Test that calculated parameters are internally consistent."""
        for security_level in ["high", "medium", "low"]:
            for m in [50, 100, 500, 1000, 5000]:
                try:
                    params = calculator.calculate_for_security_level(
                        m=m,
                        security_level=security_level
                    )
                    
                    # Basic consistency checks
                    assert params.m == m
                    assert params.d > 0
                    assert params.kappa > 0
                    assert 0 < params.eta_v < 0.5
                    assert 0 < params.eta_e < 0.5
                    assert params.p == params.d / params.m
                    
                    # p should be reasonable
                    assert 0 < params.p <= 1
                    
                except Exception as e:
                    pytest.fail(f"Failed for m={m}, level={security_level}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])