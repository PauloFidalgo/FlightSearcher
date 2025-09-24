import json
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, String, Table, Text, TypeDecorator
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
	pass


# Association tables for many-to-many relationships
result_departure_flights = Table(
	'result_departure_flights',
	Base.metadata,
	sa.Column('result_id', sa.ForeignKey('result.id'), primary_key=True),
	sa.Column('flight_id', sa.ForeignKey('flight.id'), primary_key=True),
)

result_arrival_flights = Table(
	'result_arrival_flights',
	Base.metadata,
	sa.Column('result_id', sa.ForeignKey('result.id'), primary_key=True),
	sa.Column('flight_id', sa.ForeignKey('flight.id'), primary_key=True),
)

daily_search_results = Table(
	'daily_search_results',
	Base.metadata,
	sa.Column('daily_search_id', sa.ForeignKey('daily_search.id'), primary_key=True),
	sa.Column('result_id', sa.ForeignKey('result.id'), primary_key=True),
)


class DailySearch(Base):
	__tablename__ = 'daily_search'

	id: Mapped[int] = mapped_column(primary_key=True)
	result_date: Mapped[datetime] = mapped_column(DateTime)

	results: Mapped[list['Result']] = relationship('Result', secondary=daily_search_results, back_populates='daily_search_results')


class Result(Base):
	__tablename__ = 'result'

	id: Mapped[int] = mapped_column(primary_key=True)

	departure_flight_airport_1: Mapped[str] = mapped_column(String(20))
	departure_flight_airport_2: Mapped[str] = mapped_column(String(20))
	arrival_flight_airport_1: Mapped[str] = mapped_column(String(20))
	arrival_flight_airport_2: Mapped[str] = mapped_column(String(20))

	departure_date: Mapped[datetime] = mapped_column(DateTime)
	arrival_date: Mapped[datetime] = mapped_column(DateTime)

	departure_flights: Mapped[list['Flight']] = relationship('Flight', secondary=result_departure_flights, back_populates='departure_results')

	arrival_flights: Mapped[list['Flight']] = relationship('Flight', secondary=result_arrival_flights, back_populates='arrival_results')
	daily_search_results: Mapped[list['Result']] = relationship(
		'DailySearch',
		secondary=daily_search_results,
		back_populates='results',
	)

	@property
	def departure_flight_airports(self) -> tuple[str, str]:
		return (self.departure_flight_airport_1, self.departure_flight_airport_2)

	@departure_flight_airports.setter
	def departure_flight_airports(self, value: tuple[str, str]):
		self.departure_flight_airport_1, self.departure_flight_airport_2 = value

	@property
	def arrival_flight_airports(self) -> tuple[str, str]:
		return (self.arrival_flight_airport_1, self.arrival_flight_airport_2)

	@arrival_flight_airports.setter
	def arrival_flight_airports(self, value: tuple[str, str]):
		self.arrival_flight_airport_1, self.arrival_flight_airport_2 = value


class JSONList(TypeDecorator):
	"""Custom SQLAlchemy type for storing Python lists as JSON strings"""

	impl = Text
	cache_ok = True

	def process_bind_param(self, value, dialect):
		"""Convert Python list to JSON string when saving to database"""
		if value is None:
			return None
		if isinstance(value, list):
			return json.dumps(value)
		return value

	def process_result_value(self, value, dialect):
		"""Convert JSON string back to Python list when reading from database"""
		if value is None:
			return None
		if isinstance(value, str):
			try:
				return json.loads(value)
			except (json.JSONDecodeError, TypeError):
				# If it's not valid JSON, return as string (for backwards compatibility)
				return value
		return value


class Flight(Base):
	__tablename__ = 'flight'

	id: Mapped[int] = mapped_column(primary_key=True)
	arrival_airport: Mapped[str] = mapped_column(String(20))
	departure_airport: Mapped[str] = mapped_column(String(20))
	departure_date: Mapped[datetime] = mapped_column(DateTime)
	arrival_date: Mapped[datetime] = mapped_column(DateTime)
	departure_time: Mapped[datetime] = mapped_column(DateTime)
	arrival_time: Mapped[datetime] = mapped_column(DateTime)
	price: Mapped[float] = mapped_column(sa.Float)
	total_hours: Mapped[float] = mapped_column(sa.Float, nullable=True, default=0.0)
	companies: Mapped[str] = mapped_column(JSONList, nullable=True)
	connections: Mapped[str] = mapped_column(String(255), nullable=True)

	departure_results: Mapped[list['Result']] = relationship('Result', secondary=result_departure_flights, back_populates='departure_flights')

	arrival_results: Mapped[list['Result']] = relationship('Result', secondary=result_arrival_flights, back_populates='arrival_flights')

	def _key(self):
		return (
			self.arrival_airport,
			self.departure_airport,
			self.departure_date,
			self.departure_time,
			self.arrival_date,
			self.arrival_time,
			self.price,
			self.total_hours,
		)

	def __hash__(self):
		return hash(self._key())

	def __eq__(self, other):
		if isinstance(other, Flight):
			return self._key() == other._key()
		return NotImplemented
