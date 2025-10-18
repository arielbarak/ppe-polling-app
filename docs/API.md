# API Reference 📡

Complete API documentation for the PPE polling system.

Base URL: `http://localhost:8000`

## Polls

### Create Poll

```bash
POST /polls
```

**Body:**
```json
{
  "question": "What's for dinner?",
  "options": ["Pizza", "Tacos", "Salad"]
}
```

**Response:**
```json
{
  "id": "poll_abc123",
  "question": "What's for dinner?",
  "options": ["Pizza", "Tacos", "Salad"],
  "registrants": {}
}
```

### Get Poll

```bash
GET /polls/{poll_id}
```

**Response:**
```json
{
  "id": "poll_abc123",
  "question": "What's for dinner?",
  "options": ["Pizza", "Tacos", "Salad"],
  "registrants": {
    "user_123": {"kty": "EC", "x": "...", "y": "..."}
  },
  "votes": {},
  "ppe_certifications": {}
}
```

### List Polls

```bash
GET /polls
```

**Response:**
```json
{
  "polls": [
    {
      "id": "poll_abc123",
      "question": "What's for dinner?",
      "options": ["Pizza", "Tacos", "Salad"]
    }
  ]
}
```

## Registration

### Register for Poll

```bash
POST /polls/{poll_id}/register
```

**Body:**
```json
{
  "publicKey": {
    "kty": "EC",
    "crv": "P-256",
    "x": "base64_x",
    "y": "base64_y"
  }
}
```

**Response:**
```json
{
  "message": "Registration challenge generated",
  "challengeText": "a b c 1 2 3"
}
```

### Verify Registration

```bash
POST /polls/{poll_id}/register/verify
```

**Body:**
```json
{
  "publicKey": {...},
  "solution": "abc123"
}
```

**Response:**
```json
{
  "message": "Registration successful",
  "userId": "user_123"
}
```

## PPE Protocol

### Get Ideal Graph Neighbors

```bash
GET /polls/{poll_id}/graph/ideal
```

**Response:**
```json
{
  "poll_id": "poll_abc123",
  "ideal_graph": {
    "user_123": ["user_456", "user_789"],
    "user_456": ["user_123", "user_789"]
  }
}
```

### Record PPE Certification

```bash
POST /polls/{poll_id}/ppe-certification
```

**Body:**
```json
{
  "user1_public_key": {...},
  "user2_public_key": {...}
}
```

**Response:**
```json
{
  "message": "PPE certification recorded",
  "user1_id": "user_123",
  "user2_id": "user_456"
}
```

## Voting

### Cast Vote

```bash
POST /polls/{poll_id}/vote
```

**Body:**
```json
{
  "publicKey": {...},
  "option": "Pizza",
  "signature": "base64_signature"
}
```

**Response:**
```json
{
  "message": "Vote recorded successfully"
}
```

### Get Results

```bash
GET /polls/{poll_id}/results
```

**Response:**
```json
{
  "poll_id": "poll_abc123",
  "results": {
    "Pizza": 5,
    "Tacos": 3,
    "Salad": 2
  },
  "total_votes": 10
}
```

## Verification

### Comprehensive Verification

```bash
GET /polls/{poll_id}/verification/comprehensive
```

**Response:**
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["High clustering coefficient"],
  "metrics": {
    "total_participants": 50,
    "total_certifications": 125,
    "valid_votes": 48
  },
  "analysis": {
    "connectivity": {...},
    "suspicious_clusters": []
  }
}
```

### Graph Properties

```bash
GET /polls/{poll_id}/verification/graph-properties
```

### Sybil Detection

```bash
GET /polls/{poll_id}/verification/sybil-detection
```

### Vote Validation

```bash
GET /polls/{poll_id}/verification/vote-validation
```

## Proof Graph

### Get Proof Graph

```bash
GET /polls/{poll_id}/proof/graph
```

**Response:**
```json
{
  "metadata": {
    "poll_id": "poll_abc123",
    "question": "What's for dinner?",
    "num_participants": 50,
    "num_votes": 48
  },
  "participants": [...],
  "certifications": [...],
  "votes": [...],
  "graph_hash": "sha256_hash"
}
```

### Export Proof Graph

```bash
GET /polls/{poll_id}/proof/export
```

Downloads complete proof as JSON file.

## PPE Configuration

### Get Available PPE Types

```bash
GET /ppe/types
```

**Response:**
```json
{
  "available_types": {
    "symmetric_captcha": {
      "name": "Symmetric CAPTCHA",
      "description": "Text-based CAPTCHA",
      "requires_human": true
    }
  }
}
```

### Test Challenge Generation

```bash
POST /ppe/test-challenge
```

**Body:**
```json
{
  "ppe_type": "symmetric_captcha",
  "difficulty": "medium"
}
```

**Response:**
```json
{
  "sample_challenge": "a b c 1 2 3",
  "estimated_effort_seconds": 10
}
```

## WebSocket

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{poll_id}/{user_id}');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

### Send PPE Challenge

```javascript
ws.send(JSON.stringify({
  type: "ppe_challenge",
  target: "peer_user_id",
  challenge: "a b c 1 2 3",
  sessionId: "session_123"
}));
```

### Message Types

- `ppe_challenge` - Send challenge to peer
- `ppe_commitment` - Send commitment
- `ppe_reveal` - Reveal secret and solution
- `ppe_signature` - Exchange signatures
- `ppe_complete` - PPE completed

## Rate Limits

All endpoints: 100 requests/minute per IP

## Error Responses

**400 Bad Request:**
```json
{
  "detail": "Invalid input data"
}
```

**404 Not Found:**
```json
{
  "detail": "Poll not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Server error message"
}
```

## Authentication

Currently no authentication required. For production, add JWT tokens:

```bash
Authorization: Bearer your_jwt_token
```

## CORS

Default CORS allows all origins for development. Configure in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

That's the complete API!