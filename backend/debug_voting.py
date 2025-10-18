"""
Debugging script for Issue #7: Cannot reach voting state.
Run this to diagnose exactly where the voting flow is breaking.
"""

from app.database import SessionLocal
from app.services.state_machine import StateMachine, PollPhase
from app.models.user import Poll, User
from app.models.certification_state import CertificationState


def debug_voting_flow(user_id: str, poll_id: str):
    """
    Comprehensive debugging for voting flow.
    """
    db = SessionLocal()
    sm = StateMachine(db)
    
    print("=" * 60)
    print("VOTING FLOW DEBUG REPORT")
    print("=" * 60)
    
    # Check poll exists and phase
    poll = db.query(Poll).filter_by(id=poll_id).first()
    if not poll:
        print("PROBLEM: Poll not found")
        db.close()
        return
    
    print(f"\n1. POLL STATUS")
    print(f"   Poll ID: {poll.id}")
    print(f"   Phase: {poll.phase}")
    print(f"   Expected degree: {getattr(poll, 'expected_degree', 'Not set')}")
    
    if poll.phase != PollPhase.VOTING:
        print(f"   WARNING: Poll is in {poll.phase}, not VOTING")
    else:
        print("   Poll is in VOTING phase")
    
    # Check user exists and is registered
    user = db.query(User).filter_by(id=user_id, poll_id=poll_id).first()
    if not user:
        print("\nPROBLEM: User not registered for this poll")
        db.close()
        return
    
    print(f"\n2. USER STATUS")
    print(f"   User ID: {user.id}")
    print(f"   Registration order: {getattr(user, 'registration_order', 'Not set')}")
    print("   User is registered")
    
    # Check certification state
    cert_state = db.query(CertificationState).filter_by(
        user_id=user_id,
        poll_id=poll_id
    ).first()
    
    if not cert_state:
        print("\nPROBLEM: No certification state found")
        print("   This means PPE assignments were never created")
        db.close()
        return
    
    print(f"\n3. CERTIFICATION STATE")
    print(f"   Required PPEs: {cert_state.required_ppes}")
    print(f"   Completed: {cert_state.completed_ppes}")
    print(f"   Failed: {cert_state.failed_ppes}")
    print(f"   Max allowed failures: {cert_state.max_allowed_failures}")
    print(f"   Is certified: {cert_state.is_certified}")
    print(f"   Is excluded: {cert_state.is_excluded}")
    print(f"   Has voted: {cert_state.has_voted}")
    
    # Check certification logic
    if cert_state.completed_ppes < cert_state.required_ppes:
        print(f"   WARNING: Not enough PPEs completed")
        print(f"      Need {cert_state.required_ppes - cert_state.completed_ppes} more")
    elif not cert_state.is_certified:
        print("   PROBLEM: Enough PPEs completed but is_certified=False")
        print("      This is a bug in update_certification_status()")
    else:
        print("   User is certified")
    
    if cert_state.failed_ppes > cert_state.max_allowed_failures:
        print(f"   PROBLEM: Too many failures")
        print(f"      Failed {cert_state.failed_ppes}, max {cert_state.max_allowed_failures}")
        print(f"      User is excluded: {cert_state.is_excluded}")
    
    # Check state machine logic
    print(f"\n4. STATE MACHINE CHECK")
    
    user_state, reason = sm.get_user_state(user_id, poll_id)
    print(f"   Current state: {user_state}")
    if reason:
        print(f"   Reason: {reason}")
    
    can_vote, vote_reason = sm.can_user_vote(user_id, poll_id)
    print(f"   Can vote: {can_vote}")
    if vote_reason:
        print(f"   Reason: {vote_reason}")
    
    # Diagnosis
    print(f"\n5. DIAGNOSIS")
    
    if can_vote:
        print("   USER CAN VOTE!")
        print("   If voting still fails, check:")
        print("      - Frontend authorization header")
        print("      - Vote endpoint /api/polls/{poll_id}/vote")
        print("      - Check browser console for errors")
    else:
        print("   USER CANNOT VOTE")
        print(f"   Reason: {vote_reason}")
        print("\n   CHECKLIST:")
        
        checks = [
            (poll.phase == PollPhase.VOTING, "Poll in VOTING phase"),
            (cert_state is not None, "Certification state exists"),
            (cert_state.completed_ppes >= cert_state.required_ppes, "Enough PPEs completed"),
            (cert_state.is_certified, "User is certified"),
            (not cert_state.is_excluded, "User not excluded"),
            (not cert_state.has_voted, "User hasn't voted yet"),
        ]
        
        for check, description in checks:
            status = "OK" if check else "ERROR"
            print(f"      {status} {description}")
    
    print("\n" + "=" * 60)
    db.close()


def quick_poll_status(poll_id: str):
    """Quick overview of poll status."""
    db = SessionLocal()
    
    poll = db.query(Poll).filter_by(id=poll_id).first()
    if not poll:
        print(f"Poll {poll_id} not found")
        db.close()
        return
    
    users = db.query(User).filter_by(poll_id=poll_id).count()
    cert_states = db.query(CertificationState).filter_by(poll_id=poll_id).all()
    
    certified = sum(1 for cs in cert_states if cs.is_certified)
    excluded = sum(1 for cs in cert_states if cs.is_excluded)
    voted = sum(1 for cs in cert_states if cs.has_voted)
    
    print(f"\nPOLL OVERVIEW: {poll_id}")
    print(f"   Phase: {poll.phase}")
    print(f"   Total users: {users}")
    print(f"   Certification states: {len(cert_states)}")
    print(f"   Certified users: {certified}")
    print(f"   Excluded users: {excluded}")
    print(f"   Users who voted: {voted}")
    
    if poll.phase == PollPhase.VOTING and certified > 0:
        print(f"   TARGET: {certified} users should be able to vote")
    
    db.close()


def list_all_polls():
    """List all polls in the database."""
    db = SessionLocal()
    
    polls = db.query(Poll).all()
    
    if not polls:
        print("No polls found in database")
        db.close()
        return
    
    print("\nALL POLLS:")
    for poll in polls:
        user_count = db.query(User).filter_by(poll_id=poll.id).count()
        print(f"   {poll.id} - {poll.phase} - {user_count} users")
    
    db.close()


def fix_certification_states(poll_id: str):
    """
    Fix certification states that may have incorrect is_certified flags.
    """
    db = SessionLocal()
    
    cert_states = db.query(CertificationState).filter_by(poll_id=poll_id).all()
    
    fixed_count = 0
    for cert_state in cert_states:
        old_certified = cert_state.is_certified
        cert_state.update_certification_status()
        
        if old_certified != cert_state.is_certified:
            fixed_count += 1
            print(f"Fixed user {cert_state.user_id}: {old_certified} → {cert_state.is_certified}")
    
    if fixed_count > 0:
        db.commit()
        print(f"Fixed {fixed_count} certification states")
    else:
        print("No certification states needed fixing")
    
    db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("USAGE:")
        print("  python debug_voting.py list                    # List all polls")
        print("  python debug_voting.py status <poll_id>        # Quick poll overview")
        print("  python debug_voting.py debug <user_id> <poll_id>  # Full debug")
        print("  python debug_voting.py fix <poll_id>           # Fix certification states")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        list_all_polls()
    elif command == "status" and len(sys.argv) >= 3:
        quick_poll_status(sys.argv[2])
    elif command == "debug" and len(sys.argv) >= 4:
        debug_voting_flow(sys.argv[2], sys.argv[3])
    elif command == "fix" and len(sys.argv) >= 3:
        fix_certification_states(sys.argv[2])
    else:
        print("Invalid command or missing arguments")
        sys.exit(1)