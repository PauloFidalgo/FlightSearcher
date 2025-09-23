from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Flight:
    arrival_airport: str
    departure_airport: str
    departure_date: datetime
    arrival_date: datetime
    price: float
    total_hours: Optional[float] = 0.0
    companies: Optional[list[str]] = None
