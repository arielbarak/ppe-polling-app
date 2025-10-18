"""
Database initialization script.
Creates all tables for the PPE polling application.
"""

from app.database import Base, engine
from app.models.user import User, Poll, Vote
from app.models.certification_state import CertificationState


def create_all_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully!")


def drop_all_tables():
    """Drop all database tables (for development)."""
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables dropped!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "drop":
            drop_all_tables()
        elif sys.argv[1] == "create":
            create_all_tables()
        elif sys.argv[1] == "reset":
            drop_all_tables()
            create_all_tables()
        else:
            print("Usage: python init_db.py [create|drop|reset]")
    else:
        create_all_tables()