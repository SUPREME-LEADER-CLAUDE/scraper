# scraper.py

"""
This module contains the code for the backend,
that will handle the scraping process
"""

from time import sleep
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from base import Base
from scroller import Scroller
from communicator import Communicator
from database import DataSaver
from parser import Parser  # Import the Parser class
import signal
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def signal_handler(sig, frame):
    logging.info('CTRL+C detected. Shutting down driver...')
    if hasattr(signal_handler, 'driver'):
        signal_handler.driver.quit()
    sys.exit(0)

# Register the signal handler for CTRL+C
signal.signal(signal.SIGINT, signal_handler)

class Backend(Base):

    def __init__(self, searchquery, outputformat, headlessmode, location=None, lat_center=None, long_center=None, start_angle=None, end_angle=None):
        self.searchquery = searchquery
        self.location = location
        self.lat_center = lat_center
        self.long_center = long_center
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.outputformat = outputformat
        self.headlessMode = headlessmode
        Communicator.set_output_format(outputformat)  # Set output format in headless mode
        self.data_saver = DataSaver()  # Instantiate the DataSaver class
        self.init_driver()
        signal_handler.driver = self.driver  # Attach driver to the signal handler
        self.scroller = Scroller(driver=self.driver, searchquery=self.searchquery)
        self.parser = Parser(driver=self.driver, searchquery=self.searchquery)  # Instantiate the Parser class with searchquery

    def init_driver(self):
        options = webdriver.ChromeOptions()
        if self.headlessMode == 1:
            options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Explicitly set the path to the Google Chrome binary
        options.binary_location = "/usr/bin/google-chrome"

        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)

        Communicator.show_message("Opening browser...")
        logging.debug("Initializing ChromeDriver with options: %s", options.arguments)

        try:
            # Automatically get the matching ChromeDriver version
            service = Service(ChromeDriverManager().install())
            logging.debug("ChromeDriver service initialized.")
        except Exception as e:
            Communicator.show_message(f"Error downloading ChromeDriver: {str(e)}")
            logging.error(f"Error downloading ChromeDriver: {e}")
            sys.exit(1)

        self.driver = webdriver.Chrome(service=service, options=options)
        logging.debug("ChromeDriver initialized successfully.")

        self.driver.maximize_window()
        self.driver.implicitly_wait(self.timeout)

    def mainscraping(self):
        data = []
        try:
            querywithplus = "+".join(self.searchquery.split())
            if self.lat_center and self.long_center:
                link_of_page = f"https://www.google.com/maps/search/{querywithplus}/@{self.lat_center},{self.long_center},14z"
            else:
                locationwithplus = "+".join(self.location.split())
                link_of_page = f"https://www.google.com/maps/search/{querywithplus}+in+{locationwithplus}/"
            self.openingurl(url=link_of_page)
            Communicator.show_message("Working start...")
            sleep(1)
            self.scroller.scroll()
            all_results_links = self.get_all_results_links()
            data = self.collect_data(all_results_links)
        except Exception as e:
            Communicator.show_message(f"Error occurred while scraping. Error: {str(e)}")
            logging.error(f"Error occurred while scraping: {e}")
        finally:
            try:
                Communicator.show_message("Closing the driver")
                self.driver.close()
                self.driver.quit()
            except Exception as e:
                Communicator.show_message(f"Error occurred while closing the driver. Error: {str(e)}")
                logging.error(f"Error occurred while closing the driver: {e}")
            Communicator.end_processing()

            # Save data using DataSaver
            Communicator.show_message(f"Saving data: {data}")
            if len(data) >= 5:  # Ensure data has at least 5 entries before saving and uploading
                self.data_saver.save(data, self.searchquery)  # Pass searchquery to DataSaver.save()
            else:
                Communicator.show_message(f"Not enough data collected to save. Only {len(data)} entries found.")
                logging.warning(f"Not enough data collected to save. Only {len(data)} entries found.")
        return data

    def collect_data(self, all_results_links):
        Communicator.show_message(f"Collecting data from links: {all_results_links}")
        self.parser.main(all_results_links)
        return self.parser.finalData

    def get_all_results_links(self):
        results_links = []
        try:
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a.result-title")
            for elem in elements:
                link = elem.get_attribute("href")
                if link:
                    results_links.append(link)
        except Exception as e:
            Communicator.show_message(f"Error occurred while getting result links. Error: {str(e)}")
            logging.error(f"Error occurred while getting result links: {e}")
        return results_links

    def cleanup(self):
        try:
            Communicator.show_message("Closing the driver")
            self.driver.close()
            self.driver.quit()
        except Exception as e:
            Communicator.show_message(f"Error occurred while closing the driver. Error: {str(e)}")
            logging.error(f"Error occurred while closing the driver: {e}")
