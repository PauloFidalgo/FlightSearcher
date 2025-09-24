from dataclasses import dataclass
from datetime import datetime
from .flight import Flight

@dataclass
class Result:
    departure_flight_airports: tuple[str, str]
    arrival_flight_airports: tuple[str, str]
    departure_date: datetime
    arrival_date: datetime
    departure_flights: list[Flight]
    arrival_flights: list[Flight]