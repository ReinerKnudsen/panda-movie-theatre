from database import engine
from sqlmodel import text

with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print("Verbindung erfolgreich:", result.fetchone())
