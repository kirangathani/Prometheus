from typing import List, Dict
import re
import os
import time
from datetime import datetime

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # Common naming convention
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager

from .web_scraper import WebScraper

class HoR(WebScraper):
    BASE_URL: str = "https://disclosures-clerk.house.gov/FinancialDisclosure"
    CURRENT_YEAR: str = str(datetime.now().year)
    
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._set_download_dir()
    
    def _set_download_dir(self) -> str:
        """Responsible for changing the chrome_driver experimental preferences to (1) allow for downloading, and 
        (2) select the correct destination folder for downloads.

        Returns:
            download_dir_path (str): The file path from the cwd to the target download dir.
        """
        self._make_download_dir()
        
        # Configure download behavior after driver creation
        if self.driver:
            self.driver.execute_cdp_cmd('Page.setDownloadBehavior', {
                'behavior': 'allow',
                'downloadPath': self.download_dir_path
            })
            
            time.sleep(2)
        
        return self.download_dir_path
    
    def _make_download_dir(self, dir_name: str = "DisclosureFiles") -> str:
        """Responsible for creating a directory to house the downloaded PDFs showing the disclosure information.

        Returns:
            self.download_dir_path (str): returns the path to the download_dir
        """
        
        # Create the main download dir
        self.download_dir_path = os.path.join(os.getcwd(), dir_name)
        
        if not os.path.exists(self.download_dir_path):
            os.makedirs(self.download_dir_path)
            print(f"Created the download dir with this path: {self.download_dir_path}")
        else:
            print(f"Using exsiting directory as the download dir with the path: {self.download_dir_path}")
        
        print(f"THis is the download dir path from the init function of the child: {self.download_dir_path}")
        
        return self.download_dir_path
    
    def scrape_disclosures(self, years: List[str] = None, people: List[str] = None) -> Dict[str, int]:
        """Returns a list of dictionaries. Each dictionary has the person name, the year, the disclosure
        document ID."""
        
        # Go to the HoR website.
        self._go_to_HoR_website()
        
        # Sleep until the javascript (for the links) has loaded.
        time.sleep(10)
        
        # Validate the year input.
        if not self._year_input_validation(years):
            available_years = self._get_all_years()
            raise ValueError(f"Please input correct years! Here is a list of the available years:\n{available_years}")
        
        available_years = self._get_all_years()
        links = self._get_disclosure_link_hrefs()
        
        if not years:
            years = available_years
        
        # Download the correct FDs    
        year_links = {year: link for year, link in zip(available_years, links)}
        self._download_desired_FDs(years=years, year_links=year_links)
        
        pass
    

    def _download_desired_FDs(self, years: List[str], year_links: Dict[str, str], current_year: str=CURRENT_YEAR) -> None:
        """Responsible for downloading all of the desired FDs into the download dictionary. This is simply done through URL
        navigation with the chrome webdriver. The targeting of the download folder is done during the __init__ function. We will delete an
        existing file if it is for the current year and within the download folder to redownload a file from the web. For non-current year
        files we will simply avoid the download and use the file already within the repo.

        Args:
            years (List[str]): the years for which we want to get FDs for
            year_links (Dict[str, str]): dictionary mapping the years to the PDF links.
            current_year (str): _description_. Defaults to CURRENT_YEAR. The current year.
        """
        
        # Get all the existing zip files...
        existing_files = os.listdir(self.download_dir_path)
        
        # Navigate to each link we need to:
        for year in years:
            if year == current_year:
                is_current_year = True
            else:
                is_current_year = False
        
            existing_duplicate_files = [file for file in existing_files if file.startswith(year) and file.endswith(".zip")]
            
            if existing_duplicate_files: # If there are duplicates...
                if is_current_year:
                    for file in existing_duplicate_files:
                        filepath = os.path.join(self.download_dir_path, file)
                        os.remove(filepath)
                        print(f"Deleting existing file for the current year. Current Year: {year}. Deleted file: {filepath}")
                else:
                    continue # Skipping the url navigation and therefore the file download.
                
            # Get the new file...
            self.go_to_url(year_links[year])
            print(f"Downloading {year_links[year]}")
            while any(file.endswith(".crdownload") for file in os.listdir(self.download_dir_path)):
                time.sleep(1) # Sleep until there are no pending downloads.            
            
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
    
    def _get_disclosure_link_elements(self) -> List[WebElement]:
        """Returns a list of the link objects for the years. Uses the XPATH to find the relevant links."""
        year_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'FD.zip')]")
        return year_links
    
    def _get_disclosure_link_hrefs(self) -> List[str]:
        """Returns a list of hrefs for the years. Uses the WebElement link objects by calling the _get_disclosure_link_elements() function."""
        year_links = self._get_disclosure_link_elements()
        hrefs = [link.get_attribute("href") for link in year_links]
        return hrefs
    
    def _get_all_years(self) -> List[str]:
        """Responsible for calling the private function that gets all the relevant hrefs, then
        using regex to go through these hrefs to find all the years for which there is disclosure information."""
        year_links = self._get_disclosure_link_hrefs()
        years = []
        for link in year_links:
            year_match = re.search(r"(\d{4})FD\.zip", link)
            year = year_match.group(1)
            if year not in years:
                years.append(year)
        print(f"Years return: {years}")
        return years
    
    
                

    
    
    
    
    
    