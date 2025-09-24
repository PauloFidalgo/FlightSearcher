import os
from datetime import datetime, timedelta
from ..scraper.play import Scraper
from ..models.flight import Flight
from ..models.result import Result

class FlightSearch:
    def __init__(self) -> None:
        self.scraper = Scraper()

    def search_flights(self, 
                       possible_departures: list[str], 
                       possible_arrivals: list[str], 
                       stay_time: list[int], 
                       possible_departure_dates: list[datetime],
                       last_possible_day: datetime) -> Result:
        
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
        max_stay = max(stay_time)
        min_arrival = min(possible_departure_dates) + timedelta(days=min_stay)
        max_arrival = min(max(possible_departure_dates) + timedelta(days=max_stay), last_possible_day)
        num_days = (max_arrival - min_arrival).days + 1

        possible_arrival_dates = [min_arrival + timedelta(days=x) for x in range(num_days)]

        for dep_airport in possible_departures:
            for arr_airport in possible_arrivals:
                for arr_date in possible_arrival_dates:
                    entry = (dep_airport, arr_airport, arr_date)
                    date_search = arr_date.strftime("%Y-%m-%d")
                    flights = self.scraper.get_flights(dep_airport, arr_airport, date_search)
                    arrival_flights[entry] = flights

        results = []
                
        for (dep_air, arr_air, dep_dt), dep_flights in departure_flights.items():
            for (ret_dep_air, ret_arr_air, arr_dt), arr_flights in arrival_flights.items():
                if arr_dt >= dep_dt + timedelta(days=min_stay) and arr_dt <= dep_dt + timedelta(days=max_stay):
                    res_entry = Result(
                        departure_flight_airports=(dep_air, arr_air),
                        arrival_flight_airports=(ret_dep_air, ret_arr_air),
                        departure_date=dep_dt,
                        arrival_date=arr_dt,
                        departure_flights=dep_flights,
                        arrival_flights=arr_flights
                    )

                    results.append(res_entry)

        return results


