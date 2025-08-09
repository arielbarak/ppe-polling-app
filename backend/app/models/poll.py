from pydantic import BaseModel, Field
from typing import List, Dict, Any
import uuid

class PollCreate(BaseModel):
    question: str
    options: List[str]

# New model to represent a single, structured vote
class Vote(BaseModel):
    publicKey: Dict[str, Any]
    option: str
    signature: str

class Poll(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    options: List[str]
    registrants: Dict[str, Any] = {}
    # The key is the user_id (hash of public key), value is the Vote object
    votes: Dict[str, Vote] = {}
