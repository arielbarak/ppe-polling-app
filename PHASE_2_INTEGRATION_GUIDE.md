# Phase 2: Graph Expansion Verification - Integration Guide

## 🎯 What This Implements

This phase implements **THE KEY SECURITY METRIC** from the PPE paper: **Sybil resistance bounds**.

The system computes the maximum number of fake identities an adversary can create, even after successfully completing many PPEs with honest participants.

## 🔧 Quick Integration

### 1. Backend Integration

The expansion endpoints are already integrated into your FastAPI application. The new endpoints are:

```
GET /api/expansion/{poll_id}/metrics          # Complete expansion analysis
GET /api/expansion/{poll_id}/sybil-bound     # Quick Sybil bound check
GET /api/expansion/{poll_id}/expansion/vertex # Vertex expansion only
GET /api/expansion/{poll_id}/expansion/edge   # Edge expansion only
GET /api/expansion/{poll_id}/expansion/spectral # Spectral gap only
GET /api/expansion/{poll_id}/lse-property     # LSE property check
```

### 2. Frontend Integration

Add the expansion metrics component to your poll verification page:

```jsx
import ExpansionMetrics from '../components/ExpansionMetrics';

// In your verification component:
function PollVerification({ pollId }) {
  return (
    <div>
      {/* Your existing verification components */}
      
      {/* NEW: Graph Expansion Verification */}
      <ExpansionMetrics pollId={pollId} />
    </div>
  );
}
```

### 3. Database Setup

The system uses your existing poll and certification data. Ensure your database has:
- `polls` table with poll information
- `poll_participants` table with participant registration  
- `ppe_certifications` table with successful PPE verifications

## 🛡️ Key Security Metrics

### The Critical Metric: Sybil Resistance Bound

```json
{
  "sybil_bound": {
    "max_sybil_nodes": 45,           // Max fake identities possible
    "attack_edges": 1200,            // Adversary's successful PPEs
    "average_degree": 58.5,          // Graph connectivity
    "sybil_percentage": 4.5,         // % of total that could be Sybil
    "resistance_level": "HIGH",      // HIGH/MEDIUM/LOW classification
    "multiplicative_advantage": 45.0 // Adversary advantage vs honest user
  }
}
```

**Security Guarantee**: Even if an adversary completes 1,200 PPEs with honest participants, they can control at most 45 fake identities (4.5% of participants).

### Other Verification Metrics

- **Vertex Expansion**: How well the graph expands small sets
- **Edge Expansion**: Graph conductance (bottleneck detection)  
- **Spectral Gap**: Eigenvalue-based expansion measure
- **LSE Property**: Large-Set Expanding verification
- **Minimum Degree**: Connectivity requirements

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Test all expansion algorithms
cd backend
python -m pytest tests/test_graph_expansion.py -v

# Test THE KEY METRIC (Sybil bounds)
python -m pytest tests/test_sybil_bounds.py -v

# Test spectral analysis
python -m pytest tests/test_spectral_analysis.py -v
```

## 📊 Example API Usage

### Get Complete Expansion Metrics

```bash
curl "http://localhost:8000/api/expansion/poll_123/metrics"
```

Response:
```json
{
  "poll_id": "poll_123",
  "verification_passed": true,
  "sybil_bound": {
    "max_sybil_nodes": 45,
    "resistance_level": "HIGH",
    "sybil_percentage": 4.5
  },
  "vertex_expansion": {
    "expansion_ratio": 2.3,
    "satisfies_threshold": true
  },
  "is_lse": true,
  "num_nodes": 1000,
  "average_degree": 58.5
}
```

### Get Quick Sybil Bound Check

```bash
curl "http://localhost:8000/api/expansion/poll_123/sybil-bound"
```

Response:
```json
{
  "poll_id": "poll_123", 
  "sybil_bound": {
    "max_sybil_nodes": 45,
    "resistance_level": "HIGH"
  },
  "verification_passed": true
}
```

## 🎨 Frontend Display

The `ExpansionMetrics` component provides:

- **Overall verification status** with pass/fail indicators
- **Highlighted Sybil resistance bound** (the key security metric)
- **Detailed expansion properties** with progress bars
- **Security guarantees explanation** in plain English
- **Color-coded resistance levels** (green=HIGH, yellow=MEDIUM, red=LOW)

## ⚙️ Configuration

Adjust security parameters in `backend/app/config/expansion_config.py`:

```python
class ExpansionConfig(BaseSettings):
    SECURITY_PARAMETER: int = 40              # κ (security parameter)
    ETA_E: float = 0.125                      # Max failed PPE fraction
    ETA_V: float = 0.025                      # Max deleted node fraction
    VERTEX_EXPANSION_THRESHOLD: float = 2.0   # Required vertex expansion
    EDGE_EXPANSION_THRESHOLD: float = 0.3     # Required conductance
    SPECTRAL_GAP_THRESHOLD: float = 0.1       # Required λ₂
```

## 🔬 Mathematical Foundation

This implementation follows the PPE paper exactly:

- **Section 4.1**: LSE property and graph expansion
- **Lemma 4.2**: Random graph LSE parameters
- **Theorem 4.4**: Soundness and Sybil bound (THE KEY RESULT)
- **Appendix C**: Parameter constraints and bounds

### The Key Formula (Theorem 4.4)

```
max_sybil_nodes ≤ max(K, (b / ((b-1)(1/2 - ηV) - bηE)) * (a/d))
```

Where:
- `a` = attack edges (successful adversary PPEs)
- `d` = average degree
- `b` = expansion parameter √(d(1/2 - ηV) / (2ln(m) - 2))
- `K` = security-based minimum bound

## 🚀 Next Steps

1. **Validate**: Run tests to ensure everything works correctly
2. **Tune**: Adjust thresholds based on your specific use case  
3. **Monitor**: Track Sybil bounds over time as polls run
4. **Scale**: For graphs >10,000 nodes, consider sampling optimizations

## 🛠️ Troubleshooting

### Database Connection Issues
Update the database import in `backend/app/api/expansion_endpoints.py` to match your database setup.

### Performance Issues  
For large graphs, the system automatically uses sparse matrix methods. If still slow, reduce `EXPANSION_SAMPLE_SIZE` in config.

### High Sybil Bounds
This indicates the graph may need:
- Higher average degree (more PPEs per participant)
- Better expansion (different participant matching)
- Lower adversary capability (fewer attack edges)

---

## ✅ Verification Complete

Your PPE polling system now has **provable Sybil resistance** with concrete security bounds!

**THE KEY INSIGHT**: The system can now tell you exactly how many fake identities an adversary can create, providing quantifiable security guarantees.