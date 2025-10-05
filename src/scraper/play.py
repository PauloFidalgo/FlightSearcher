import heapq
import random
import re
import time
from datetime import date, datetime, timedelta

from playwright.sync_api import Page, sync_playwright
from playwright_stealth import Stealth
from selectolax.parser import HTMLParser

from src.models.database import Flight


class Scraper:
	USER_AGENTS = [
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
		'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
		'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0',
	]

	VIEWPORTS = [
		{'width': 1280, 'height': 720},
		{'width': 1366, 'height': 768},
		{'width': 1440, 'height': 900},
		{'width': 1536, 'height': 864},
		{'width': 1600, 'height': 900},
		{'width': 1680, 'height': 1050},
	]

	def _filter_flights(self, flights: list[Flight]) -> list[Flight]:
		if not flights:
			return []

		cheapest = heapq.nsmallest(5, flights, key=lambda x: x.price or float('inf'))
		fastest = heapq.nsmallest(5, flights, key=lambda x: x.total_hours or float('inf'))

		unique_flights = set(cheapest + fastest)

		return list(unique_flights)

	def get_flights(self, departure: str, arrival: str, date: str, adults: int = 1) -> list[Flight]:
		url: str = f'https://www.momondo.pt/flight-search/{departure}-{arrival}/{date}/{adults}adults?fs=fdDir=false&ucs=1oi53hh&sort=bestflight_a'

		html: str = self.fetch_momondo_html(url=url)

		flights = self.parse_momondo_flights(html, departure, arrival, date)

		return self._filter_flights(flights=flights)

	def _handle_cookie_consent(self, page: Page):
		"""Handle cookie consent with more human-like behavior"""
		try:
			time.sleep(random.uniform(1, 2))

			cookie_selectors = ["text='Aceitar tudo'", "text='Accept all'", "[data-testid='accept-all']", '.cookie-accept', '#cookie-accept']

			for selector in cookie_selectors:
				try:
					locator = page.locator(selector)
					if locator.count() > 0:
						for i in range(locator.count()):
							if locator.nth(i).is_visible():
								time.sleep(random.uniform(0.5, 1.5))
								locator.nth(i).click()
								time.sleep(random.uniform(1, 2))
								return
				except Exception as e:
					print(f'Error handling cookie consent: {e}')
					continue

		except Exception as e:
			print(f'Error handling cookie consent: {e}')

	def fetch_momondo_html(self, url: str) -> str:
		with Stealth().use_sync(sync_playwright()) as p:
			browser = p.chromium.launch(
				headless=True,
				args=['--disable-blink-features=AutomationControlled', '--enable-webgl', '--use-gl=swiftshader', '--enable-accelerated-2d-canvas'],
			)

			viewport = random.choice(self.VIEWPORTS)
			user_agent = random.choice(self.USER_AGENTS)
			context = browser.new_context(
				user_agent=user_agent,
				viewport={'width': viewport['width'], 'height': viewport['height']},
			)

			page = context.new_page()

			page.goto(url, timeout=60000)

			self._handle_cookie_consent(page)

			for _ in range(5):
				random_x = random.uniform(-100.0, 100.0)
				random_y = random.uniform(-200.0, 200.0)

				init_x = random_x
				init_y = random_y
				for _ in range(15):
					delta_x = random.choice([1, -1, 0])
					delta_y = random.choice([1, -1, 0])
					page.mouse.move(init_x + delta_x, init_y + delta_y)
				page.mouse.wheel(random_x, random_y)
				time.sleep(random.uniform(0.05, 1.5))

			page.wait_for_function(
				"""() => {
                    const el = document.querySelector('div[role="progressbar"]');
                    return el && el.getAttribute('aria-hidden') === 'true';
                }""",
				timeout=60000,
			)

			html_content = page.content()
			browser.close()
			return html_content

	def parse_momondo_flights(self, html: str, departure_airport: str, arrival_airport: str, dt: str) -> list[Flight]:
		try:
			tree = HTMLParser(html)
		except Exception as e:
			print(f'Error parsing HTML: {e}')
			return []

		flights: list[Flight] = []

		base_date = datetime.strptime(dt, '%Y-%m-%d')

		flight_cards = tree.css('div.nrc6-inner')

		for card in flight_cards:
			try:
				# ---- Times and Connections ----
				times = [span.text().strip() for span in card.css('div.vmXl span') if span.text().strip() != '–']
				if len(times) >= 3:
					dep_time_str = times[0]
					arr_parts = times[1].split('+')
					arr_time_str = arr_parts[0]
					extra_days = int(arr_parts[1]) if len(arr_parts) > 1 else 0
					connections = times[2].strip()

					dep_time = datetime.strptime(dep_time_str, '%H:%M')
					arr_time = datetime.strptime(arr_time_str, '%H:%M')

					dep_dt = base_date.replace(hour=dep_time.hour, minute=dep_time.minute)
					arr_dt = base_date.replace(hour=arr_time.hour, minute=arr_time.minute) + timedelta(days=extra_days)

					# ---- Total time ----
					total_time_div = card.css_first('div.xdW8-mod-full-airport')
					total_time_str = total_time_div.text().strip() if total_time_div else None
					total_hours = None
					if total_time_str:
						match = re.match(r'(?:(\d+)h)?\s*(?:(\d+)m)?', total_time_str)
						if match:
							hours = int(match.group(1)) if match.group(1) else 0
							minutes = int(match.group(2)) if match.group(2) else 0
							total_hours = hours + minutes / 60

					# ---- Company ----
					company_div = card.css_first('div.J0g6-operator-text')
					companies = [company.strip() for company in company_div.text().split('•')] if company_div else []

					# ---- Price ----
					price_div = card.css_first('div.e2GB-price-text')
					price = None
					if price_div:
						price_text = price_div.text().strip()
						price = float(re.sub(r'[^\d,]', '', price_text).replace(',', '.'))

					today = date.today()

					flights.append(
						Flight(
							departure_airport=departure_airport,
							arrival_airport=arrival_airport,
							search_date=today,
							departure_date=dep_dt,
							arrival_date=arr_dt,
							departure_time=dep_dt,
							arrival_time=arr_dt,
							price=price,
							total_hours=total_hours,
							companies=companies,
							connections=connections,
						)
					)

			except Exception as e:
				print(f'Error parsing flight card: {e}')
				print(f'Error type: {type(e).__name__}')
				continue

		return flights
