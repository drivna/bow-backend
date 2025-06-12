from typing import Optional
from sqlalchemy import create_engine, Engine
import os
from dotenv import load_dotenv


class DatabaseEngine:
    engine: Optional[Engine] = None

    @classmethod
    def create_mysql_db_engine(cls) -> Engine:
        if cls.engine is not None:
            return cls.engine

        load_dotenv()

        environment = os.getenv("ENVIRONMENT")

        if environment == "TEST":
            # Use in-memory SQLite for testing environment
            cls.engine = create_engine("sqlite:///:memory:", echo=True)
        else:
            # Ensure the database is in the root of the project
            db_user: str = os.getenv("DB_USER", "postgres")
            db_password: str = os.getenv("DB_PASSWORD", "local")
            db_host: str = os.getenv("DB_HOST", "localhost")
            db_port: str = os.getenv("DB_PORT", "5432")
            db_name: str = os.getenv("DB_NAME", "bow_db")

            postgres_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

            cls.engine = create_engine(postgres_url, echo=True)

        return cls.engine
