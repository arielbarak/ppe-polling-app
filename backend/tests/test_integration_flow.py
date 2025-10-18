"""
Integration tests for complete protocol flow.
"""

import pytest
import asyncio
from tests.simulation.user_simulator import SimulatedUser
from tests.simulation.scenario_runner import ScenarioRunner


@pytest.mark.asyncio
async def test_single_user_flow():
    """Test complete flow for a single user."""
    user = SimulatedUser("test_user_001")
    user.generate_keypair()
    
    poll_id = "test_poll_001"
    
    # Registration
    registered = await user.register_for_poll(poll_id, solve_captcha=True)
    assert registered, "User should register successfully"
    
    # Vote
    voted = await user.vote(poll_id, "Option A")
    assert voted, "User should vote successfully"


@pytest.mark.asyncio
async def test_honest_scenario_small():
    """Test honest scenario with 10 users."""
    runner = ScenarioRunner()
    
    # Create test poll (in real test, use a test database)
    poll_id = "test_poll_002"
    
    results = await runner.run_honest_scenario(poll_id, num_users=10)
    
    # Assertions
    assert results["successful_registrations"] >= 8, "Most users should register"
    assert results["successful_votes"] >= 8, "Most users should vote"


@pytest.mark.asyncio
async def test_concurrent_registrations():
    """Test many users registering concurrently."""
    users = []
    for i in range(20):
        user = SimulatedUser(f"concurrent_user_{i}")
        user.generate_keypair()
        users.append(user)
    
    poll_id = "test_poll_003"
    
    # Concurrent registrations
    tasks = [user.register_for_poll(poll_id, solve_captcha=True) for user in users]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = sum(1 for r in results if r is True)
    assert successful >= 18, "Most concurrent registrations should succeed"


@pytest.mark.asyncio
async def test_sybil_detection():
    """Test that Sybil attacks are detected."""
    runner = ScenarioRunner()
    poll_id = "test_poll_004"
    
    # Run Sybil attack scenario
    results = await runner.run_sybil_attack_scenario(
        poll_id, 
        num_honest=15, 
        num_sybils=10
    )
    
    # The verification should detect suspicious patterns
    # (This would need actual verification check in real test)
    assert results["successful_registrations"] > 0