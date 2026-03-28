import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

echo = os.getenv("SQL_ECHO", "false").lower() == "true"

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set — check your .env file")

engine = create_engine(DATABASE_URL, echo=echo)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
