# PPE Polling System - Simulation & Testing Guide

## Overview

This directory contains comprehensive testing infrastructure for simulating realistic usage of the PPE polling system at scale.

## Running Simulations

### Honest Scenario (All users follow protocol)

```bash
cd backend
python -m tests.simulation.run_simulation --scenario honest --users 50
```

This simulates 50 honest users going through:
1. Registration with CAPTCHA
2. PPE certification with neighbors
3. Voting

### Sybil Attack Scenario

```bash
python -m tests.simulation.run_simulation --scenario sybil --honest 30 --sybils 20
```

Simulates an attack where:
- 30 honest users follow the protocol
- 20 Sybil identities controlled by attacker
- Sybils primarily certify each other (collusion)
- Sybils coordinate votes

### Load Test

```bash
python -m tests.simulation.run_simulation --scenario load --users 100
```

Tests system under load with 100 concurrent users.

### With Verification

Add `--verify` flag to run verification after simulation:

```bash
python -m tests.simulation.run_simulation --scenario sybil --honest 30 --sybils 20 --verify
```

## Running Unit Tests

```bash
pytest tests/test_integration_flow.py -v
pytest tests/test_performance.py -v
```

## Expected Results

### Honest Scenario (50 users)
- **Registrations**: ~48-50 successful (95-100%)
- **PPE Completions**: ~100-150 (2-3 per user)
- **Votes**: ~48-50 successful
- **Avg Registration Time**: 2-5 seconds
- **Avg PPE Time**: 5-15 seconds
- **Verification**: ✅ VALID, no warnings

### Sybil Attack Scenario (30 honest + 20 Sybils)
- **Registrations**: ~48-50 successful
- **PPE Completions**: ~100-120
- **Votes**: ~48-50 successful
- **Verification**: ⚠️ WARNINGS about:
  - Suspicious low-conductance clusters
  - Vote-certification correlation
  - Voter clustering

### Load Test (100 users)
- **Throughput**: 5-10 users/second
- **Success Rate**: >90%
- **System should remain stable**

## Performance Benchmarks

Target performance metrics:
- **Registration**: < 5 seconds per user
- **PPE Protocol**: < 20 seconds per pair
- **Voting**: < 1 second per vote
- **Verification**: < 30 seconds for 50 users

## Custom Scenarios

You can create custom scenarios by:

1. Import the scenario runner:
```python
from tests.simulation.scenario_runner import ScenarioRunner
```

2. Create and run custom scenario:
```python
runner = ScenarioRunner()
users = runner.create_users(25)
# ... custom logic ...
```

## Troubleshooting

### Connection Refused
- Ensure backend is running: `uvicorn app.main:app --reload`
- Check base URL: `--base-url http://localhost:8000`

### Timeouts
- Increase httpx timeout in user_simulator.py
- Reduce concurrent users
- Check server resources

### High Failure Rate
- Check server logs for errors
- Verify database state
- Run with smaller user counts first

## CI/CD Integration

To integrate with CI/CD:

```yaml
# .github/workflows/test.yml
- name: Run Simulation Tests
  run: |
    python -m tests.simulation.run_simulation --scenario honest --users 20
    python -m tests.simulation.run_simulation --scenario sybil --honest 15 --sybils 10 --verify
```

## Metrics Collection

Simulations collect:
- Registration success rate
- PPE completion rate
- Vote success rate
- Timing statistics (mean, median, min, max)
- Throughput (operations/second)
- Error logs

Results are stored in `runner.results` dictionary.