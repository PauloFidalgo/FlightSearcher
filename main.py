from datetime import datetime, timedelta

from src.scraper.play import Scraper
from src.services.database_service import DatabaseService
from src.services.trip_agency_service import TripAgencyService

from src.utils.logger import setup_logging, get_logger


def run():
	database = DatabaseService(database_url='sqlite:///flights.db', echo=False)
	scraper = Scraper()

	try:
		if not database.health_check():
			raise RuntimeError('Database not ready')

		# departure_airports = ['OPO', 'LIS', 'MAD']
		# arrival_airports = ['NRT', 'HND']
		# stay_time = [9, 10, 11]

		# possible_departure_dates = [datetime(year=2026, month=8, day=1) + timedelta(days=x) for x in range(24)]
		# last_possible_day = datetime(year=2026, month=8, day=31)

		departure_airports = ['OPO']
		arrival_airports = ['MAD']
		stay_time = [3, 4]
		possible_departure_dates = [datetime(year=2025, month=11, day=29) + timedelta(days=x) for x in range(50)]
		last_possible_day = datetime(year=2026, month=1, day=1)

		trip_agent = TripAgencyService(database_service=database, scraper=scraper)

		trip_agent.find_daily_flight_combinations(
			possible_trip_starting_points=departure_airports,
			possible_trip_destinations=arrival_airports,
			wanted_stay_time=stay_time,
			possible_start_trip_dates=possible_departure_dates,
			last_vacation_day=last_possible_day,
			save_to_db=False,
		)

	except Exception as e:
		print(f'Unexpected error: {e}')
	finally:
		database.close()


def main() -> None:
	run()


if __name__ == '__main__':
	setup_logging()
	get_logger(__name__).info("Starting application...")
	main()
