import json
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, String, Text, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
	pass


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

	# Add unique constraint for the combination of fields
	__table_args__ = (
		UniqueConstraint(
			'search_date',
			'arrival_airport',
			'departure_airport',
			'departure_date',
			'arrival_date',
			'departure_time',
			'arrival_time',
			'total_hours',
			'companies',
			'connections',
			name='uq_flight_details',
		),
	)

	id: Mapped[int] = mapped_column(primary_key=True)
	search_date: Mapped[datetime] = mapped_column(DateTime)
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

	@classmethod
	def by_search_date(cls, search_date):
		"""Helper method for querying by search date"""
		from sqlalchemy import func

		return func.date(cls.search_date) == search_date

	@classmethod
	def by_departure_date(cls, departure_date):
		"""Helper method for querying by departure date"""
		from sqlalchemy import func

		return func.date(cls.departure_date) == departure_date
