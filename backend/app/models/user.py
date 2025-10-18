"""
SQLAlchemy models for User and Poll entities.
"""

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Text
from sqlalchemy.sql import func
from datetime import datetime

from app.database import Base


class User(Base):
    """
    User model for SQLAlchemy database.
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    poll_id = Column(String, nullable=False, index=True)
    username = Column(String, nullable=True)
    public_key = Column(Text, nullable=True)  # JSON string of public key
    
    # Registration details
    registration_order = Column(Integer, nullable=True)  # Position in shuffled list
    registered_at = Column(DateTime, server_default=func.now())
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User id={self.id} poll={self.poll_id}>"


class Poll(Base):
    """
    Poll model for SQLAlchemy database.
    """
    __tablename__ = "polls"
    
    id = Column(String, primary_key=True)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON string of options
    
    # PPE paper parameters
    phase = Column(String, default="setup")  # PollPhase enum
    expected_degree = Column(Integer, default=60)  # d from paper
    eta_e = Column(Float, default=0.125)  # ηE: max failed PPE fraction
    eta_v = Column(Float, default=0.025)  # ηV: max deleted node fraction
    session_id = Column(String, nullable=True)  # Unique session ID for graph generation
    
    # Phase timestamps
    created_at = Column(DateTime, server_default=func.now())
    registration_started_at = Column(DateTime, nullable=True)
    certification_started_at = Column(DateTime, nullable=True)
    voting_started_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Settings
    min_verifications_required = Column(Integer, default=2)
    
    def __repr__(self):
        return f"<Poll id={self.id} phase={self.phase}>"


class Vote(Base):
    """
    Vote model for SQLAlchemy database.
    """
    __tablename__ = "votes"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    poll_id = Column(String, nullable=False, index=True)
    
    response = Column(Text, nullable=False)  # The vote choice
    signature = Column(Text, nullable=False)  # Cryptographic signature
    
    # Timestamps
    cast_at = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<Vote user={self.user_id} poll={self.poll_id}>"