from datetime import datetime

from src.services.database_service import DatabaseException, DatabaseService
from src.services.flight_search_service import FlightSearchService


def daily_check():
	database = DatabaseService(database_url='sqlite:///flights.db', echo=True)

	try:
		if not database.health_check():
			raise RuntimeError('Database health check failed')

		if not database.result_exists_today():
			# departure_airports = ['OPO', 'LIS', 'MAD']
			departure_airports = ['OPO']
			# arrival_airports = ["NRT", "HND"]
			arrival_airports = ['NRT']
			stay_time = [8]
			"""
            possible_departure_dates = [
                datetime(year=2026, month=8, day=1) + timedelta(days=x)
                for x in range(24)
            ]"""
			possible_departure_dates = [datetime(year=2026, month=8, day=1)]

			last_possible_day = datetime(year=2026, month=8, day=31)

			flight_search = FlightSearchService()
			results = flight_search.search_flights(
				possible_departures=departure_airports,
				possible_arrivals=arrival_airports,
				stay_time=stay_time,
				possible_departure_dates=possible_departure_dates,
				last_possible_day=last_possible_day,
			)

			_ = database.create_daily_search(
				results=results,
			)

			print('Created daily_search')
	except DatabaseException as e:
		print(f'Database error: {e}')
	except Exception as e:
		print(f'Unexpected error: {e}')
	finally:
		database.close()


def main() -> None:
	daily_check()


if __name__ == '__main__':
	main()
