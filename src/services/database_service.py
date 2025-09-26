from collections.abc import Generator
from contextlib import contextmanager
from datetime import date
from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect, select, func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.models.database import Base, DailySearch, Result


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

	def result_exists_today(self) -> bool:
		try:
			with self.get_session() as session:
				today = date.today()
				stmt = select(DailySearch).where(func.date(DailySearch.result_date) == today)
				result = session.execute(stmt).first()
				exists = result is not None

				return exists
		except Exception as e:
			raise DatabaseException(f'Failed to check daily result: {e}') from e

	def get_today_search(self) -> DailySearch | None:
		try:
			with self.get_session() as session:
				today = date.today()
				stmt = select(DailySearch).where(func.date(DailySearch.result_date) == today)
				result = session.execute(stmt).scalar_one_or_none()

				if result:
					for res in result.results:
						_ = res.departure_flights
						_ = res.arrival_flights

				session.expunge_all()
				return result
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to retrieve todays result: {e}') from e

	def get_search_by_date(self, target_date: date) -> DailySearch | None:
		try:
			with self.get_session() as session:
				stmt = select(DailySearch).where(func.date(DailySearch.result_date) == target_date)
				result = session.execute(stmt).scalar_one_or_none()

				if result:
					for res in result.results:
						_ = res.departure_flights
						_ = res.arrival_flights

				session.expunge_all()
				return result
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to retrieve result for {target_date}: {e}') from e

	def get_all_results(self) -> list[DailySearch]:
		try:
			with self.get_session() as session:
				stmt = select(DailySearch).order_by(DailySearch.result_date.desc())
				results = session.execute(stmt).scalars().all()

				for result in results:
					for res in result.results:
						_ = res.departure_flights
						_ = res.arrival_flights

				return list(results)
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to retrieve results: {e}') from e

	def create_daily_search(self, results: list[Result]) -> DailySearch:
		try:
			with self.get_session() as session:
				result = DailySearch(
					result_date=date.today(),
					results=results,
				)

				session.add(result)
				session.flush()
				session.refresh(result)

				return result
		except IntegrityError as e:
			raise DatabaseException(f'Result already exists for date {date.today()}: {e}') from e
		except SQLAlchemyError as e:
			raise DatabaseException(f'Failed to create model: {e}') from e

	def close(self) -> None:
		if self._engine:
			self._engine.dispose()
