"""Database initialization script — creates tables."""

from models.database import Base, engine


def init_db() -> None:
    """Create all tables. No seed users — all users must register."""
    Base.metadata.create_all(bind=engine)
    print("Database initialized")


if __name__ == "__main__":
    init_db()
