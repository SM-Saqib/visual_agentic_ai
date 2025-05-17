from sqlalchemy import text
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.database.base import engine

# Add the client_id column to the users table
with engine.connect() as connection:
    connection.execute(
        text("ALTER TABLE users ADD COLUMN client_id VARCHAR(255) UNIQUE NOT NULL;")
    )

    # commit the changes
    connection.commit()

    # confirm the column was added
    result = connection.execute(
        text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='users';"
        )
    )
    print(result.fetchall())
    print("client_id column added to users table.")
