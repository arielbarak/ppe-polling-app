#!/usr/bin/env python3
"""
PPE Enhancement Setup Script
Helps setup the new PPE protocol types in an existing deployment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.ppe_integration import (
    migrate_existing_polls_to_ppe_config, 
    validate_ppe_config,
    get_recommended_ppe_types
)
from app.models.ppe_types import PPEConfig


def setup_ppe_enhancement():
    """Main setup function."""
    print("Setting up PPE Protocol Enhancement...")
    
    db = SessionLocal()
    try:
        # Create PPE configs for existing polls
        print("\nStep 1: Migrating existing polls...")
        created_count = migrate_existing_polls_to_ppe_config(db)
        print(f"Created PPE configurations for {created_count} existing polls")
        
        # Validate all PPE configs
        print("\nStep 2: Validating PPE configurations...")
        configs = db.query(PPEConfig).all()
        total_issues = 0
        
        for config in configs:
            issues = validate_ppe_config(config)
            if issues:
                print(f"Poll {config.poll_id}:")
                for issue in issues:
                    print(f"   - {issue}")
                total_issues += len(issues)
        
        if total_issues == 0:
            print("All PPE configurations are valid!")
        else:
            print(f"Found {total_issues} configuration issues to review")
        
        # Display summary
        print(f"\nStep 3: Setup Summary")
        print(f"   - Total polls: {len(configs)}")
        print(f"   - PPE configs created: {created_count}")
        print(f"   - Configuration issues: {total_issues}")
        
        # Display available PPE types
        print(f"\nAvailable PPE Types:")
        print(f"   - Symmetric CAPTCHA: Both users solve CAPTCHAs")
        print(f"   - Proof of Storage: Verify access to cloud storage")  
        print(f"   - Computational: Proof-of-work puzzles")
        print(f"   - Social Distance: Reduced effort for social connections")
        
        print(f"\nPPE Enhancement setup complete!")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        raise
    finally:
        db.close()


def test_ppe_types():
    """Test PPE type implementations."""
    print("Testing PPE implementations...")
    
    from app.services.ppe.symmetric_captcha import SymmetricCaptchaPPE
    from app.services.ppe.proof_of_storage import ProofOfStoragePPE
    from app.services.ppe.computational import ComputationalPPE
    from app.models.ppe_types import PPEDifficulty
    
    try:
        # Test Symmetric CAPTCHA
        print("Testing Symmetric CAPTCHA...")
        captcha_ppe = SymmetricCaptchaPPE(difficulty=PPEDifficulty.EASY)
        challenge = captcha_ppe.generate_challenge("test_session", "user1", "user2")
        assert "challenge_data" in challenge
        print("Symmetric CAPTCHA working")
        
        # Test Proof of Storage
        print("Testing Proof of Storage...")
        storage_ppe = ProofOfStoragePPE(difficulty=PPEDifficulty.EASY)
        challenge = storage_ppe.generate_challenge("test_session", "user1", "user2")
        assert "challenge_data" in challenge
        print("Proof of Storage working")
        
        # Test Computational
        print("Testing Computational PPE...")
        comp_ppe = ComputationalPPE(difficulty=PPEDifficulty.EASY)
        challenge = comp_ppe.generate_challenge("test_session", "user1", "user2")
        assert "challenge_data" in challenge
        print("Computational PPE working")
        
        print("All PPE types tested successfully!")
        
    except Exception as e:
        print(f"PPE testing failed: {e}")
        raise


def show_integration_guide():
    """Show integration guide for existing code."""
    print("""
INTEGRATION GUIDE

To integrate the new PPE types into your existing poll creation:

1. Import the integration utilities:
   ```python
   from app.services.ppe_integration import create_default_ppe_config
   ```

2. Add to your poll creation function:
   ```python
   def create_poll(poll_data, db: Session):
       # Create poll as usual
       poll = Poll(**poll_data)
       db.add(poll)
       db.flush()  # Get poll.id
       
       # Create PPE configuration
       create_default_ppe_config(poll.id, db)
       
       db.commit()
       return poll
   ```

3. Use the new API endpoints in your frontend:
   ```javascript
   // Get available PPE types for a poll
   const types = await ppeService.getAvailableTypes(pollId);
   
   // Initiate a PPE with specific type
   const execution = await ppeService.initiatePPE({
       poll_id: pollId,
       prover_id: userId,
       verifier_id: partnerId,
       ppe_type: 'symmetric_captcha'
   });
   ```

4. Update your frontend components to use the new PPE selector:
   ```jsx
   import PPETypeSelector from './components/ppe/PPETypeSelector';
   import { usePPEExecution } from './hooks/usePPEExecution';
   ```

For complete examples, see:
   - backend/app/services/ppe_integration.py
   - frontend/src/components/ppe/
   - backend/tests/test_ppe_types.py
""")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            setup_ppe_enhancement()
        elif command == "test":
            test_ppe_types()
        elif command == "guide":
            show_integration_guide()
        else:
            print("Usage: python setup_ppe_enhancement.py [setup|test|guide]")
    else:
        print("PPE Enhancement Setup")
        print("Usage:")
        print("  python setup_ppe_enhancement.py setup  - Setup PPE for existing polls")
        print("  python setup_ppe_enhancement.py test   - Test PPE implementations")
        print("  python setup_ppe_enhancement.py guide  - Show integration guide")