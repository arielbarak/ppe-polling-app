# Phase 0 Implementation Verification Checklist

## Quick Start

1. **Initialize Database:**
   ```bash
   cd backend
   python init_db.py reset
   ```

2. **Run Tests:**
   ```bash
   pytest tests/test_state_machine.py -v
   pytest tests/test_voting_flow_integration.py -v -s
   ```

3. **Debug Issues:**
   ```bash
   python debug_voting.py list
   python debug_voting.py debug <user_id> <poll_id>
   ```

---

## Issue Verification Checklist

### ✅ Issue #7: Can Reach Voting State (CRITICAL BLOCKER)

**Test Steps:**
1. [ ] Create a poll in REGISTRATION phase
2. [ ] Register multiple users
3. [ ] Run PPE assignment: `assignment_service.assign_ppe_partners(poll_id)`
4. [ ] Complete all required PPEs for a user
5. [ ] Transition poll to VOTING phase: `state_machine.transition_to_voting(poll_id)`
6. [ ] Check voting authorization: `state_machine.can_user_vote(user_id, poll_id)`
7. [ ] Cast vote: `POST /api/polls/{poll_id}/vote`

**Expected Result:** 
- `can_user_vote()` returns `(True, None)`
- Vote API call succeeds
- User cannot vote twice

**Debug Commands:**
```bash
python debug_voting.py debug <user_id> <poll_id>
python debug_voting.py fix <poll_id>
```

---

### ✅ Issue #5: State Persists on Refresh

**Test Steps:**
1. [ ] User completes some PPEs
2. [ ] Refresh browser page
3. [ ] Check certification state API: `GET /api/polls/{poll_id}/certification/state`
4. [ ] Verify state is restored (completed count correct)

**Expected Result:**
- State API returns existing certification progress
- Frontend displays correct completion count
- User can continue from where they left off

**Debug:**
- Check `certification_states` table in database
- Verify `useCertificationState` hook loads data on mount

---

### ✅ Issue #2: Automatic PPE Assignment

**Test Steps:**
1. [ ] Create poll and register users
2. [ ] Transition to certification phase
3. [ ] Check assignments API: `GET /api/polls/{poll_id}/certification/assignments`
4. [ ] Verify no "Verify User" button exists in frontend
5. [ ] Verify assignments appear automatically

**Expected Result:**
- Assignments generated automatically when registration closes
- No manual intervention required
- PPE partners calculated using certification graph algorithm

**Debug:**
```python
from app.services.ppe_assignment_service import PPEAssignmentService
service = PPEAssignmentService(db)
assignments = service.assign_ppe_partners(poll_id)
print(assignments)
```

---

### ✅ Issue #1: Dynamic Verification Count

**Test Steps:**
1. [ ] Check verification requirements API
2. [ ] Verify message shows "X out of Y" with correct Y (not hardcoded 2)
3. [ ] Add more users to poll
4. [ ] Verify Y updates based on graph degree

**Expected Result:**
- Shows actual required verifications based on graph
- Count updates as participants join
- Message updates as PPEs complete

**Debug:**
```python
from app.services.verification_service import VerificationService
service = VerificationService(db)
required, completed, remaining = service.get_verification_requirements(user_id, poll_id)
```

---

### ✅ Issue #3: Captcha Case Sensitivity

**Test Steps:**
1. [ ] Generate captcha with solution "ABC123"
2. [ ] Try answers: "abc123", "Abc123", "ABC123"
3. [ ] All should be accepted

**Expected Result:**
- Case-insensitive verification
- Clear messaging about case insensitivity

**Debug:**
```python
from app.services.captcha_service import CaptchaService
service = CaptchaService()
result = service.verify_captcha("abc123", "ABC123")  # Should be True
```

---

### ✅ Issue #4: PPE Type Clarity

**Test Steps:**
1. [ ] Check registration captcha terminology
2. [ ] Check certification phase labels
3. [ ] Verify clear distinction between one-sided and two-sided PPE

**Expected Result:**
- Registration shows "one-sided PPE" or "server-verified"
- Certification shows "peer-to-peer PPE" or "two-sided"
- Clear explanations of differences

---

### ✅ Issue #6: Clear Verification Purpose

**Test Steps:**
1. [ ] Check certification phase component
2. [ ] Verify explanation of why verification is needed
3. [ ] Check security impact messaging

**Expected Result:**
- "Building Security Graph" explanation visible
- Shows Sybil attack prevention purpose
- Displays mathematical security guarantees

---

## Integration Verification

### Complete Voting Flow Test

Run the integration test:
```bash
pytest tests/test_voting_flow_integration.py::TestVotingFlowIntegration::test_complete_voting_flow -v -s
```

**Expected Output:**
```
✓ Registered 10 users
✓ Assigned PPE partners to 10 users
✓ User user_0 completed 4 PPEs → Certified: True
✓ User user_1 completed 3 PPEs → Certified: True
...
✓ Transitioned to voting: 10 certified, 0 excluded
✓ User user_0 CAN VOTE
✓ User user_1 CAN VOTE
...
✓ User user_0 voted
✓ User user_1 voted
...
✓ User user_0 correctly blocked from double-voting
✅ INTEGRATION TEST PASSED: Complete voting flow works!
```

### Frontend Integration

1. [ ] Load VerificationStatus component
2. [ ] Load CertificationPhase component  
3. [ ] Load updated RegistrationCaptcha component
4. [ ] Test useCertificationState hook
5. [ ] Verify state persistence across page refresh

### API Integration

Test all endpoints work:
```bash
# Certification state
curl "http://localhost:8000/api/polls/{poll_id}/certification/state?user_id={user_id}"

# PPE assignments  
curl "http://localhost:8000/api/polls/{poll_id}/certification/assignments?user_id={user_id}"

# Vote status
curl "http://localhost:8000/api/polls/{poll_id}/vote/status?user_id={user_id}"

# Verification requirements
curl "http://localhost:8000/api/polls/{poll_id}/verification/requirements?user_id={user_id}"
```

---

## Common Issues & Solutions

### Issue: "User cannot vote: Not registered for this poll"
**Solution:** Check user exists in database for that poll
```bash
python debug_voting.py debug <user_id> <poll_id>
```

### Issue: "User cannot vote: Did not complete certification in time"
**Solution:** Check certification state
```bash
python debug_voting.py fix <poll_id>
```

### Issue: Frontend shows incorrect verification count
**Solution:** Check verification service returns correct data
```python
# In backend shell:
from app.services.verification_service import VerificationService
service = VerificationService(db)
required, completed, remaining = service.get_verification_requirements(user_id, poll_id)
print(f"Required: {required}, Completed: {completed}")
```

### Issue: PPE assignments not generated
**Solution:** Run assignment service manually
```python
from app.services.ppe_assignment_service import PPEAssignmentService
service = PPEAssignmentService(db)
assignments = service.assign_ppe_partners(poll_id)
```

---

## Performance Verification

1. [ ] Page load time with state persistence
2. [ ] PPE assignment generation time for 100+ users
3. [ ] State machine performance for multiple concurrent users
4. [ ] Database query efficiency for certification states

---

## Security Verification

1. [ ] State machine prevents unauthorized voting
2. [ ] PPE assignment algorithm produces secure graph
3. [ ] Certification requirements enforce security parameters
4. [ ] Vote recording validates all authorization checks

---

**🎯 SUCCESS CRITERIA:** 
All 7 issues resolved, tests pass, voting flow works end-to-end.