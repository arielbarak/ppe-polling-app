# PPE Plugin System - Developer Guide

## Overview

The PPE (Proof of Private Effort) plugin system allows you to add new challenge types without modifying core protocol logic.

## Creating a New PPE Type

### Step 1: Implement BasePPE

Create a new file in `backend/app/ppe/` (e.g., `my_ppe.py`):

```python
from .base import BasePPE, PPEType, PPEDifficulty
from typing import Tuple, Any

class MyCustomPPE(BasePPE):
    def get_type(self) -> PPEType:
        # Add your type to PPEType enum first
        return PPEType.MY_CUSTOM_TYPE
    
    def generate_challenge_with_secret(self, secret: str, session_id: str) -> Tuple[Any, str]:
        # Generate your challenge deterministically
        challenge_data = "..."  # Your challenge format
        solution = "..."        # Correct solution
        return challenge_data, solution
    
    def verify_challenge_generation(self, secret: str, session_id: str, 
                                    challenge_data: Any, solution: str) -> bool:
        # Verify challenge was generated correctly
        regenerated, regenerated_sol = self.generate_challenge_with_secret(secret, session_id)
        return regenerated_sol == solution
    
    def verify_solution(self, challenge_data: Any, solution: str) -> bool:
        # Verify solution is correct
        # Your verification logic
        return True  # or False
    
    def estimate_effort(self) -> float:
        # Return estimated seconds to solve
        return 15.0
```

### Step 2: Register Your PPE

In `backend/app/ppe/factory.py`, add to `_register_builtin()`:

```python
from .my_ppe import MyCustomPPE

self.register(
    MyCustomPPE,
    PPEMetadata(
        ppe_type=PPEType.MY_CUSTOM_TYPE,
        name="My Custom PPE",
        description="Description of what this does",
        requires_human=True,  # or False if automated
        supports_batch=False,
        client_library_required=False
    )
)
```

### Step 3: Client-Side Handler

Create `frontend/src/ppe/MyCustomHandler.js`:

```javascript
import { BasePPEHandler } from './BasePPEHandler';

export class MyCustomHandler extends BasePPEHandler {
  constructor(difficulty = 'medium') {
    super('my_custom_type', difficulty);
  }

  async generateChallengeWithSecret(secret, sessionId) {
    // Must match server-side generation
    return { challengeData: "...", solution: "..." };
  }

  async verifyChallengeGeneration(secret, sessionId, challengeData, solution) {
    // Verify challenge
    return true;
  }

  async verifySolution(challengeData, solution) {
    // Verify solution
    return true;
  }

  renderChallenge(challengeData, onSolutionSubmit) {
    // Return React component
    return <div>Your custom UI</div>;
  }
}
```

### Step 4: Register Client Handler

In `frontend/src/ppe/PPEFactory.js`:

```javascript
import { MyCustomHandler } from './MyCustomHandler';

this.register('my_custom_type', MyCustomHandler);
```

## Example: Proof-of-Work PPE

Here's a complete example of a Proof-of-Work challenge:

### Backend

```python
# backend/app/ppe/proof_of_work.py
from .base import BasePPE, PPEType, PPEDifficulty
import hashlib
from typing import Tuple

class ProofOfWorkPPE(BasePPE):
    def get_type(self) -> PPEType:
        return PPEType.PROOF_OF_WORK
    
    def generate_challenge_with_secret(self, secret: str, session_id: str) -> Tuple[str, str]:
        # Challenge: Find nonce such that H(secret || session || nonce) starts with N zeros
        difficulty_zeros = {
            PPEDifficulty.EASY: 3,
            PPEDifficulty.MEDIUM: 4,
            PPEDifficulty.HARD: 5
        }
        target_zeros = difficulty_zeros[self.difficulty]
        
        # The challenge is the (secret, session, target)
        challenge_data = f"{secret}:{session_id}:{target_zeros}"
        
        # Solution is a nonce that satisfies the condition
        solution = self._find_nonce(secret, session_id, target_zeros)
        
        return challenge_data, solution
    
    def _find_nonce(self, secret: str, session_id: str, target_zeros: int) -> str:
        nonce = 0
        prefix = "0" * target_zeros
        while True:
            candidate = f"{secret}{session_id}{nonce}"
            hash_result = hashlib.sha256(candidate.encode()).hexdigest()
            if hash_result.startswith(prefix):
                return str(nonce)
            nonce += 1
            if nonce > 1000000:  # Safety limit
                break
        return "0"
    
    def verify_solution(self, challenge_data: str, solution: str) -> bool:
        parts = challenge_data.split(":")
        secret, session_id, target_zeros = parts[0], parts[1], int(parts[2])
        
        candidate = f"{secret}{session_id}{solution}"
        hash_result = hashlib.sha256(candidate.encode()).hexdigest()
        prefix = "0" * target_zeros
        
        return hash_result.startswith(prefix)
    
    def estimate_effort(self) -> float:
        # Rough estimates
        return {
            PPEDifficulty.EASY: 1.0,
            PPEDifficulty.MEDIUM: 5.0,
            PPEDifficulty.HARD: 30.0
        }[self.difficulty]
```

## Testing Your PPE

Use the test endpoint:

```bash
curl -X POST http://localhost:8000/ppe/test-challenge \
  -H "Content-Type: application/json" \
  -d '{"ppe_type": "my_custom_type", "difficulty": "medium"}'
```

## Best Practices

1. **Deterministic Generation**: Always use the secret and session_id to generate challenges deterministically
2. **Verification**: Both parties must be able to verify challenges were generated correctly
3. **Effort Estimation**: Provide accurate effort estimates
4. **Client-Server Parity**: Ensure client and server implementations match exactly
5. **Testing**: Write comprehensive tests for your PPE type

## Available PPE Types

Run: `GET /ppe/types` to see all registered PPE types.