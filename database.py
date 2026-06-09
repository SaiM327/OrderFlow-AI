#connects to the actual database

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./orders.db" #use a local SQLite database named orders.db

engine = create_engine( #responsible for talking to the database
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker( #creates a new session for each request --> you open a session, do your database operations, and then close it
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def run_migrations():
    inspector = inspect(engine)

    if not inspector.has_table("orders"):
        return

    columns = {column["name"] for column in inspector.get_columns("orders")}

    if "confirmed_at" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE orders ADD COLUMN confirmed_at DATETIME")
            )


run_migrations()