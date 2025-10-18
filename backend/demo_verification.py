"""
Demo script to test the advanced verification functionality.

This script demonstrates:
1. Creating a poll with participants
2. Adding PPE certifications
3. Running comprehensive verification
4. Displaying verification results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.poll import Poll
from app.services.verification_service import verification_service


def create_demo_poll():
    """Create a demo poll with participants and certifications."""
    poll = Poll(
        id="demo-verification-poll",
        question="Which is the best verification algorithm?",
        options=["Spectral gap analysis", "Conductance calculation", "Sybil detection", "All of the above"]
    )
    
    # Add 10 participants
    for i in range(10):
        user_id = f"user{i}"
        poll.registrants[user_id] = {
            "kty": "EC",
            "x": f"mock_x_{i}",
            "y": f"mock_y_{i}"
        }
    
    # Create a connected certification graph
    # Each user certifies the next 3 users (cyclically)
    for i in range(10):
        user_id = f"user{i}"
        poll.ppe_certifications[user_id] = set()
        
        for j in range(1, 4):  # Certify next 3 users
            target_id = f"user{(i + j) % 10}"
            poll.ppe_certifications[user_id].add(target_id)
    
    # Add some votes
    for i in range(0, 8, 2):  # Even numbered users vote
        user_id = f"user{i}"
        poll.votes[user_id] = {
            "option": "All of the above",
            "signature": f"mock_signature_{i}",
            "publicKey": poll.registrants[user_id]
        }
    
    return poll


def run_verification_demo():
    """Run the verification demo."""
    print("🔍 Advanced Poll Verification Demo")
    print("=" * 50)
    
    # Create demo poll
    print("\n1️⃣ Creating demo poll...")
    poll = create_demo_poll()
    print(f"   ✅ Poll created with {len(poll.registrants)} participants")
    print(f"   ✅ {sum(len(certs) for certs in poll.ppe_certifications.values())} certifications added")
    print(f"   ✅ {len(poll.votes)} votes cast")
    
    # Run verification
    print("\n2️⃣ Running comprehensive verification...")
    result = verification_service.verify_poll_comprehensive(poll)
    
    # Display results
    print("\n3️⃣ Verification Results:")
    print(f"   Status: {'✅ VALID' if result.is_valid else '❌ INVALID'}")
    print(f"   Summary: {result._generate_summary()}")
    
    print("\n📊 Key Metrics:")
    for key, value in result.metrics.items():
        if isinstance(value, float):
            print(f"   • {key}: {value:.4f}")
        else:
            print(f"   • {key}: {value}")
    
    if result.errors:
        print("\n❌ Errors:")
        for error in result.errors:
            print(f"   • {error}")
    
    if result.warnings:
        print("\n⚠️ Warnings:")
        for warning in result.warnings:
            print(f"   • {warning}")
    
    print("\n🔬 Analysis Results:")
    for key, value in result.analysis.items():
        print(f"   • {key}: {type(value).__name__}")
        if key == "connectivity" and isinstance(value, dict):
            print(f"     - Connected: {value.get('is_connected', 'Unknown')}")
            print(f"     - Components: {value.get('num_components', 'Unknown')}")
        elif key == "degree_distribution" and isinstance(value, dict):
            print(f"     - Mean degree: {value.get('mean', 0):.2f}")
            print(f"     - Min/Max degree: {value.get('min', 0)}/{value.get('max', 0)}")
    
    print("\n✨ Verification complete!")
    return result


if __name__ == "__main__":
    try:
        result = run_verification_demo()
        print(f"\n🎉 Demo completed successfully. Poll is {'VALID' if result.is_valid else 'INVALID'}.")
    except Exception as e:
        print(f"\n💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()