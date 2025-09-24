from datetime import datetime, timedelta
from src.services.flight_search import FlightSearch
from src.services.database import DatabaseService, DatabaseException

def daily_check():
    database = DatabaseService(database_url="sqlite:///flights.db", echo=True)
    
    try:
        if not database.health_check():
            raise RuntimeError("Database health check failed")
        
        if not database.result_exists_today():
            departure_airports = ['OPO', 'LIS', 'MAD']
            arrival_airports = ['NRT', 'HND']
            stay_time = list(range(8, 12))
            possible_departure_dates = [datetime(year=2026, month=8, day=1) + timedelta(days=x) for x in range(24)]
            last_possible_day = datetime(year=2026, month=8, day=31)

            flight_search = FlightSearch()
            result = flight_search.search_flights(
                possible_departures=departure_airports,
                possible_arrivals=arrival_airports,
                stay_time=stay_time,
                possible_departure_dates=possible_departure_dates,
                last_possible_day=last_possible_day,
            )

            res = database.create_result(
                departure_airports=result.departure_flight_airports,
                arrival_airports=result.arrival_flight_airports,
                departure_date=result.departure_date,
                arrival_date=result.arrival_date,
                departure_flights=result.departure_flights,
                arrival_flights=result.arrival_flights,
            )

            print(f"Created result: {res.id}")
    except DatabaseException as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        database.close()

def main() -> None:
    daily_check()
            

if __name__ == "__main__":
    main()
