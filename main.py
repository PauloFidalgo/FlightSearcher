from datetime import datetime, timedelta

from src.services.database_service import DatabaseException, DatabaseService
from src.services.flight_search_service import FlightSearchService


def daily_check():
	database = DatabaseService(database_url='sqlite:///flights.db', echo=False)

	try:
		if not database.health_check():
			raise RuntimeError('Database health check failed')

		if not database.result_exists_today():
			print('Result does not exist for today')
			departure_airports = ['OPO', 'LIS', 'MAD']
			arrival_airports = ["NRT", "HND"]
			stay_time = [9,10,11]
			
			possible_departure_dates = [
                datetime(year=2026, month=8, day=1) + timedelta(days=x)
                for x in range(24)
            ]

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

			print(f'Created daily_search, with {len(results)} results')
		else:
			daily_search = database.get_today_search()
			
			for result in daily_search.results:
				print(result)

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
