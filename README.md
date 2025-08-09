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

python -m venv venv
.\venv\Scripts\activate

##### Install the required Python packages:

pip install -r requirements.txt

### Run the backend server:

python -m uvicorn app.main:app --reload --port 8000

The backend will be running at http://localhost:8000.

### Set up the Frontend:

Open a new terminal.

#### Navigate to the frontend directory:

cd frontend

#### Install the required Node.js packages:

npm install

### Run the frontend development server:

npm run dev

The frontend will be accessible at http://localhost:5173.
