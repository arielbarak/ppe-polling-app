"""
Proof-of-Storage PPE implementation.

From Appendix B: "Prover demonstrates access to cloud storage
(e.g., Google Drive, Dropbox) by retrieving and processing a
challenge file uploaded by verifier."

This is useful for:
- Proving access to existing accounts (harder for Sybils)
- Lower cognitive load than CAPTCHAs
- Verifiable through standard APIs
"""

import hashlib
import secrets
import json
from typing import Dict, Any, Tuple, Optional
import logging

from app.services.ppe.base import PPEProtocol
from app.models.ppe_types import PPEType, PPEDifficulty

logger = logging.getLogger(__name__)


class ProofOfStoragePPE(PPEProtocol):
    """
    Proof-of-Storage PPE.
    
    Protocol:
    1. Verifier generates random challenge data
    2. Verifier uploads challenge file to shared location (or via API)
    3. Prover retrieves file
    4. Prover computes hash of file content
    5. Prover sends hash back
    6. Verifier verifies hash matches
    
    Security: Prover must have legitimate access to storage account.
    Sybil attacker needs to create/access multiple storage accounts.
    """
    
    def __init__(
        self,
        difficulty: PPEDifficulty = PPEDifficulty.MEDIUM,
        storage_provider: str = "generic"
    ):
        super().__init__(
            ppe_type=PPEType.PROOF_OF_STORAGE,
            difficulty=difficulty,
            completeness_sigma=0.98,  # High success rate (just file retrieval)
            soundness_epsilon=0.02    # Low false positive
        )
        
        self.storage_provider = storage_provider
        
        # File size based on difficulty
        self.file_size_map = {
            PPEDifficulty.EASY: 1024,         # 1 KB
            PPEDifficulty.MEDIUM: 10240,      # 10 KB
            PPEDifficulty.HARD: 102400,       # 100 KB
            PPEDifficulty.EXTREME: 1024000    # 1 MB
        }
    
    def generate_challenge(self, session_id: str, prover_id: str, verifier_id: str) -> Dict[str, Any]:
        """
        Generate storage challenge.
        
        Returns challenge data with:
        - Random file content
        - Expected hash
        - Upload instructions
        """
        file_size = self.file_size_map[self.difficulty]
        
        # Generate random file content
        random_data = secrets.token_bytes(file_size)
        
        # Compute expected hash
        expected_hash = hashlib.sha256(random_data).hexdigest()
        
        # Generate challenge file name
        challenge_filename = f"ppe_challenge_{session_id}_{prover_id[:8]}.bin"
        
        return {
            "challenge_id": hashlib.sha256(f"{session_id}:{prover_id}".encode()).hexdigest()[:16],
            "challenge_data": {
                "filename": challenge_filename,
                "file_size": file_size,
                "storage_provider": self.storage_provider,
                "instructions": self._get_storage_instructions(self.storage_provider),
                # In production, verifier would upload file and return share link
                "share_link": f"https://storage.example.com/challenges/{challenge_filename}"
            },
            "verification_data": {
                "expected_hash": expected_hash,
                "file_content": random_data.hex(),  # Store for verification
                "session_id": session_id
            }
        }
    
    def verify_response(
        self,
        challenge_data: Dict[str, Any],
        verification_data: Dict[str, Any],
        prover_response: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify prover retrieved and processed file correctly.
        """
        prover_hash = prover_response.get("file_hash", "")
        expected_hash = verification_data["expected_hash"]
        
        if not prover_hash:
            return False, "No hash provided"
        
        if prover_hash.lower() != expected_hash.lower():
            return False, "Hash mismatch - file not retrieved correctly"
        
        # Additional check: verify prover actually accessed storage
        # (Could check access logs, but omitted for simplicity)
        
        return True, None
    
    def estimate_effort_seconds(self) -> int:
        """Estimate time to retrieve and hash file."""
        # Time to: authenticate, download, hash
        effort_map = {
            PPEDifficulty.EASY: 15,      # Small file, quick
            PPEDifficulty.MEDIUM: 30,    # Medium file
            PPEDifficulty.HARD: 60,      # Large file
            PPEDifficulty.EXTREME: 120   # Very large file
        }
        return effort_map[self.difficulty]
    
    def _get_storage_instructions(self, provider: str) -> Dict[str, str]:
        """Get provider-specific instructions."""
        instructions = {
            "google_drive": {
                "step_1": "Click the share link",
                "step_2": "Download the challenge file",
                "step_3": "Compute SHA-256 hash of file",
                "step_4": "Submit hash"
            },
            "dropbox": {
                "step_1": "Access the Dropbox link",
                "step_2": "Download the file",
                "step_3": "Calculate SHA-256 hash",
                "step_4": "Return the hash"
            },
            "generic": {
                "step_1": "Access the storage link provided",
                "step_2": "Download the challenge file",
                "step_3": "Compute SHA-256 hash: sha256sum <filename>",
                "step_4": "Submit the hash value"
            }
        }
        return instructions.get(provider, instructions["generic"])


class GoogleDriveStoragePPE(ProofOfStoragePPE):
    """Google Drive specific implementation."""
    
    def __init__(self, difficulty: PPEDifficulty = PPEDifficulty.MEDIUM):
        super().__init__(difficulty=difficulty, storage_provider="google_drive")
        # In production: integrate with Google Drive API


class DropboxStoragePPE(ProofOfStoragePPE):
    """Dropbox specific implementation."""
    
    def __init__(self, difficulty: PPEDifficulty = PPEDifficulty.MEDIUM):
        super().__init__(difficulty=difficulty, storage_provider="dropbox")
        # In production: integrate with Dropbox API