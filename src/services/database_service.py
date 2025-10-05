from collections.abc import Generator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from sqlalchemy import Engine, create_engine, func, inspect, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.models.database import Base, Flight


class DatabaseException(Exception):
	"""Custom Exception for Database Service"""

	pass


class DatabaseService:
	def __init__(self, database_url: str, echo: bool = True) -> None:
		self.database_url = database_url
		self.echo = echo

		self._engine: Engine | None = None
		self._session_factory: sessionmaker | None = None

		self._initialize_database()

	def _database_exists(self) -> bool:
		db_path = self.database_url.replace('sqlite:///', '')
		exists = Path(db_path).exists()
		return exists

	def _tables_exist(self) -> bool:
		try:
			if not self._engine:
				return False

			inspector = inspect(self._engine)
			existing_tables = inspector.get_table_names()

			required_tables = set(Base.metadata.tables.keys())
			existing_tables_set = set(existing_tables)

			missing_tables = required_tables - existing_tables_set

			return bool(not missing_tables)
		except Exception:
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
			raise DatabaseException(f'Database initialization failed: {e}') from e

	@contextmanager
	def get_session(self) -> Generator[Session, None, None]:
		if not self._session_factory:
			raise DatabaseException('Database not initialized')

		session = self._session_factory()

		try:
			yield session
			session.commit()
		except Exception as e:
			session.rollback()
			raise DatabaseException(f'Database session error: {e}') from e
		finally:
			session.close()

	def health_check(self) -> bool:
		try:
			with self.get_session() as session:
				session.execute(select(1))
				return True
		except Exception:
			return False

	def get_search_by_date(self, target_date: date) -> list[Flight]:
		try:
			with self.get_session() as session:
				stmt = select(Flight).where(func.date(Flight.search_date) == target_date)
				result = session.execute(stmt).scalars().all()

				session.expunge_all()
				return list(result)
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to retrieve result for {target_date}: {e}') from e

	def get_flight_from_to_date(self, dep_air: str, arr_air: str, dep_dt: date, search_date: date) -> list[Flight]:
		try:
			with self.get_session() as session:
				stmt = select(Flight).where(
					func.date(Flight.departure_date == dep_dt),
					func.date(Flight.search_date == search_date),
					Flight.departure_airport == dep_air,
					Flight.arrival_airport == arr_air,
				)
				results = session.execute(stmt).scalars().all()

				return list(results)
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to retrieve results: {e}') from e

	def flight_exists(self, flight: Flight) -> bool:
		"""Check if a flight with the same unique fields already exists in the database"""
		try:
			with self.get_session() as session:
				stmt = select(Flight).where(
					Flight.search_date == flight.search_date,
					Flight.arrival_airport == flight.arrival_airport,
					Flight.departure_airport == flight.departure_airport,
					Flight.departure_date == flight.departure_date,
					Flight.arrival_date == flight.arrival_date,
					Flight.departure_time == flight.departure_time,
					Flight.arrival_time == flight.arrival_time,
					Flight.total_hours == flight.total_hours,
					Flight.companies == flight.companies,
					Flight.connections == flight.connections,
				)
				result = session.execute(stmt).first()
				return result is not None
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to check if flight exists: {e}') from e

	def save_flights(self, flights: list[Flight]) -> None:
		"""Save a list of flights to the database"""
		if not flights:
			return

		try:
			with self.get_session() as session:
				session.add_all(flights)
		except IntegrityError as e:
			raise DatabaseException(f'Duplicate flight data: {e}') from e
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to save flights: {e}') from e

	def save_unique_flights(self, flights: list[Flight]) -> None:
		"""Save only unique flights to the database, returning count of flights saved"""
		if not flights:
			return

		unique_flights = []
		for flight in flights:
			if not self.flight_exists(flight):
				unique_flights.append(flight)

		if unique_flights:
			self.save_flights(unique_flights)

	def close(self) -> None:
		if self._engine:
			self._engine.dispose()
