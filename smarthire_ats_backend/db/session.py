import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Driver: mysql-connector-python → SQLAlchemy URL scheme mysql+mysqlconnector://
# https://docs.sqlalchemy.org/en/20/dialects/mysql.html#mysqlconnector
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+mysqlconnector://user:password@127.0.0.1:3306/smarthire_ats?charset=utf8mb4",
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
