# PPE Polling System 🗳️

A Sybil-resistant polling system using Proof of Private Effort (PPE). Based on the research paper by Canetti et al.

## What is this?

A voting system where you prove you're human by solving challenges with other voters. No central authority needed. Cryptographically verifiable. Resistant to fake accounts.

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker (optional)

### Run with Docker (easiest)

```bash
# Clone the repo
git clone https://github.com/arielbarak/ppe-polling-app.git
cd ppe-polling-app

# Start everything
docker-compose up
```

Then open http://localhost:3000

### Run manually

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

Backend runs at http://localhost:8000, frontend at http://localhost:3000

## How it works

1. **Registration** - Solve a CAPTCHA to register
2. **PPE Protocol** - Exchange challenges with assigned neighbors
3. **Vote** - Cast your vote (only after PPE is complete)
4. **Verify** - Anyone can verify the poll's integrity

The system prevents Sybil attacks by requiring mutual effort between users. Fake accounts can't collude without detection.

## Features

- ✅ One-sided PPE for registration
- ✅ Symmetric CAPTCHA for bidirectional PPE
- ✅ Ideal graph for neighbor assignment
- ✅ Cryptographic proof graphs
- ✅ Advanced Sybil detection
- ✅ Modular PPE architecture
- ✅ Real-time WebSocket communication
- ✅ Complete verification algorithms

## Testing

```bash
# Run all tests
cd backend
pytest

# Run simulations
python -m pytest tests/simulation/ -v
```

## Documentation

- [Deployment Guide](docs/DEPLOYMENT.md) - Production deployment
- [API Reference](docs/API.md) - Complete API docs
- [Architecture Overview](docs/ARCHITECTURE.md) - How it works
- [Developer Guide](docs/DEVELOPMENT.md) - Contributing
- [Research Summary](docs/RESEARCH.md) - Paper explanation

## Project Structure

```
├── backend/               # FastAPI backend
│   ├── app/
│   │   ├── models/       # Data models
│   │   ├── routes/       # API endpoints
│   │   ├── services/     # Business logic
│   │   ├── utils/        # Utilities
│   │   └── ppe/          # PPE implementations
│   └── tests/            # Tests and simulations
├── frontend/             # React frontend
│   └── src/
│       ├── components/   # UI components
│       ├── services/     # API clients
│       └── ppe/          # PPE handlers
└── docs/                 # Documentation
```

## License

MIT

## Citation

Based on: Canetti, R., et al. "PPE Polling: Proof of Private Effort for Sybil-Resistant Polling Systems"

## Contributing

See [DEVELOPMENT.md](docs/DEVELOPMENT.md)

The project aims to maintain the following coverage thresholds:
- Backend: Minimum 70% line coverage
- Frontend: Minimum 60% line coverage
- Critical components (cryptography, verification): Minimum 85% coverage

### Complete Coverage Report

A comprehensive test coverage report for the entire project can be generated using:

```bash
# Generate combined coverage report
cd ppe-polling-app
./generate_coverage_report.sh
```

This script runs both backend and frontend coverage tools and generates a consolidated report in the project root directory.

