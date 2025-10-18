# Architecture Overview 🏗️

How the PPE polling system works under the hood.

## High-Level Flow

```
┌─────────┐   1. Register    ┌─────────┐
│  User A │ ───────────────> │  System │
└─────────┘   (solve CAPTCHA) └─────────┘
                                    │
                                    │ 2. Assign neighbors
                                    │    (ideal graph)
                                    ▼
┌─────────┐                   ┌─────────┐
│  User A │ ◄────────────────►│  User B │
└─────────┘   3. PPE protocol  └─────────┘
     │        (mutual challenges)
     │
     │ 4. Vote
     ▼
┌─────────┐
│  System │ ──> 5. Generate proof graph
└─────────┘
     │
     │ 6. Anyone can verify
     ▼
┌──────────┐
│ Verifier │
└──────────┘
```

## Backend Architecture

```
app/
├── models/          # Pydantic data models
│   ├── poll.py      # Poll, Vote, Registration
│   └── proof_graph.py
│
├── routes/          # FastAPI endpoints
│   ├── polls.py     # CRUD operations
│   ├── registration.py
│   ├── ppe.py       # PPE protocol
│   ├── verification.py
│   └── ws.py        # WebSocket
│
├── services/        # Business logic
│   ├── poll_service.py
│   ├── graph_service.py
│   ├── ppe_service.py
│   ├── verification_service.py
│   └── proof_graph_service.py
│
├── utils/           # Utilities
│   ├── crypto_utils.py
│   ├── captcha_utils.py
│   ├── ppe_utils.py
│   └── graph_analysis.py
│
└── ppe/             # PPE implementations
    ├── base.py      # BasePPE interface
    ├── symmetric_captcha.py
    └── factory.py   # PPE factory
```

## Frontend Architecture

```
src/
├── components/      # React components
│   ├── PollCreatePage.jsx
│   ├── PollVotePage.jsx
│   ├── PollVerifyPage.jsx
│   ├── PPEChallengeModal.jsx
│   ├── ProofGraphViewer.jsx
│   └── AdvancedVerificationPanel.jsx
│
├── services/        # API clients
│   ├── api.js
│   ├── cryptoService.js
│   ├── ppeService.js
│   ├── proofGraphApi.js
│   └── verificationApi.js
│
└── ppe/             # PPE handlers
    ├── BasePPEHandler.js
    ├── SymmetricCaptchaHandler.js
    └── PPEFactory.js
```

## Key Components

### 1. Registration PPE (One-Sided)

User proves they're human by solving a CAPTCHA:

```python
challenge = generate_captcha()
user_solution = solve_captcha(challenge)
if verify(challenge, user_solution):
    register_user()
```

### 2. Ideal Graph

Deterministic neighbor assignment using hash-based random graph:

```python
def compute_ideal_graph(participants):
    graph = {}
    for user in participants:
        neighbors = hash_based_selection(user, participants)
        graph[user] = neighbors
    return graph
```

### 3. Symmetric CAPTCHA PPE

Both parties exchange challenges:

```
User A                    User B
  │                         │
  ├──── Challenge A ───────>│
  │<──── Challenge B ────────┤
  │                         │
  ├──── Commitment ────────>│
  │<──── Commitment ─────────┤
  │                         │
  ├──── Reveal ────────────>│
  │<──── Reveal ─────────────┤
  │                         │
  ├──── Signature ─────────>│
  │<──── Signature ──────────┤
  │                         │
  └─ Mutual Certification ──┘
```

### 4. Proof Graph

Cryptographically bound structure:

```python
proof = {
    "metadata": {...},
    "participants": [...],
    "certifications": [...],
    "votes": [...],
    "graph_hash": sha256(all_above)
}
```

### 5. Verification

Advanced graph analysis detects attacks:

```python
# Conductance check
for cluster in find_clusters(graph):
    if conductance(cluster) < 0.2:
        flag_as_suspicious()

# Spectral analysis
eigenvalues = compute_laplacian_spectrum(graph)
spectral_gap = eigenvalues[1] - eigenvalues[0]
if spectral_gap < 0.1:
    warn_poor_expansion()
```

## Data Flow

### Registration Flow

```
1. User generates keypair
2. POST /polls/{id}/register with public key
3. Server generates CAPTCHA challenge
4. User solves CAPTCHA
5. POST /polls/{id}/register/verify with solution
6. Server verifies solution
7. User added to registrants
```

### PPE Flow

```
1. GET /polls/{id}/graph/ideal to get neighbors
2. Connect WebSocket: ws://server/ws/{poll_id}/{user_id}
3. For each neighbor:
   a. Generate challenge with secret
   b. Send ppe_challenge message
   c. Receive peer's challenge
   d. Solve peer's challenge
   e. Create commitment
   f. Send ppe_commitment message
   g. Receive peer's commitment
   h. Reveal secret + solution
   i. Send ppe_reveal message
   j. Verify peer's reveal
   k. Exchange signatures
   l. POST /polls/{id}/ppe-certification
```

### Voting Flow

```
1. User selects option
2. Sign message: sign(poll_id + option)
3. POST /polls/{id}/vote with signature
4. Server verifies:
   - User is registered
   - User has enough certifications
   - Signature is valid
5. Vote recorded
```

## Security Properties

### Sybil Resistance

System detects fake accounts through:
- **Graph expansion**: Honest users create well-connected graph
- **Conductance**: Fake accounts cluster together (low conductance)
- **Effort requirement**: Each identity requires effort with others

### Cryptographic Properties

- **Public verifiability**: Anyone can verify proof graph
- **Tamper evidence**: Graph hash changes if any data modified
- **Non-repudiation**: Signatures prove who voted
- **Privacy**: No link between voter and vote (if implemented)

## Scalability

Current system handles:
- **Users**: 100+ concurrent
- **PPE sessions**: 50+ simultaneous
- **Verification**: O(n²) worst case for n users

Optimization opportunities:
- Async PPE protocol
- Batch verification
- Database for persistence
- Caching layer

## Extensibility

### Adding New PPE Type

1. Implement `BasePPE` interface:
```python
class MyPPE(BasePPE):
    def generate_challenge_with_secret(self, secret, session): ...
    def verify_solution(self, challenge, solution): ...
```

2. Register in factory:
```python
ppe_factory.register(MyPPE, metadata)
```

3. Create client handler:
```javascript
class MyPPEHandler extends BasePPEHandler { ... }
ppeFactory.register('my_ppe', MyPPEHandler);
```

That's it! The system uses your new PPE type.

## Performance

Typical operation times:
- **Registration**: 2-5 seconds
- **PPE protocol**: 10-20 seconds per pair
- **Vote casting**: <1 second
- **Verification**: 5-30 seconds for 50 users

## Future Improvements

- Persistent database storage
- Privacy-preserving voting (zero-knowledge proofs)
- Mobile app support
- Batch PPE optimization
- Alternative PPE types (audio, image recognition)
- Reputation system