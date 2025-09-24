from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Flight:
    arrival_airport: str
    departure_airport: str
    departure_date: datetime
    arrival_date: datetime
    departure_time: datetime
    arrival_time: datetime
    price: float
    total_hours: Optional[float] = 0.0
    companies: Optional[list[str]] = None
    connections: Optional[str] = None

    def _key(self):
        return (self.arrival_airport, self.departure_airport, self.departure_date, self.departure_time, self.arrival_date, self.arrival_time, self.price, self.total_hours)

    def __hash__(self):
        return hash(
            self._key()
        )

    def __eq__(self, other):
        if isinstance(other, Flight):
            return self._key() == other._key()
        return NotImplemented