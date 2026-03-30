import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Driver: mysql-connector-python → SQLAlchemy URL scheme mysql+mysqlconnector://
# https://docs.sqlalchemy.org/en/20/dialects/mysql.html#mysqlconnector
_raw_url = os.getenv("MYSQL_URL")
if not _raw_url:
    raise RuntimeError(
        "MYSQL_URL environment variable is not set. "
        "Ensure the Railway MySQL service is linked and MYSQL_URL is configured."
    )

# Railway's MySQL service provides the URL with the plain `mysql://` scheme.
# SQLAlchemy requires `mysql+mysqlconnector://` to use the mysql-connector-python
# driver that is installed in this project.
DATABASE_URL = _raw_url.replace("mysql://", "mysql+mysqlconnector://", 1)

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
