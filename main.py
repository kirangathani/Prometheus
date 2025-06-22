from src import Scrapers
import time

hor_scraper = Scrapers.HoR()
hor_scraper._go_to_HoR_website()

# Sleeping
time.sleep(10)

# Simple debugging to see if these elements actually have text
hor_scraper._debug_year_links()

years = hor_scraper._get_all_years()
print(years)


