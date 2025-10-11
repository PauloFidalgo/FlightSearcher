import contextlib
import csv
import os
import random
import time
from datetime import date, datetime, timedelta

from src.models.database import Flight
from src.scraper.play import Scraper
from src.services.database_service import DatabaseException, DatabaseService


class TripAgencyService:
	def __init__(self, scraper: Scraper, database_service: DatabaseService | None = None) -> None:
		self._scraper: Scraper = scraper
		self._db_service: DatabaseService | None = database_service

	def _get_flights_dict(
		self,
		dep: list[str],
		arr: list[str],
		dt: list[datetime],
	) -> dict[tuple[str, str, datetime], list[Flight]]:
		res: dict[tuple[str, str, datetime], list[Flight]] = dict()

		today = date.today()

		for st_point in dep:
			for trip_dest in arr:
				for dp_date in dt:
					dep_flights_combination = []

					if self._db_service:
						with contextlib.suppress(DatabaseException):
							dep_flights_combination = self._db_service.get_flight_from_to_date(
								dep_air=st_point,
								arr_air=trip_dest,
								dep_dt=dp_date,
								search_date=today,
							)

					if not dep_flights_combination:
						dep_flights_combination = self._scraper.get_flights(departure=st_point, arrival=trip_dest, date=dp_date.strftime('%Y-%m-%d'))

						# Try to mimic the human behavior
						time.sleep(random.uniform(0.05, 5.5))

						if self._db_service:
							with contextlib.suppress(DatabaseException):
								self._db_service.save_unique_flights(dep_flights_combination)

					entry = (st_point, trip_dest, dp_date)
					res[entry] = dep_flights_combination

		return res

	def find_daily_flight_combinations(
		self,
		possible_trip_starting_points: list[str],
		possible_trip_destinations: list[str],
		wanted_stay_time: list[int],
		possible_start_trip_dates: list[datetime],
		last_vacation_day: datetime,
	) -> None:
		valid_starting_points = list(filter(lambda x: x <= last_vacation_day, possible_start_trip_dates))
		departure_flights = self._get_flights_dict(
			dep=possible_trip_starting_points,
			arr=possible_trip_destinations,
			dt=valid_starting_points,
		)

		min_stay = min(wanted_stay_time)
		max_stay = max(wanted_stay_time)
		first_day = min(possible_start_trip_dates)
		last_day = max(possible_start_trip_dates)
		first_arrival_day = first_day + timedelta(days=min_stay)
		last_arrival_day = min(last_vacation_day, last_day + timedelta(days=max_stay))

		num_days = (last_arrival_day - first_arrival_day).days + 1

		valid_return_dates = [first_arrival_day + timedelta(days=x) for x in range(num_days)]

		arrival_flights = self._get_flights_dict(
			dep=possible_trip_destinations,
			arr=possible_trip_starting_points,
			dt=valid_return_dates,
		)

		for (dep_flight_dp, dep_flight_arr, dep_flight_dt), dep_flights in departure_flights.items():
			arr_dates = [dep_flight_dt + timedelta(days=stay_days) for stay_days in wanted_stay_time]
			for arr_date in arr_dates:
				key = (dep_flight_arr, dep_flight_dp, arr_date)
				arr_flights = arrival_flights.get(key, [])

				filename = f'dep_{dep_flight_dp}_{dep_flight_arr}_{dep_flight_dt.strftime("%Y-%m-%d")}__arr_{dep_flight_arr}_{dep_flight_dp}_{arr_date.strftime("%Y-%m-%d")}.csv'
				all_combinations = []
				for dep_flt in dep_flights:
					for arr_flt in arr_flights:
						all_combinations.append((dep_flt, arr_flt))

				if not all_combinations:
					continue

				os.makedirs('outputs', exist_ok=True)
				with open(f'outputs/{filename}', 'w', newline='') as off:
					writer = csv.writer(off)

					# Write CSV headers
					headers = [
						'dep_id',
						'dep_search_date',
						'dep_departure_airport',
						'dep_arrival_airport',
						'dep_departure_date',
						'dep_arrival_date',
						'dep_departure_time',
						'dep_arrival_time',
						'dep_price',
						'dep_total_hours',
						'dep_companies',
						'dep_connections',
						'arr_id',
						'arr_search_date',
						'arr_departure_airport',
						'arr_arrival_airport',
						'arr_departure_date',
						'arr_arrival_date',
						'arr_departure_time',
						'arr_arrival_time',
						'arr_price',
						'arr_total_hours',
						'arr_companies',
						'arr_connections',
						'total_price',
						'trip_duration_days',
					]
					writer.writerow(headers)

					# Write flight combination data
					for dep_flight, arr_flight in all_combinations:
						trip_duration = (arr_flight.departure_date.date() - dep_flight.arrival_date.date()).days
						total_price = (dep_flight.price or 0) + (arr_flight.price or 0)

						row = [
							dep_flight.id if hasattr(dep_flight, 'id') else '',
							dep_flight.search_date.strftime('%Y-%m-%d %H:%M:%S') if dep_flight.search_date else '',
							dep_flight.departure_airport,
							dep_flight.arrival_airport,
							dep_flight.departure_date.strftime('%Y-%m-%d') if dep_flight.departure_date else '',
							dep_flight.arrival_date.strftime('%Y-%m-%d') if dep_flight.arrival_date else '',
							dep_flight.departure_time.strftime('%H:%M') if dep_flight.departure_time else '',
							dep_flight.arrival_time.strftime('%H:%M') if dep_flight.arrival_time else '',
							dep_flight.price or 0,
							dep_flight.total_hours or 0,
							', '.join(dep_flight.companies) if dep_flight.companies else '',
							dep_flight.connections or '',
							arr_flight.id if hasattr(arr_flight, 'id') else '',
							arr_flight.search_date.strftime('%Y-%m-%d %H:%M:%S') if arr_flight.search_date else '',
							arr_flight.departure_airport,
							arr_flight.arrival_airport,
							arr_flight.departure_date.strftime('%Y-%m-%d') if arr_flight.departure_date else '',
							arr_flight.arrival_date.strftime('%Y-%m-%d') if arr_flight.arrival_date else '',
							arr_flight.departure_time.strftime('%H:%M') if arr_flight.departure_time else '',
							arr_flight.arrival_time.strftime('%H:%M') if arr_flight.arrival_time else '',
							arr_flight.price or 0,
							arr_flight.total_hours or 0,
							', '.join(arr_flight.companies) if arr_flight.companies else '',
							arr_flight.connections or '',
							total_price,
							trip_duration,
						]
						writer.writerow(row)
