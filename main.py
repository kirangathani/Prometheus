from src import Scrapers
import time

hor_scraper = Scrapers.HoR()

hor_scraper.scrape_disclosures()

links = hor_scraper._get_disclosure_links_by_year()
print(f"These are the links from calling from main:{links}")



