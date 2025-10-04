# PPE Polling App

A secure polling application using Proof of Private Effort (PPE) for Sybil resistance.

## Prerequisites

- Docker
- Docker Compose

## Quick Start with Docker

1. Clone the repository:
```bash
git clone <repository-url>
cd ppe-polling-app
```

2. Start the application:
```bash
docker-compose up --build
```

This will:
- Build and start the frontend (available at http://localhost:5173)
- Build and start the backend API (available at http://localhost:8000)

3. Stop the application:
```bash
docker-compose down
```

## Development

### Frontend Development
The frontend container runs in development mode with hot-reload enabled.
Any changes to the frontend code will automatically reflect in the browser.

### Backend Development
The backend also supports hot-reload. Changes to Python files will automatically
restart the server.

## Container Details

- Frontend: Node.js 22 with Vite and React
- Backend: Python 3.11 with FastAPI
- Ports:
  - Frontend: 5173
  - Backend: 8000

## Troubleshooting

If you encounter any issues:

1. Clean Docker build cache:
```bash
docker-compose build --no-cache
```

2. Remove volumes and rebuild:
```bash
docker-compose down -v
docker-compose up --build
```

3. Check container logs:
```bash
docker-compose logs frontend  # For frontend logs
docker-compose logs backend   # For backend logs
```
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

