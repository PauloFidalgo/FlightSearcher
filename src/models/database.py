import sqlalchemy as sa
from sqlalchemy import String, DateTime, ForeignKey, Table, Date
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column, relationship
from datetime import datetime, date
from typing import List


class Base(DeclarativeBase):
    pass


# Association tables for many-to-many relationships
result_departure_flights = Table(
    "result_departure_flights",
    Base.metadata,
    sa.Column("result_id", sa.ForeignKey("result.id"), primary_key=True),
    sa.Column("flight_id", sa.ForeignKey("flight.id"), primary_key=True),
)

result_arrival_flights = Table(
    "result_arrival_flights",
    Base.metadata,
    sa.Column("result_id", sa.ForeignKey("result.id"), primary_key=True),
    sa.Column("flight_id", sa.ForeignKey("flight.id"), primary_key=True),
)


class Result(Base):
    __tablename__ = "result"

    id: Mapped[int] = mapped_column(primary_key=True)

    departure_flight_airport_1: Mapped[str] = mapped_column(String(20))
    departure_flight_airport_2: Mapped[str] = mapped_column(String(20))
    arrival_flight_airport_1: Mapped[str] = mapped_column(String(20))
    arrival_flight_airport_2: Mapped[str] = mapped_column(String(20))

    result_date: Mapped[date] = mapped_column(Date, unique=True)

    departure_date: Mapped[datetime] = mapped_column(DateTime)
    arrival_date: Mapped[datetime] = mapped_column(DateTime)

    departure_flights: Mapped[List["Flight"]] = relationship(
        "Flight", secondary=result_departure_flights, back_populates="departure_results"
    )

    arrival_flights: Mapped[List["Flight"]] = relationship(
        "Flight", secondary=result_arrival_flights, back_populates="arrival_results"
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


class Flight(Base):
    __tablename__ = "flight"

    id: Mapped[int] = mapped_column(primary_key=True)
    arrival_airport: Mapped[str] = mapped_column(String(20))
    departure_airport: Mapped[str] = mapped_column(String(20))
    departure_date: Mapped[datetime] = mapped_column(DateTime)
    arrival_date: Mapped[datetime] = mapped_column(DateTime)
    departure_time: Mapped[datetime] = mapped_column(DateTime)
    arrival_time: Mapped[datetime] = mapped_column(DateTime)
    price: Mapped[float] = mapped_column(sa.Float)
    total_hours: Mapped[float] = mapped_column(sa.Float, nullable=True, default=0.0)
    companies: Mapped[str] = mapped_column(sa.Text, nullable=True)
    connections: Mapped[str] = mapped_column(String(255), nullable=True)

    departure_results: Mapped[List["Result"]] = relationship(
        "Result", secondary=result_departure_flights, back_populates="departure_flights"
    )

    arrival_results: Mapped[List["Result"]] = relationship(
        "Result", secondary=result_arrival_flights, back_populates="arrival_flights"
    )
