import os
from datetime import datetime, timedelta
from ..scraper.play import Scraper
from ..models.flight import Flight

class FlightSearch:
    def __init__(self) -> None:
        self.scraper = Scraper()

    def search_flights(self, possible_departures: list[str], possible_arrivals: list[str], stay_time: list[int], possible_departure_dates: list[datetime], last_possible_day: datetime):
        departure_flights: dict[tuple[str, str, datetime], list[Flight]] = {}
        arrival_flights: dict[tuple[str, str, datetime], list[Flight]] = {}

        for dep_airport in possible_departures:
            for arr_airport in possible_arrivals:
                for dep_date in possible_departure_dates:
                    entry = (dep_airport, arr_airport, dep_date)
                    date_search = dep_date.strftime("%Y-%m-%d")
                    flights = self.scraper.get_flights(dep_airport, arr_airport, date_search)
                    departure_flights[entry] = flights

        min_stay = min(stay_time)
        possible_arrival_dates = [min(possible_departure_dates) + timedelta(days=x) for x in range(min_stay, 31) if (min(possible_departure_dates) + timedelta(days=x)) < last_possible_day]

        for dep_airport in possible_departures:
            for arr_airport in possible_arrivals:
                for arr_date in possible_arrival_dates:
                    entry = (dep_airport, arr_airport, arr_date)
                    date_search = arr_date.strftime("%Y-%m-%d")
                    flights = self.scraper.get_flights(dep_airport, arr_airport, date_search)
                    arrival_flights[entry] = flights
