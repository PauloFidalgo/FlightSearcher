from pydantic import BaseModel
from datetime import datetime

class ScheduleEntry(BaseModel):
    departure: datetime
    arrival: datetime

class Schedule(BaseModel):
    options: list[ScheduleEntry]