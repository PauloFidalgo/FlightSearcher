from src.services.flight_search import FlightSearch
from datetime import datetime, timedelta
from dotenv import load_dotenv

def main():
    load_dotenv()

    flight_search: FlightSearch = FlightSearch()

    possible_departures: list[str] = ["OPO", "LIS", "MAD", "BCN"]
    possible_arrivals: list[str] = ["HND", "NRT", "IBR"]
    possible_days: list[int] = list(range(8, 12))

    start_date = datetime(2026, 8, 1)
    end_date = datetime(2026, 8, 31)
    possible_departure_dates: list[datetime] = [start_date + timedelta(days=x) for x in range(23)]

    res = flight_search.search_flights(
        possible_arrivals=possible_arrivals,
        possible_departures=possible_departures,
        possible_departure_dates=possible_departure_dates,
        stay_time=possible_days,
        last_possible_day=end_date,
    )

    print(res)


if __name__ == "__main__":
    main()
