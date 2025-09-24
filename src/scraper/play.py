import os
import random
from datetime import datetime, timedelta
from selectolax.parser import HTMLParser
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
import re
import heapq

from ..models.flight import Flight


class Scraper:
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) Gecko/20100101 Firefox/118.0",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    ]

    def _filter_flights(self, flights: list[Flight]) -> list[Flight]:
        if not flights:
            return []

        cheapest = heapq.nsmallest(5, flights, key=lambda x: x.price or float('inf'))
        fastest = heapq.nsmallest(5, flights, key=lambda x: x.total_hours or float('inf'))

        unique_flights = set(cheapest + fastest)

        return list(unique_flights)

    def get_flights(self, departure: str, arrival: str, date: str, adults: int = 1) -> list[Flight]:
        url: str = (
            f"https://www.momondo.pt/flight-search/"
            f"{departure}-{arrival}/{date}/{adults}adults?fs=fdDir=false&ucs=1oi53hh&sort=bestflight_a"
        )

        html: str = self.fetch_momondo_html(url=url)

        flights = self.parse_momondo_flights(html, departure, arrival, date)
        return self._filter_flights(flights=flights)

    def fetch_momondo_html(self, url: str) -> str:
        user_agent = random.choice(self.USER_AGENTS)

        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.set_extra_http_headers({"User-Agent": user_agent})

            page.goto(url, timeout=60000)

            try:
                locator = page.locator("text='Aceitar tudo'")
                count = locator.count()
                for i in range(count):
                    if locator.nth(i).is_visible():
                        locator.nth(i).click()
                        break
            except Exception:
                pass

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

    def parse_momondo_flights(self, html: str, departure_airport: str, arrival_airport: str, date: str):
        tree = HTMLParser(html)
        flights = []

        base_date = datetime.strptime(date, "%Y-%m-%d")

        for card in tree.css('div.nrc6-inner'):
            try:
                # ---- Times and Connections ----
                times = [span.text().strip() for span in card.css('div.vmXl span') if span.text().strip() != '–']
                if len(times) >= 3:
                    dep_time_str = times[0]
                    arr_parts = times[1].split('+')
                    arr_time_str = arr_parts[0]
                    extra_days = int(arr_parts[1]) if len(arr_parts) > 1 else 0
                    connections = times[2].strip()

                    dep_time = datetime.strptime(dep_time_str, "%H:%M")
                    arr_time = datetime.strptime(arr_time_str, "%H:%M")

                    dep_dt = base_date.replace(hour=dep_time.hour, minute=dep_time.minute)
                    arr_dt = base_date.replace(hour=arr_time.hour, minute=arr_time.minute) + timedelta(days=extra_days)
                else:
                    dep_dt = arr_dt = connections = None

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

                flights.append(Flight(
                    departure_airport=departure_airport,
                    arrival_airport=arrival_airport,
                    departure_date=dep_dt,
                    arrival_date=arr_dt,
                    departure_time=dep_dt,
                    arrival_time=arr_dt,
                    price=price,
                    total_hours=total_hours,
                    companies=companies,
                    connections=connections,
                ))

            except Exception as e:
                print("Error parsing card:", e)
                continue

        return flights
