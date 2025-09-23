from playwright.sync_api import sync_playwright
from selectolax.parser import HTMLParser
from datetime import datetime
from ..models.flight import Flight

class Scraper:
    def get_flights(self, departure: str, arrival: str, date: str, adults: int = 1) -> list[Flight]:
        url: str = f"https://www.momondo.pt/flight-search/{departure}-{arrival}/{date}/{adults}adults?fs=fdDir=false&ucs=1oi53hh&sort=bestflight_a"

        html: str = self.fetch_momondo_html(url=url)
        print(html)
        return []

    def fetch_momondo_html(self, url: str) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.wait_for_selector('ul.resultsList__results')
            html_content = page.content()
            browser.close()
            return html_content

    def parse_momondo_flights(html: str):
        tree = HTMLParser(html)
        results = []

        for card in tree.css('li.resultWrapper'):
            airline = card.css_first('span.airlineName')
            price = card.css_first('span.price')
            duration = card.css_first('span.duration')

            if airline and price and duration:
                results.append({
                    "airline": airline.text(),
                    "price": price.text(),
                    "duration": duration.text(),
                })
        return results