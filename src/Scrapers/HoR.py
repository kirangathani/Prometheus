from typing import List, Dict
import re
import os
import time

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
        self._set_download_dir()
    
    def _set_download_dir(self) -> str:
        """Responsible for extending the chrome_options attribute of the parent class to include some
        settings for the downloading of files. Including setting the correct filepath for the downloads

        Returns:
            download_dir_path (str): The file path from the cwd to the target download dir.
        """
        self._make_download_dir()
        
        download_options = [
            f'--download-default-directory={self.download_dir_path}',
            '--disable-web-security',  # Sometimes needed for downloads
            '--allow-running-insecure-content'  # Sometimes needed for downloads
        ]
        
        print(f"These are the attributes of the class: {self.__str__()}")
        
        self.chrome_options.extend(download_options)
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
        links = self._get_disclosure_links_by_year()
        
        if not years:
            years = available_years
            
        year_links = {year: link for year, link in zip(available_years, links)}
        print(f"These are the year-link pairs:{year_links}") 
        
        
        # Navigate to each link we need to:
        for year in years:
            print(f"This is the year we are on: {year}")
            existing_files = set(os.listdir(self.download_dir_path))
            
            page_title = self.driver.title
            print(f"This is the page title: {page_title} for this link: {year_links[year]}")
            
            self.go_to_url(year_links[year]) # Go to url to download.
            
            timeout = 30
            start_time = time.time()
            downloaded_file = None
            while (time.time() - start_time) < timeout:
                time.sleep(1)
        
                current_files = set(os.listdir(self.download_dir_path))
                print(f"Here are the names of the current files: {current_files}")
                new_files = current_files - existing_files
                print(f"Here are the names of the new files: {new_files}")    
                
                for file in new_files:
                    print(f"We have entered, the new files for loop - there is at least one new file!")
                    print(f"THis is the new file name: {file}")
                    if file.startswith(f"{year}FD") and file.endswith(".zip"):
                        print(f"This file {file}, Passed the new file check.")
                        downloaded_file = os.path.join(self.download_dir_path, file)
                        print(f"Downloaded file: {downloaded_file}")
                        break # Break from the for loop
                
                if downloaded_file:
                    break # break from the while loop
            
            if not downloaded_file:
                raise FileNotFoundError(f"File download failed due to downloaded_file not existing for this link: {year_links[year]}")
            
            if not os.path.exists(downloaded_file):
                raise FileNotFoundError(f"File download failed for {year_links[year]}!") 
        
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
    
    def _get_disclosure_links_by_year(self) -> List[str]:
        """Returns a list of hrefs for the years. Uses the XPATH to find the relevant links."""
        year_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'FD.zip')]")
        print(f"Link return:{[link.get_attribute("href") for link in year_links]}")
        return [link.get_attribute("href") for link in year_links]
    
    def _get_all_years(self) -> List[str]:
        """Responsible for calling the private function that gets all the relevant hrefs, then
        using regex to go through these hrefs to find all the years for which there is disclosure information."""
        year_links = self._get_disclosure_links_by_year()
        years = []
        for link in year_links:
            year_match = re.search(r"(\d{4})FD\.zip", link)
            year = year_match.group(1)
            if year not in years:
                years.append(year)
        print(f"Years return: {years}")
        return years
    
    
                

    
    
    
    
    
    