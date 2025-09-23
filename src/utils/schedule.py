from datetime import datetime, timedelta
from ..models.schedule import Schedule, ScheduleEntry

def build_schedule(stay_time: list[int], possible_departure_dates: list[datetime], last_possible_day: datetime) -> Schedule:
    schedule: Schedule = Schedule(options=[])

    for d in possible_departure_dates:
        for s in stay_time:
            end = d + timedelta(days=s)
            if end <= last_possible_day:
                schedule.options.append(ScheduleEntry(departure=d, arrival=end))
    
    return schedule