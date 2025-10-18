"""
Performance benchmarks for the system.
"""

import pytest
import time
import statistics
from tests.simulation.user_simulator import SimulatedUser


@pytest.mark.asyncio
async def test_registration_performance():
    """Benchmark registration performance."""
    times = []
    
    for i in range(10):
        user = SimulatedUser(f"perf_user_{i}")
        user.generate_keypair()
        
        start = time.time()
        await user.register_for_poll("perf_poll_001", solve_captcha=True)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    print(f"\nAverage registration time: {avg_time:.3f}s")
    
    # Registration should complete within reasonable time
    assert avg_time < 5.0, "Registration should be fast"


@pytest.mark.asyncio
async def test_voting_performance():
    """Benchmark voting performance."""
    user = SimulatedUser("perf_user_vote")
    user.generate_keypair()
    
    await user.register_for_poll("perf_poll_002", solve_captcha=True)
    
    times = []
    for i in range(10):
        start = time.time()
        await user.vote("perf_poll_002", f"Option {i % 3}")
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg_time = statistics.mean(times)
    print(f"\nAverage voting time: {avg_time:.3f}s")
    
    assert avg_time < 1.0, "Voting should be very fast"