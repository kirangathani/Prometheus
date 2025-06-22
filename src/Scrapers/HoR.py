from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # Common naming convention
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from .web_scraper import WebScraper

class HoR(WebScraper):
    BASE_URL = "https://disclosures-clerk.house.gov/FinancialDisclosure"
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
    
    def scrape_disclosures(self, years: List[int] = None, people: List[str] = None) -> Dict[str, int]:
        """Returns a list of dictionaries. Each dictionary has the person name, the year, the disclosure
        document ID."""
        
        # Go to the HoR website.
        self._go_to_HoR_website()
        
        # Validate the year input.
        self._year_input_validation(years)
        
        if years:
            for year in years:
                pass
        pass
    
    def _go_to_HoR_website(self, url=BASE_URL) -> None:
        self.go_to_url(url)
    
    def _year_input_validation(self, years: List[int]) -> bool:
        """Returns False if any inputted year not present on the website."""
        if years:
            for year in years:
                try:
                    # Check if the year is present on the webpage.
                    locator = (By.PARTIAL_LINK_TEXT, str(year))
                    self.wait.until(EC.presence_of_element_located(locator))
                except TimeoutException as e:
                    print(f"The year {year} has not yet been uploaded to the website.")
                    return False
        return True
    
    def _get_all_years(self) -> List[str]:
        """Returns a list of the available years."""
        
        available_years = []
        
        year_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'FD.zip')]")
        
        print(f"Found {len(year_links)} year links")
        for link in year_links:
            href = link.get_attribute('href')
            if href:
                # Extract year from href like: '/public_disc/financial-pdfs/2025FD.zip'
                import re
                year_match = re.search(r'(\d{4})FD\.zip', href)
                if year_match:
                    year = year_match.group(1)
                    print(f"Found year: {year}")
                    if year not in available_years:
                        available_years.append(year)
        
        return available_years

    
                

    
    
    
    
    
    