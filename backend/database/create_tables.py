from backend.database.base import engine, Base
from backend.models.models import *  # Import all models to ensure they are registered with Base


def create_all_tables():
    """
    Create all tables in the database using SQLAlchemy's Base metadata.
    """
    try:
        print("Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("All tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")


if __name__ == "__main__":
    create_all_tables()
