from pydantic import BaseModel, Field
from typing import List, Dict, Any, Set
import uuid

class PollCreate(BaseModel):
    question: str
    options: List[str]

class Vote(BaseModel):
    publicKey: Dict[str, Any]
    option: str
    signature: str

class UserVerification(BaseModel):
    verified_by: Set[str] = Field(default_factory=set)
    has_verified: Set[str] = Field(default_factory=set)

class Poll(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[str]
    registrants: Dict[str, Any] = {}
    votes: Dict[str, Vote] = {}
    # Map of user_id to their verification status
    verifications: Dict[str, UserVerification] = Field(default_factory=dict)
    # Map of user_id to set of peers they have completed PPE with
    ppe_certifications: Dict[str, Set[str]] = Field(default_factory=dict)
    
    def can_vote(self, user_id: str, min_verifications: int = 2) -> bool:
        """Check if a user has enough verifications to vote"""
        if user_id not in self.verifications:
            return False
        return len(self.verifications[user_id].verified_by) >= min_verifications
    
    def add_verification(self, verifier_id: str, verified_id: str) -> None:
        """Record a verification between two users"""
        # Initialize verification records if they don't exist
        if verifier_id not in self.verifications:
            self.verifications[verifier_id] = UserVerification()
        if verified_id not in self.verifications:
            self.verifications[verified_id] = UserVerification()
            
        # Record the verification
        self.verifications[verifier_id].has_verified.add(verified_id)
        self.verifications[verified_id].verified_by.add(verifier_id)
    
    def add_ppe_certification(self, user1_id: str, user2_id: str) -> None:
        """Record a PPE certification between two users (bidirectional)"""
        # Initialize PPE records if they don't exist
        if user1_id not in self.ppe_certifications:
            self.ppe_certifications[user1_id] = set()
        if user2_id not in self.ppe_certifications:
            self.ppe_certifications[user2_id] = set()
            
        # Record the PPE certification (bidirectional)
        self.ppe_certifications[user1_id].add(user2_id)
        self.ppe_certifications[user2_id].add(user1_id)
    
    def get_ppe_certifications(self, user_id: str) -> Set[str]:
        """Get all PPE certifications for a user"""
        return self.ppe_certifications.get(user_id, set())
