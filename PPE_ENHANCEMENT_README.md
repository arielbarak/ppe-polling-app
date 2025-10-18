# PPE Protocol Enhancement - Implementation Guide

## Overview

This implementation adds **multiple PPE protocol types** to the existing PPE polling application, as described in Appendix B of the "Public Verification of Private Effort" paper. It provides flexibility and robustness beyond basic CAPTCHA-based PPE.

## 🆕 New PPE Types Implemented

### 1. **Symmetric CAPTCHA PPE** (Enhanced Base Implementation)
- **Description**: Both parties solve CAPTCHAs and exchange solutions
- **Security**: MAC (Message Authentication Code) binding prevents replay attacks
- **Use Case**: Universal, works for all users
- **Effort**: Medium (20-40 seconds)

### 2. **Proof-of-Storage PPE**
- **Description**: Prover demonstrates access to cloud storage (Google Drive, Dropbox)
- **Security**: Requires legitimate access to existing accounts (harder for Sybils)
- **Use Case**: Users with cloud storage accounts
- **Effort**: Low (15-30 seconds)

### 3. **Computational PPE**
- **Description**: Proof-of-work style challenges with adjustable difficulty
- **Security**: Very high - computationally infeasible to fake
- **Use Case**: High-security scenarios, small polls
- **Effort**: Variable (based on difficulty: 10 seconds to 2+ minutes)

### 4. **Social Network Distance PPE**
- **Description**: Reduced effort for socially connected users
- **Security**: High + improved UX for legitimate users
- **Use Case**: Large polls with social network integration
- **Effort**: Variable (50% reduction for direct connections)

## 🏗️ Architecture

```
backend/
├── app/
│   ├── models/
│   │   └── ppe_types.py                  # PPE type definitions & database models
│   ├── services/
│   │   ├── ppe/                          # PPE implementations
│   │   │   ├── base.py                   # Abstract base classes
│   │   │   ├── symmetric_captcha.py      # Enhanced CAPTCHA PPE
│   │   │   ├── proof_of_storage.py       # Cloud storage verification
│   │   │   ├── computational.py          # Proof-of-work puzzles
│   │   │   └── social_distance.py        # Social network based
│   │   ├── ppe_executor.py               # PPE execution orchestrator
│   │   └── ppe_integration.py            # Integration utilities
│   ├── api/
│   │   └── ppe_endpoints.py              # Enhanced API endpoints
│   └── schemas/
│       └── ppe.py                        # Pydantic schemas
└── tests/
    └── test_ppe_types.py                 # Comprehensive test suite

frontend/
└── src/
    ├── components/
    │   └── ppe/                          # PPE UI components
    │       ├── SymmetricCaptchaPPE.jsx
    │       ├── ProofOfStoragePPE.jsx
    │       ├── ComputationalPPE.jsx
    │       └── PPETypeSelector.jsx
    ├── hooks/
    │   └── usePPEExecution.js            # PPE state management
    └── services/
        └── ppeService.js                 # Enhanced API client
```

## Quick Start

### 1. **Backend Setup**

```bash
cd backend

# Install dependencies (networkx is already in requirements.txt)
pip install -r requirements.txt

# Update database schema
python init_db.py reset

# Setup PPE enhancement for existing polls
python setup_ppe_enhancement.py setup

# Test PPE implementations
python setup_ppe_enhancement.py test
```

### 2. **Frontend Setup**

```bash
cd frontend

# No new dependencies needed - uses existing Ant Design components
npm install

# Start development server
npm start
```

### 3. **Integration**

Update your poll creation to include PPE configuration:

```python
from app.services.ppe_integration import create_default_ppe_config

def create_poll(poll_data, db: Session):
    poll = Poll(**poll_data)
    db.add(poll)
    db.flush()  # Get poll.id
    
    # Create PPE configuration
    create_default_ppe_config(poll.id, db)
    
    db.commit()
    return poll
```

## API Endpoints

### Enhanced PPE Endpoints (`/api/ppe/`)

```http
POST /api/ppe/initiate
POST /api/ppe/submit/{execution_id}
GET  /api/ppe/status/{execution_id}
GET  /api/ppe/active/{poll_id}/{user_id}
GET  /api/ppe/config/{poll_id}
GET  /api/ppe/types
GET  /api/ppe/available-types/{poll_id}
POST /api/ppe/cleanup/{poll_id}
```

### Example Usage

```javascript
// Get available PPE types for a poll
const response = await fetch('/api/ppe/available-types/poll123');
const { available_types } = await response.json();

// Initiate symmetric CAPTCHA PPE
const execution = await fetch('/api/ppe/initiate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    poll_id: 'poll123',
    prover_id: 'user1',
    verifier_id: 'user2',
    ppe_type: 'symmetric_captcha'
  })
});

// Submit response
const result = await fetch(`/api/ppe/submit/${executionId}`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    answer: 'ABC123',
    mac: 'mac_value'
  })
});
```

## Configuration

### Poll PPE Configuration

```python
from app.models.ppe_types import PPEType, PPEDifficulty

ppe_config = PPEConfig(
    poll_id="poll123",
    
    # Available PPE types for this poll
    allowed_certification_types=[
        PPEType.SYMMETRIC_CAPTCHA,
        PPEType.PROOF_OF_STORAGE,
        PPEType.COMPUTATIONAL
    ],
    
    # Default type
    default_certification_type=PPEType.SYMMETRIC_CAPTCHA,
    
    # Difficulty settings
    certification_difficulty=PPEDifficulty.MEDIUM,
    
    # Performance limits
    ppe_timeout=300,  # 5 minutes
    max_concurrent_ppes=3,
    
    # Security parameters (Definition 2.2)
    completeness_sigma=0.95,  # 95% honest success rate
    soundness_epsilon=0.05,   # 5% adversary success rate
)
```

### Recommended Configurations

```python
# High security poll
high_security_config = {
    "allowed_types": [PPEType.COMPUTATIONAL, PPEType.SYMMETRIC_CAPTCHA],
    "default_type": PPEType.COMPUTATIONAL,
    "difficulty": PPEDifficulty.HARD,
    "completeness_sigma": 0.98,
    "soundness_epsilon": 0.02
}

# Large poll (user-friendly)
large_poll_config = {
    "allowed_types": [PPEType.SOCIAL_DISTANCE, PPEType.PROOF_OF_STORAGE, PPEType.SYMMETRIC_CAPTCHA],
    "default_type": PPEType.SOCIAL_DISTANCE,
    "difficulty": PPEDifficulty.MEDIUM
}

# Quick poll
quick_poll_config = {
    "allowed_types": [PPEType.PROOF_OF_STORAGE, PPEType.SYMMETRIC_CAPTCHA],
    "default_type": PPEType.PROOF_OF_STORAGE,
    "difficulty": PPEDifficulty.EASY
}
```

## Testing

Run the comprehensive test suite:

```bash
cd backend

# Run all PPE tests
pytest tests/test_ppe_types.py -v

# Run specific test class
pytest tests/test_ppe_types.py::TestSymmetricCaptchaPPE -v

# Test with coverage
pytest tests/test_ppe_types.py --cov=app.services.ppe
```

### Test Coverage

The test suite covers:
- All PPE type implementations
- Security parameter validation  
- Challenge generation and verification
- Social network distance calculation
- Error handling and edge cases
- MAC binding and replay attack prevention

## Security Properties

### Definition 2.2 Implementation

Each PPE type implements the formal security properties:

- **σ-completeness**: Honest parties succeed with probability ≥ σ
- **ε-soundness**: Adversary succeeds with probability ≤ ε

| PPE Type | σ (Completeness) | ε (Soundness) | Notes |
|----------|------------------|---------------|--------|
| Symmetric CAPTCHA | 0.95 | 0.05 | MAC binding prevents replay |
| Proof-of-Storage | 0.98 | 0.02 | High completeness (just file access) |
| Computational | 0.99 | 0.01 | Very high security, deterministic |
| Social Distance | 0.97 | 0.03 | Variable based on social connections |

### Security Validation

```python
# Validate security parameters
valid, reason = ppe.validate_security_parameters()
if not valid:
    print(f"Security issue: {reason}")
```

## Performance & Effort Estimation

### Effort Comparison

| PPE Type | Easy | Medium | Hard | Extreme |
|----------|------|--------|------|---------|
| Symmetric CAPTCHA | 10s | 20s | 40s | 60s |
| Proof-of-Storage | 15s | 30s | 60s | 120s |
| Computational | 16s | 262s | ~17min | ~67min |
| Social Distance | 7.5s (connected) | 15s (connected) | 30s (connected) | 60s (connected) |

### Concurrent Execution

- **Default limit**: 3 concurrent PPEs per user
- **Configurable**: Per poll via `max_concurrent_ppes`
- **Cleanup**: Automatic timeout handling with `/cleanup` endpoint

## 🌐 Frontend Integration

### PPE Type Selector Component

```jsx
import PPETypeSelector from './components/ppe/PPETypeSelector';
import { usePPEExecution } from './hooks/usePPEExecution';

function CertificationPhase({ pollId, userId }) {
  const { initiatePPE, submitResponse } = usePPEExecution(pollId, userId);
  const [selectedType, setSelectedType] = useState(null);

  return (
    <div>
      <PPETypeSelector 
        pollId={pollId} 
        onSelect={setSelectedType}
      />
      
      {selectedType && (
        <button onClick={() => initiatePPE(partnerId, selectedType)}>
          Start {selectedType} PPE
        </button>
      )}
    </div>
  );
}
```

### PPE Execution Components

```jsx
// Dynamic component loading based on PPE type
const PPEComponents = {
  'symmetric_captcha': SymmetricCaptchaPPE,
  'proof_of_storage': ProofOfStoragePPE,
  'computational': ComputationalPPE,
  'social_distance': SocialDistancePPE
};

function PPEExecution({ execution, onComplete }) {
  const PPEComponent = PPEComponents[execution.ppe_type];
  
  return (
    <PPEComponent
      execution={execution}
      onSubmit={submitResponse}
      onComplete={onComplete}
    />
  );
}
```

## 🔄 Migration Guide

### From Existing PPE Implementation

1. **Database Migration**:
   ```bash
   python init_db.py reset  # Creates new tables
   python setup_ppe_enhancement.py setup  # Migrates existing polls
   ```

2. **API Migration**:
   - Old endpoints still work (backward compatible)
   - New endpoints provide enhanced functionality
   - Gradual migration possible

3. **Frontend Migration**:
   - Keep existing PPE components
   - Add new PPE type selector for enhanced polls
   - Use enhanced service methods for new features

## 🐛 Troubleshooting

### Common Issues

1. **"PPE type not allowed for this poll"**
   ```python
   # Check poll configuration
   config = await ppeService.getPPEConfig(pollId);
   console.log('Allowed types:', config.allowed_certification_types);
   ```

2. **"Timeout exceeded"**
   ```python
   # Increase timeout in poll configuration
   update_poll_ppe_config(poll_id, db, ppe_timeout=600)  # 10 minutes
   ```

3. **"No solution found" (Computational PPE)**
   ```python
   # Reduce difficulty for testing
   update_poll_ppe_config(poll_id, db, certification_difficulty=PPEDifficulty.EASY)
   ```

### Debug Mode

```bash
# Enable debug logging
export PPE_DEBUG=1

# Run with verbose output
python setup_ppe_enhancement.py test
```

## Monitoring & Analytics

### PPE Execution Tracking

```python
# Get PPE execution statistics
from app.models.ppe_types import PPEExecution
from sqlalchemy import func

stats = db.query(
    PPEExecution.ppe_type,
    func.count(PPEExecution.id).label('total'),
    func.avg(PPEExecution.duration_seconds).label('avg_duration'),
    func.sum(case((PPEExecution.result == True, 1), else_=0)).label('success_count')
).group_by(PPEExecution.ppe_type).all()

for stat in stats:
    print(f"{stat.ppe_type}: {stat.success_count}/{stat.total} success, avg {stat.avg_duration:.1f}s")
```

### Audit Logging

```python
# PPE execution audit trail
executions = db.query(PPEExecution).filter(
    PPEExecution.poll_id == poll_id,
    PPEExecution.created_at >= yesterday
).all()

for exec in executions:
    print(f"PPE {exec.id}: {exec.ppe_type} {exec.status} in {exec.duration_seconds}s")
```

## Future Enhancements

### Planned Features

1. **Human Interaction PPE** (Video/Audio challenges)
2. **Zero-Knowledge PPE** (ZK-SNARK based proofs)
3. **Biometric PPE** (Fingerprint/face recognition)
4. **Location-based PPE** (GPS verification)

### Extension Points

```python
# Add custom PPE type
class CustomPPE(PPEProtocol):
    def __init__(self):
        super().__init__(PPEType.CUSTOM, difficulty)
    
    def generate_challenge(self, session_id, prover_id, verifier_id):
        # Custom challenge logic
        pass
    
    def verify_response(self, challenge_data, verification_data, response):
        # Custom verification logic
        pass

# Register in executor
executor.ppe_registry[PPEType.CUSTOM] = CustomPPE
```

---

## 📞 Support

For questions about this implementation:

1. **Check the tests**: `backend/tests/test_ppe_types.py` has comprehensive examples
2. **Review integration guide**: `python setup_ppe_enhancement.py guide`  
3. **Validate configuration**: Use `validate_ppe_config()` utility
4. **Check logs**: Enable debug mode for detailed PPE execution logs

---

**Commit Message for Integration:**
```
feat(ppe): enhance PPE protocols with multiple implementation types

- Implement symmetric CAPTCHA-based PPE with MAC binding
- Add proof-of-storage PPE option for backup-based effort
- Create computational PPE with adjustable proof-of-work difficulty
- Build social network distance-based PPE for improved UX
- Add PPE type selection and configuration per poll
- Implement Definition 2.2 (σ-completeness, ε-soundness)
- Add concurrent PPE execution support with timeout management
- Create comprehensive PPE audit logging for security analysis

Implements Appendix B PPE mechanisms from paper with full backward compatibility.
Ready for production deployment with extensive test coverage.
```