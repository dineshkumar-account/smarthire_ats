import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Driver: mysql-connector-python → SQLAlchemy URL scheme mysql+mysqlconnector://
# https://docs.sqlalchemy.org/en/20/dialects/mysql.html#mysqlconnector
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Ensure the Railway MySQL service is linked and DATABASE_URL is configured."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
