from typing import List
import random
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC # Common naming convention
from webdriver_manager.chrome import ChromeDriverManager


class WebScraper:
    def __init__(self, headless=True, timeout=10, user_agent=None, chrome_options=None):
        """
        Initialize WebScraper with configurable options.

        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Default timeout for waits in seconds
            user_agent (str): Custom user agent string
            chrome_options (list): Additional Chrome options
        """
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.wait = None
        self.scraped_data = []

        # Default Chrome options for stealth scraping
        self.chrome_options = [
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu'
        ]
    
        # Set user agent
        self.user_agent = user_agent or self._get_random_user_agent()

        # Initialize driver on creation
        self._setup_driver()

    def _get_random_user_agent(self):
        """Return a realistic user agent to avoid detection."""
        agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ]
        return random.choice(agents)
        
    def _setup_driver(self) -> None:
        """
        Configure and initialize Chrome WebDriver with stealth options.
        """
        try:            
            # Configure Chrome options
            options = Options()
            
            # Add headless mode if specified
            if self.headless:
                options.add_argument('--headless')
            
            # Add all predefined chrome options
            for option in self.chrome_options:
                options.add_argument(option)
            
            # Setting the user agent we defined in the __init__()
            options.add_argument(f'--user-agent={self.user_agent}')
            
            # Disabling chrome's native automation detection apparatus
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Auto-download and setup ChromeDriver. Install has built-in cache detection system. Will reuse ChromDriver if already installed witin cache. .install() returns the path to the relevant ChromDriver exe (which the Service instance needs to know)
            service = Service(ChromeDriverManager().install())
            
            # Initialize driver
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Remove webdriver property to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Setup WebDriverWait
            self.wait = WebDriverWait(self.driver, self.timeout)
            
            print(f"Chrome driver initialized successfully (headless: {self.headless})")
            
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            raise e
    
    def go_to_url(self, url, wait_for_element=None, max_retries=3) -> bool:
        """
        Navigate to a URL with error handling and optional element waiting.
        
        Args:
            url (str): The URL to navigate to
            wait_for_element (tuple): Optional (By, locator) to wait for after navigation. `By` is the parameter we will watch out for, and `locator` is the value of the aforementioned param we will look out for.
            once we see the correct value in the correct param of any element in the html, then we will stop waiting.
            max_retries (int): Number of retry attempts for failed navigation
            
        Returns:
            bool: True if navigation successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                print(f"Navigating to: {url} (attempt {attempt + 1}/{max_retries})")
                
                # Navigate to URL
                self.driver.get(url)
                
                # .until() takes a func and repeatedly calls it with the self.driver passed as the arg. self.wait has self.driver because we passed self.driver into the WebDriverWait constructor.
                self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete") # Func returns a bool showing whether the document is ready.
                
                # Wait for specific element if provided
                if wait_for_element:
                    self.wait.until(EC.presence_of_element_located(wait_for_element)) # EC.presence_of_element_located checks to see if an element can be found. `wait_for_element` contains the data specifying the element to wait for.
                    print(f"Element {wait_for_element} found - page loaded successfully") # Once the awaited element is found, we can say that the page has been loaded.
                
                print(f"Successfully navigated to: {self.driver.current_url}")
                return True
                
            except Exception as e:
                print(f"Navigation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    print(f"Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
                else:
                    print(f"Failed to navigate to {url} after {max_retries} attempts")
                    return False
        
        return False