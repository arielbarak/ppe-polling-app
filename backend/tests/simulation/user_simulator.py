"""
Simulated user for testing.

Handles complete user lifecycle: registration, PPE, voting.
"""

import asyncio
import httpx
import websockets
import json
from typing import Optional, Dict, List, Set
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
import base64
import secrets


class SimulatedUser:
    """
    Simulates a user going through the PPE polling protocol.
    """
    
    def __init__(self, user_id: str, base_url: str = "http://localhost:8000"):
        self.user_id = user_id
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws")
        
        # Cryptographic identity
        self.private_key = None
        self.public_key = None
        self.public_key_jwk = None
        
        # Protocol state
        self.registered_polls: Set[str] = set()
        self.ppe_certifications: Dict[str, Set[str]] = {}  # poll_id -> set of certified peers
        self.votes: Dict[str, str] = {}  # poll_id -> option
        
        # WebSocket connection
        self.websocket = None
        self.ws_messages = []
        
        # Performance tracking
        self.timings = {
            "registration": [],
            "ppe_completion": [],
            "vote_cast": []
        }
    
    def generate_keypair(self):
        """Generate EC keypair for this user."""
        self.private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        self.public_key = self.private_key.public_key()
        
        # Convert to JWK format
        public_numbers = self.public_key.public_numbers()
        x = public_numbers.x.to_bytes(32, byteorder='big')
        y = public_numbers.y.to_bytes(32, byteorder='big')
        
        self.public_key_jwk = {
            "kty": "EC",
            "crv": "P-256",
            "x": base64.urlsafe_b64encode(x).decode().rstrip('='),
            "y": base64.urlsafe_b64encode(y).decode().rstrip('=')
        }
    
    def sign_message(self, message: str) -> str:
        """Sign a message with private key."""
        signature = self.private_key.sign(
            message.encode(),
            ec.ECDSA(hashes.SHA256())
        )
        return base64.b64encode(signature).decode()
    
    async def register_for_poll(self, poll_id: str, solve_captcha: bool = True) -> bool:
        """
        Register for a poll with PPE challenge.
        
        Args:
            poll_id: Poll identifier
            solve_captcha: Whether to solve the CAPTCHA (True = honest, False = attack)
            
        Returns:
            True if registration successful
        """
        import time
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                # Get registration challenge
                response = await client.post(
                    f"{self.base_url}/polls/{poll_id}/register",
                    json={"publicKey": self.public_key_jwk},
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    print(f"User {self.user_id[:8]}: Registration request failed")
                    return False
                
                data = response.json()
                challenge_text = data.get("challengeText", "")
                
                # Solve CAPTCHA
                if solve_captcha:
                    solution = challenge_text.replace(" ", "")
                else:
                    # Attacker submits random solution
                    solution = secrets.token_hex(4)
                
                # Submit solution
                response = await client.post(
                    f"{self.base_url}/polls/{poll_id}/register/verify",
                    json={
                        "publicKey": self.public_key_jwk,
                        "solution": solution
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    self.registered_polls.add(poll_id)
                    elapsed = time.time() - start_time
                    self.timings["registration"].append(elapsed)
                    print(f"User {self.user_id[:8]}: Registered in {elapsed:.2f}s")
                    return True
                else:
                    print(f"User {self.user_id[:8]}: Registration verification failed")
                    return False
                    
        except Exception as e:
            print(f"User {self.user_id[:8]}: Registration error: {e}")
            return False
    
    async def connect_websocket(self, poll_id: str):
        """Connect to WebSocket for real-time PPE."""
        try:
            ws_uri = f"{self.ws_url}/ws/{poll_id}/{self.user_id}"
            self.websocket = await websockets.connect(ws_uri)
            print(f"User {self.user_id[:8]}: WebSocket connected")
            return True
        except Exception as e:
            print(f"User {self.user_id[:8]}: WebSocket connection failed: {e}")
            return False
    
    async def perform_ppe_with_peer(self, poll_id: str, peer_id: str) -> bool:
        """
        Perform complete PPE protocol with a peer.
        
        Simplified simulation - assumes both parties cooperate.
        
        Args:
            poll_id: Poll identifier
            peer_id: Peer user ID
            
        Returns:
            True if PPE completed successfully
        """
        import time
        start_time = time.time()
        
        try:
            # In real implementation, this would go through full protocol
            # For simulation, we just record the certification
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/polls/{poll_id}/ppe-certification",
                    json={
                        "user1_public_key": self.public_key_jwk,
                        "user2_public_key": {"kty": "EC", "x": peer_id, "y": peer_id}  # Simplified
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    if poll_id not in self.ppe_certifications:
                        self.ppe_certifications[poll_id] = set()
                    self.ppe_certifications[poll_id].add(peer_id)
                    
                    elapsed = time.time() - start_time
                    self.timings["ppe_completion"].append(elapsed)
                    print(f"User {self.user_id[:8]}: PPE with {peer_id[:8]} completed in {elapsed:.2f}s")
                    return True
                return False
                
        except Exception as e:
            print(f"User {self.user_id[:8]}: PPE error: {e}")
            return False
    
    async def vote(self, poll_id: str, option: str) -> bool:
        """
        Cast a vote on a poll.
        
        Args:
            poll_id: Poll identifier
            option: Option to vote for
            
        Returns:
            True if vote successful
        """
        import time
        start_time = time.time()
        
        try:
            # Sign vote
            message = f"{poll_id}:{option}"
            signature = self.sign_message(message)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/polls/{poll_id}/vote",
                    json={
                        "publicKey": self.public_key_jwk,
                        "option": option,
                        "signature": signature
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    self.votes[poll_id] = option
                    elapsed = time.time() - start_time
                    self.timings["vote_cast"].append(elapsed)
                    print(f"User {self.user_id[:8]}: Voted for '{option}' in {elapsed:.2f}s")
                    return True
                else:
                    print(f"User {self.user_id[:8]}: Vote failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"User {self.user_id[:8]}: Vote error: {e}")
            return False
    
    async def disconnect_websocket(self):
        """Disconnect WebSocket."""
        if self.websocket:
            await self.websocket.close()
            print(f"User {self.user_id[:8]}: WebSocket disconnected")
    
    def get_average_timings(self) -> Dict[str, float]:
        """Get average timings for operations."""
        import statistics
        result = {}
        for operation, times in self.timings.items():
            if times:
                result[operation] = {
                    "mean": statistics.mean(times),
                    "median": statistics.median(times),
                    "min": min(times),
                    "max": max(times)
                }
        return result