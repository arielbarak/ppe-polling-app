#!/usr/bin/env python3
"""
Test script to verify PPE implementation works correctly.
"""

from app.utils.ppe_utils import (
    generate_secret_key,
    generate_challenge_with_secret,
    verify_challenge_generation,
    create_commitment,
    verify_commitment,
    create_ppe_session_id,
    verify_solution_correctness
)
from app.services.ppe_service import PPEService, PPEState

def test_ppe_utils():
    print("=== Testing PPE Utilities ===")
    
    # Test secret generation
    secret1 = generate_secret_key()
    secret2 = generate_secret_key()
    print(f"✓ Secrets are unique: {secret1 != secret2}")
    
    # Test deterministic challenge generation
    session_id = "test_session"
    challenge1, solution1 = generate_challenge_with_secret(secret1, session_id)
    challenge2, solution2 = generate_challenge_with_secret(secret1, session_id)
    print(f"✓ Challenge generation is deterministic: {solution1 == solution2}")
    print(f"  Challenge: {challenge1}")
    print(f"  Solution: {solution1}")
    
    # Test challenge verification
    verified = verify_challenge_generation(secret1, session_id, challenge1, solution1)
    print(f"✓ Challenge verification works: {verified}")
    
    # Test commitment scheme
    test_solution = "test123"
    commitment, nonce = create_commitment(test_solution)
    commitment_valid = verify_commitment(test_solution, nonce, commitment)
    commitment_invalid = verify_commitment("wrong", nonce, commitment)
    print(f"✓ Commitment scheme works: {commitment_valid and not commitment_invalid}")
    
    # Test session ID generation
    user1, user2, poll_id = "user1", "user2", "poll123"
    session1 = create_ppe_session_id(user1, user2, poll_id)
    session2 = create_ppe_session_id(user2, user1, poll_id)  # Reverse order
    print(f"✓ Session ID is order-independent: {session1 == session2}")
    
    # Test solution verification
    test_challenge = "a b c 1 2 3"
    correct = verify_solution_correctness(test_challenge, "abc123")
    incorrect = verify_solution_correctness(test_challenge, "wrong")
    print(f"✓ Solution verification works: {correct and not incorrect}")

def test_ppe_service():
    print("\n=== Testing PPE Service ===")
    
    service = PPEService()
    
    # Test session creation
    session = service.create_session("user1", "user2", "poll1", "session1")
    print(f"✓ Session created: {session.session_id == 'session1'}")
    print(f"✓ Initial states are idle: {session.user1_state == PPEState.IDLE}")
    
    # Test state management
    session.set_user_state("user1", PPEState.CHALLENGE_SENT)
    state_updated = session.get_user_state("user1") == PPEState.CHALLENGE_SENT
    print(f"✓ State management works: {state_updated}")
    
    # Test both users state check
    both_idle = session.both_users_reached_state(PPEState.IDLE)
    session.set_user_state("user2", PPEState.CHALLENGE_SENT)
    both_challenge_sent = session.both_users_reached_state(PPEState.CHALLENGE_SENT)
    print(f"✓ Both users state check: {not both_idle and both_challenge_sent}")
    
    # Test session retrieval
    retrieved = service.get_session("session1")
    print(f"✓ Session retrieval works: {retrieved is not None}")

def test_full_ppe_protocol_simulation():
    print("\n=== Simulating Full PPE Protocol ===")
    
    # Simulate two users doing PPE
    user1_id = "user1"
    user2_id = "user2"
    poll_id = "poll123"
    
    # Step 1: Create session
    session_id = create_ppe_session_id(user1_id, user2_id, poll_id)
    print(f"1. Session created: {session_id}")
    
    # Step 2: Both users generate challenges
    user1_secret = generate_secret_key()
    user2_secret = generate_secret_key()
    
    user1_challenge, user1_solution = generate_challenge_with_secret(user1_secret, session_id)
    user2_challenge, user2_solution = generate_challenge_with_secret(user2_secret, session_id)
    
    print(f"2. User1 challenge: {user1_challenge}")
    print(f"   User2 challenge: {user2_challenge}")
    
    # Step 3: Users solve each other's challenges and create commitments
    # User1 solves User2's challenge
    user1_solution_to_user2 = user2_challenge.replace(' ', '')
    user1_commitment, user1_nonce = create_commitment(user1_solution_to_user2)
    
    # User2 solves User1's challenge  
    user2_solution_to_user1 = user1_challenge.replace(' ', '')
    user2_commitment, user2_nonce = create_commitment(user2_solution_to_user1)
    
    print(f"3. Commitments created and exchanged")
    
    # Step 4: Reveal secrets and verify
    # User1 verifies User2's challenge was generated correctly
    user2_challenge_valid = verify_challenge_generation(user2_secret, session_id, user2_challenge, user2_solution)
    
    # User2 verifies User1's challenge was generated correctly
    user1_challenge_valid = verify_challenge_generation(user1_secret, session_id, user1_challenge, user1_solution)
    
    # Verify commitments
    user1_commitment_valid = verify_commitment(user1_solution_to_user2, user1_nonce, user1_commitment)
    user2_commitment_valid = verify_commitment(user2_solution_to_user1, user2_nonce, user2_commitment)
    
    # Verify solutions are correct
    user1_solution_correct = verify_solution_correctness(user2_challenge, user1_solution_to_user2)
    user2_solution_correct = verify_solution_correctness(user1_challenge, user2_solution_to_user1)
    
    all_valid = all([
        user1_challenge_valid, user2_challenge_valid,
        user1_commitment_valid, user2_commitment_valid,
        user1_solution_correct, user2_solution_correct
    ])
    
    print(f"4. All verifications passed: {all_valid}")
    
    if all_valid:
        print("PPE Protocol completed successfully!")
        print("Users can now exchange signatures and record certification")
    else:
        print("PPE Protocol failed verification")

if __name__ == "__main__":
    test_ppe_utils()
    test_ppe_service()
    test_full_ppe_protocol_simulation()
    print("\n=== PPE Implementation Test Complete ===")