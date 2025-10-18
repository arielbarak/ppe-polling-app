"""
End-to-end integration test for voting flow.
Tests complete flow: Register → Certify → Vote
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services.state_machine import StateMachine, PollPhase
from app.services.ppe_assignment_service import PPEAssignmentService
from app.models.user import Poll, User
from app.models.certification_state import CertificationState


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.mark.integration
class TestVotingFlowIntegration:
    
    def test_complete_voting_flow(self, test_db):
        """
        INTEGRATION TEST for Issue #7.
        Tests complete flow from registration to voting.
        """
        # 1. Create poll
        poll = Poll(
            id="integration_poll",
            question="Test integration question?",
            phase=PollPhase.REGISTRATION,
            expected_degree=4,
            eta_e=0.125,
            session_id="test_session_123"
        )
        test_db.add(poll)
        test_db.commit()
        
        # 2. Register users
        num_users = 10
        for i in range(num_users):
            user = User(
                id=f"user_{i}",
                poll_id=poll.id,
                registration_order=i
            )
            test_db.add(user)
        test_db.commit()
        
        print(f"\n✓ Registered {num_users} users")
        
        # 3. Close registration and assign PPEs
        poll.phase = PollPhase.CERTIFICATION
        test_db.commit()
        
        assignment_service = PPEAssignmentService(test_db)
        assignments = assignment_service.assign_ppe_partners(poll.id)
        
        print(f"✓ Assigned PPE partners to {len(assignments)} users")
        
        # 4. Simulate PPE completions
        for user_id, partners in assignments.items():
            cert_state = test_db.query(CertificationState).filter_by(
                user_id=user_id,
                poll_id=poll.id
            ).first()
            
            # Complete all required PPEs
            for partner_id in partners:
                ppe_id = f"ppe_{user_id}_{partner_id}"
                cert_state.add_completed_ppe(ppe_id, partner_id, f"sig_{ppe_id}")
            
            test_db.commit()
            
            print(f"  ✓ User {user_id} completed {len(partners)} PPEs → "
                  f"Certified: {cert_state.is_certified}")
        
        # 5. Transition to voting phase
        state_machine = StateMachine(test_db)
        num_certified, num_excluded = state_machine.transition_to_voting(poll.id)
        
        print(f"✓ Transitioned to voting: {num_certified} certified, {num_excluded} excluded")
        
        # 6. Verify all certified users can vote
        certified_users = test_db.query(CertificationState).filter_by(
            poll_id=poll.id,
            is_certified=True
        ).all()
        
        for cert_state in certified_users:
            can_vote, reason = state_machine.can_user_vote(
                cert_state.user_id,
                poll.id
            )
            
            assert can_vote is True, (
                f"Certified user {cert_state.user_id} should be able to vote, "
                f"but got: {reason}"
            )
            
            print(f"  ✓ User {cert_state.user_id} CAN VOTE")
        
        # 7. Cast votes
        for cert_state in certified_users:
            success = state_machine.record_vote(cert_state.user_id, poll.id)
            assert success is True
            print(f"  ✓ User {cert_state.user_id} voted")
        
        # 8. Verify cannot vote twice
        for cert_state in certified_users:
            can_vote, reason = state_machine.can_user_vote(
                cert_state.user_id,
                poll.id
            )
            
            assert can_vote is False
            assert "already voted" in reason.lower()
            print(f"  ✓ User {cert_state.user_id} correctly blocked from double-voting")
        
        print("\n✅ INTEGRATION TEST PASSED: Complete voting flow works!")
    
    def test_ppe_assignment_algorithm(self, test_db):
        """Test PPE assignment algorithm works correctly."""
        # Create poll with specific parameters
        poll = Poll(
            id="assignment_test",
            question="Assignment test?",
            phase=PollPhase.CERTIFICATION,
            expected_degree=6,  # Each user should get ~6 partners
            eta_e=0.125,
            session_id="assignment_test_session"
        )
        test_db.add(poll)
        
        # Create 20 users
        num_users = 20
        for i in range(num_users):
            user = User(
                id=f"user_{i}",
                poll_id=poll.id,
                registration_order=i
            )
            test_db.add(user)
        test_db.commit()
        
        # Assign partners
        assignment_service = PPEAssignmentService(test_db)
        assignments = assignment_service.assign_ppe_partners(poll.id)
        
        # Verify assignments
        assert len(assignments) == num_users
        
        # Check that assignments are symmetric (if A has B, then B has A)
        for user_id, partners in assignments.items():
            for partner_id in partners:
                assert user_id in assignments[partner_id], (
                    f"Assignment not symmetric: {user_id} has {partner_id} "
                    f"but {partner_id} doesn't have {user_id}"
                )
        
        # Check that users don't assign to themselves
        for user_id, partners in assignments.items():
            assert user_id not in partners, f"User {user_id} assigned to themselves"
        
        print(f"✓ PPE assignment algorithm test passed for {num_users} users")
    
    def test_certification_state_persistence(self, test_db):
        """Test that certification state persists correctly (Issue #5)."""
        # Create poll and user
        poll = Poll(
            id="persistence_test",
            question="Persistence test?",
            phase=PollPhase.CERTIFICATION,
            expected_degree=5
        )
        test_db.add(poll)
        
        user = User(
            id="persistence_user",
            poll_id=poll.id,
            registration_order=0
        )
        test_db.add(user)
        test_db.commit()
        
        # Create certification state
        cert_state = CertificationState(
            user_id=user.id,
            poll_id=poll.id,
            required_ppes=5,
            completed_ppes=2,
            failed_ppes=1,
            max_allowed_failures=1,
            assigned_ppe_partners=["user_1", "user_2", "user_3", "user_4", "user_5"],
            completed_ppe_ids=["ppe_1", "ppe_2"],
            failed_ppe_ids=["ppe_3"]
        )
        test_db.add(cert_state)
        test_db.commit()
        
        # Simulate page refresh by querying state again
        retrieved_state = test_db.query(CertificationState).filter_by(
            user_id=user.id,
            poll_id=poll.id
        ).first()
        
        assert retrieved_state is not None
        assert retrieved_state.required_ppes == 5
        assert retrieved_state.completed_ppes == 2
        assert retrieved_state.failed_ppes == 1
        assert len(retrieved_state.assigned_ppe_partners) == 5
        assert len(retrieved_state.completed_ppe_ids) == 2
        assert len(retrieved_state.failed_ppe_ids) == 1
        
        # Test computed properties
        assert retrieved_state.remaining_ppes == 3
        assert retrieved_state.completion_percentage == 40.0
        assert retrieved_state.can_still_certify is True  # 1 failure = max allowed
        
        print("✓ Certification state persistence test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])