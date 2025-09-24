from contextlib import contextmanager
from datetime import date, datetime
from typing import List, Optional, Generator
from sqlalchemy import create_engine, select, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..models.database import Base, Result, Flight
from pathlib import Path
import os

class DatabaseException(Exception):
    """Custom Exception for Database Service"""
    pass

class DatabaseService:
    def __init__(self, database_url: str, echo: bool = True) -> None:
        self.database_url = database_url
        self.echo = echo

        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

        self._initialize_database()

    def _database_exists(self) -> bool:
        db_path = self.database_url.replace('sqlite:///', '')
        exists = Path(db_path).exists()
        return exists
    
    def _tables_exist(self) -> bool:
        try:
            if not self._engine:
                return False
            
            inspector = inspector(self._engine)
            existing_tables = inspector.get_table_names()

            required_tables = set(Base.metadata.tables.keys())
            existing_tables_set = set(existing_tables)

            missing_tables = required_tables - existing_tables_set

            return True if not missing_tables else False
        except Exception as e:
            return False


    def _initialize_database(self) -> None:
        try:
            db_exists = self._database_exists()

            self._engine = create_engine(
                self.database_url,
                echo=self.echo,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            )

            if db_exists and self._tables_exist():
                return 
            
            Base.metadata.create_all(self._engine)
        except SQLAlchemyError as e:
            raise DatabaseException(f"Database initialization failed: {e}")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        if not self._session_factory:
            raise DatabaseException(f"Database not initialized")

        session = self._session_factory()

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseException(f"Database session error: {e}")
        finally:
            session.close()

    def health_check(self) -> bool:
        try:
            with self.get_session() as session:
                session.execute(select(1))
                return True
        except Exception as e:
            return False

    def result_exists_today(self) -> bool:
        try:
            with self.get_session() as session:
                today = date.today()
                stmt = select(Result).where(Result.result_date == today)
                result = session.execute(stmt).first()
                exists = result is not None

                return exists
        except Exception as e:
            raise DatabaseException(f"Failed to check daily result: {e}")

    def get_today_result(self) -> Optional[Result]:
        try:
            with self.get_session() as session:
                today = date.today()
                stmt = select(Result).where(Result.result_date == today)
                result = session.execute(stmt).scalar_one_or_none()

                if result:
                    _ = result.departure_flights
                    _ = result.arrival_flights

                return result
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve todays result: {e}")

    def get_result_by_date(self, target_date: date) -> Optional[Result]:
        try:
            with self.get_session() as session:
                stmt = select(Result).where(Result.result_date == target_date)
                result = session.execute(stmt).scalar_one_or_none()

                if result:
                    _ = result.departure_flights
                    _ = result.arrival_flights

                return result
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve result for {target_date}: {e}")

    def get_all_results(self) -> list[Result]:
        try:
            with self.get_session() as session:
                stmt = select(Result).order_by(Result.result_date.desc())
                results = session.execute(stmt).scalars().all()

                for result in results:
                    _ = result.departure_flights
                    _ = result.arrival_flights

                return list(results)
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to retrieve results: {e}")

    def create_result(self,
                      departure_airports: tuple[str, str],
                      arrival_airports: tuple[str, str],
                      departure_date: datetime,
                      arrival_date: datetime,
                      departure_flights: list[Flight],
                      arrival_flights: list[Flight]) -> Result:
        try:
            with self.get_session() as session:
                result = Result(
                    result_date=date.today(),
                    departure_date=departure_date,
                    arrival_date=arrival_date,
                )

                result.departure_flight_airports = departure_airports
                result.arrival_flight_airports = arrival_airports
                result.departure_flights = departure_flights
                result.arrival_flights = arrival_flights

                session.add(result)
                session.flush()
                session.refresh(result)

                return result
        except IntegrityError as e:
            raise DatabaseException(f"Result already exists for date {date.today()}: {e}")
        except SQLAlchemyError as e:
            raise DatabaseException(f"Failed to create model: {e}")
        
    def close(self) -> None:
        if self._engine:
            self._engine.dispose()
