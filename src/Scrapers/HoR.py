from typing import List, Dict
import re
import os
import time
import json
from datetime import datetime
import zipfile
import xmltodict

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
    HORXML_PATH: str = os.path.join(os.getcwd(), "HoRXMLs")
    HORJSON_PATH: str = os.path.join(os.getcwd(), "HoRJSONs")
    
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
            
            time.sleep(2) # Time to allow the command to take effect.
        
        return self.download_dir_path
    
    def _make_download_dir(self, dir_name: str = "HoRFDs") -> str:
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
        
        # Download the correct FDs into HoRFDs    
        year_links = {year: link for year, link in zip(available_years, links)}
        self._download_desired_FDs(years=years, year_links=year_links)
        
        time.sleep(5)
        
        # Extract the HTML XML files from the HoRFDs and put into the HoRXML
        self._download_desired_XMLs(years=years)
        
        # Convert the extracted XML files to JSON format in the HoRJSON folder.
        self._convert_XMLs_to_JSONs()
        
        pass
    
    def _convert_XMLs_to_JSONs(self, hor_xml_path: str=HORXML_PATH, hor_json_path: str=HORJSON_PATH) -> None:
        """Responsible for iterating through all of the xml files in the hor_xml_path folder, then converting each of them
        to a json file of the same name in the json folder (just with the .json extension instead).

        Args:
            hor_xml_path (str): the path for the folder for the xml files. Defaults to HORXML_PATH.
            hor_json_path (str): the path for the folder for the json files. Defaults to HORJSON_PATH.
        """
        
        for file in os.listdir(hor_xml_path):
            if file.endswith(".xml"):
                xml_file_path = os.path.join(hor_xml_path, file)
                json_file_path = os.path.join(hor_json_path, file.replace(".xml", ".json"))
                
                with open(xml_file_path, "r", encoding="utf-8") as file:
                    xml_content = file.read()
                    
                data_dict = xmltodict.parse(xml_content)
                
                with open(json_file_path, "w", encoding="utf-8") as file:
                    json.dump(data_dict, file, indent=4, ensure_ascii=False)
                
                print(f"Converted file: {xml_file_path} to json: {json_file_path}")
        
    
    def _download_desired_XMLs(self, years: List[str], current_year: str=CURRENT_YEAR, hor_xml_path: str=HORXML_PATH) -> None:
        """Responsible for (1) going through the hor_xml_path folder to check whether we have existing files. If we are on the current year then it will delete old files.
        if we are on a new year, then it will abort the download process. The download process involved entering the self.download_dir_path folder, taking the relevant file names
        through checking the years of the file names, then getting the one with the highest bracketed number (TODO - this might be overkill maybe we can get rid of this and just
        impose stricter data validation for the hor_fd_path folder). We then extract the .xml file from the relevant zip file and add it to the hor_xml_path folder.

        Args:
            years (List[str]): list of years for which the user wants to scrape data.
            current_year (str, optional): current year - taken with datetime. Defaults to CURRENT_YEAR.
            hor_xml_path (str, optional): path to the destination folder for the HTML XML files which have the data. Defaults to HORXML_PATH.

        Raises:
            FileNotFoundError: Happens when we cannot find the HTML XML file in the zip file for the relevant year.
        """
        
        for year in years:
            if year == current_year:
                is_current_year = True
            else:
                is_current_year = False
                
            existing_duplicate_files = [file for file in os.listdir(hor_xml_path) if file.startswith(year)]
            
            if existing_duplicate_files:
                if is_current_year:
                    for file in existing_duplicate_files:    
                        filepath = os.path.join(hor_xml_path, file)
                        os.remove(filepath)
                        print(f"We have removed the filepath: {filepath} as it is an old version for the current year ({year})")
                else:
                    continue # Keep old files if not the current year.
                
            # Get all candidate zip files for that year.
            relevant_zip_files = [os.path.join(self.download_dir_path, file) for file in os.listdir(self.download_dir_path) if file.startswith(f"{year}FD") and file.endswith(".zip")]
            print(f"These are the relevant zip files for the year ({year}). {relevant_zip_files}")
            
            # Choose relevant zip file from these.
            max_number = -1
            relevant_zip_file = None
            for file in relevant_zip_files:
                filename = os.path.basename(file)
                number = self._extract_number_from_filename(filename)
                if number > max_number:
                    max_number = number
                    relevant_zip_file = file
            
            with zipfile.ZipFile(relevant_zip_file, "r") as zip_file:
                contents = zip_file.namelist()
                
                xml_file = None
                for file in contents:
                    if file.endswith(".xml"):
                        xml_file = file
                        break
                if not xml_file:
                    raise FileNotFoundError(f"Error! We cannot seem to find a .xml file in the FD zip file. Please double check. This is the zip file path in question: {relevant_zip_file}.\nThese are the contents: \n{contents}")
            
                zip_file.extract(xml_file, hor_xml_path)
                print(f"Extracted HTML file ({xml_file}) and placed in this folder: {hor_xml_path}")
    
    def _extract_number_from_filename(self, filename: str) -> int:
        match = re.search(r"\((\d+)\)", filename)
        if match:
            return int(match.group(1))
        else:
            return 0

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
    
    
                

    
    
    
    
    
    