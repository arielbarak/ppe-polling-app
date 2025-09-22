# Public Verification of Private Effort (PPE) Polling System
This project is a full-stack implementation of the "Public Verification of Private Effort" (PPE) polling protocol, based on the 2014 paper by Alberini, Moran, and Rosen. It provides a secure and private online polling system that is resistant to Sybil attacks and manipulation by a dishonest pollster.

## Overview
The system uses an effort-based mechanism ("one unit of effort, one vote") instead of traditional identity verification. Participants certify each other's effort through a peer-to-peer, symmetric CAPTCHA exchange. The collection of these certifications forms a publicly verifiable graph, ensuring the integrity of the poll's final results.

## Technology Stack
Backend: Python with FastAPI

Frontend: React (built with Vite)

Real-time Communication: WebSockets

Cryptography:

Client-Side: Web Crypto API (SubtleCrypto) for key generation and signing. Private keys never leave the browser.

Server-Side: Python cryptography and pyjwt libraries for signature verification.

## How to Run the Project
This project is designed to be run locally for development and testing.

### Prerequisites
Node.js and npm: Required for the frontend. Download from nodejs.org.

Python 3.9+ and pip: Required for the backend.

### Setup and Running
Clone the repository:

git clone git@github.com:arielbarak/ppe-polling-app.git
cd ppe-polling-app

Set up the Backend:

Navigate to the backend directory:

cd backend

#### Create and activate a virtual environment:

```bash
# On Windows
python -m venv venv
.\venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

#### Install the required Python packages:

```bash
pip install -r requirements.txt
```

#### Backend Dependencies

The backend requires the following key packages (included in requirements.txt):
- FastAPI: Modern web framework for building APIs
- Uvicorn: ASGI server for running FastAPI applications
- WebSockets: For real-time communication
- PyJWT: For handling JWT tokens and cryptographic operations
- Cryptography: For additional cryptographic functions

### Run the backend server:

```bash
# Make sure you're in the backend directory with the virtual environment activated
uvicorn app.main:app --reload --app-dir .
```

The backend will be running at http://localhost:8000.

### Set up the Frontend:

Open a new terminal.

#### Navigate to the frontend directory:

cd frontend

#### Install the required Node.js packages:

npm install

#### Additional Frontend Dependencies

The project uses React Force Graph for network visualization (for the public verification interface):

npm install react-force-graph --save

### Run the frontend development server:

npm run dev

The frontend will be accessible at http://localhost:5173.

## Features

### Poll Creation and Participation
- Create polls with multiple options
- Register as a participant using cryptographic identities
- Verify other participants
- Complete PPE (Proof of Private Effort) challenges with neighbors
- Cast votes securely

### Public Verification
The system includes a public verification interface that allows anyone to verify the integrity of a poll without needing to register or participate. This feature:

- Visualizes the certification graph showing connections between participants
- Validates the graph's expansion properties to ensure Sybil-resistance
- Verifies that all votes were cast by properly certified participants
- Provides metrics on PPE coverage and certification distribution
- Shows transparent poll results with verification status

To use the verification interface:
1. From the home page, enter a Poll ID in the "Verify a Poll" section
2. Or click the "Verify" button next to any poll in the available polls list
3. Examine the certification graph, verification metrics, and poll results

## Testing

The application includes comprehensive test suites to ensure the correct functioning of all components, particularly the critical verification system.

### Running Tests

To run the backend tests:

```bash
# Make sure you're in the backend directory with the virtual environment activated
cd backend
pytest
```

To run specific test categories:

```bash
# Run unit tests only
pytest tests/test_verification.py

# Run API integration tests
pytest tests/test_verification_api.py

# Run graph validation tests
pytest tests/test_graph_validation.py

# Skip stress tests (which can take longer)
pytest -m "not stress"

# Run only stress tests
pytest -m stress
```

### Test Categories

The test suite is organized into several categories:

1. **Unit Tests** (`test_verification.py`): Tests individual functions and components in isolation.

2. **API Integration Tests** (`test_verification_api.py`): Tests the API endpoints and their interaction with services.

3. **Graph Validation Tests** (`test_graph_validation.py`): Specialized tests for the graph validation algorithms.

4. **Stress Tests** (`test_verification_stress.py`): Performance tests for the verification system under load.

5. **Orchestration Tests** (`test_verification_orchestration.py`): End-to-end tests that validate the complete verification flow.

### Manual Testing Guide

To manually verify the system's functionality:

1. **Create a Poll**:
   - Create a new poll with at least 3 options
   - Verify it appears in the poll list

2. **Register Multiple Users**:
   - Open the application in different browser windows (or private/incognito windows)
   - Register at least 5 different participants

3. **Complete PPE Certification**:
   - For each user, verify at least 2 other users
   - Ensure each user is connected to at least 2 others in the certification graph

4. **Cast Votes**:
   - Have at least 3 users cast votes
   - Verify votes are recorded correctly

5. **Verify Poll Integrity**:
   - Use the public verification interface to check the poll
   - Confirm the certification graph is displayed correctly
   - Verify that the poll is marked as valid
   - Check that PPE coverage is at least 80%
   - Ensure minimum certifications per user is at least 2

## Test Coverage

The project includes tools to measure and visualize test coverage for both backend and frontend components, providing insights into the effectiveness of the test suite.

### Backend Test Coverage

To run pytest with coverage reporting and generate a terminal report:

```bash
# Make sure you're in the backend directory with the virtual environment activated
cd backend
pytest --cov=app tests/
```

To generate a detailed HTML coverage report for the backend:

```bash
# Generate HTML report that can be viewed in a browser
cd backend
pytest --cov=app --cov-report=html tests/
```

After running this command, an `htmlcov` directory will be created. Open `htmlcov/index.html` in a browser to view the interactive coverage report, which shows exactly which lines of code are covered by tests.

### Frontend Test Coverage

To run frontend tests with coverage reporting:

```bash
# Make sure you're in the frontend directory
cd frontend
npm run test:coverage
```

This command runs all Vitest tests and generates both a terminal coverage summary and an HTML report. The HTML report is stored in the `coverage` directory; open `coverage/index.html` in a browser to explore the detailed coverage results.

### Coverage Reports in CI/CD

The project is configured to generate coverage reports during continuous integration runs. Coverage reports are archived as artifacts and can be downloaded from the CI/CD pipeline results page.

### Coverage Thresholds

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

