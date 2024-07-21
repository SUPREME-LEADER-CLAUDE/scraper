import logging
from time import sleep
import tempfile
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from base import Base
from scroller import Scroller
from settings import DRIVER_EXECUTABLE_PATH
from communicator import Communicator
from database import DataSaver, save_and_upload_results
from parser import Parser
import signal
import sys
import time

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
        for attempt in range(3):
            try:
                options = uc.ChromeOptions()
                if self.headlessMode == 1:
                    options.headless = True

                prefs = {"profile.managed_default_content_settings.images": 2}
                options.add_experimental_option("prefs", prefs)

                Communicator.show_message("Wait checking for driver...\nIf you don't have webdriver in your machine it will install it")

                with tempfile.TemporaryDirectory() as tmpdirname:
                    options.add_argument(f"--user-data-dir={tmpdirname}")
                    logging.info(f"Using temporary directory for Chrome: {tmpdirname}")
                    if DRIVER_EXECUTABLE_PATH:
                        self.driver = uc.Chrome(driver_executable_path=DRIVER_EXECUTABLE_PATH, options=options)
                    else:
                        self.driver = uc.Chrome(options=options)
                break  # Exit the loop if successful
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} of 3: Error during Chrome driver initialization: {e}")
                time.sleep(5)  # Wait before retrying
                if attempt == 2:
                    raise

        Communicator.show_message("Opening browser...")
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
            Communicator.show_message(f"Navigated to URL: {link_of_page}")
            sleep(1)  # Ensure the page loads completely

            # Additional logging to debug element finding
            Communicator.show_message("Looking for the [role='feed'] element")
            feed_element = self.driver.execute_script("return document.querySelector('[role=\"feed\"]')")
            if feed_element is None:
                Communicator.show_error_message("Error: Feed element not found", "ERR_NO_FEED_ELEMENT")
            else:
                Communicator.show_message("Feed element found")

            self.scroller.scroll()
            all_results_links = self.get_all_results_links()
            data = self.collect_data(all_results_links)
        except Exception as e:
            Communicator.show_message(f"Error occurred while scraping. Error: {str(e)}")
        finally:
            try:
                Communicator.show_message("Closing the driver")
                self.driver.close()
                self.driver.quit()
            except Exception as e:
                Communicator.show_message(f"Error occurred while closing the driver. Error: {str(e)}")
            Communicator.end_processing()

            # Save data using DataSaver
            Communicator.show_message(f"Saving data: {data}")
            if len(data) >= 5:  # Ensure data has at least 5 entries before saving and uploading
                self.data_saver.save(data, self.searchquery)  # Pass searchquery to DataSaver.save()
                save_and_upload_results(data, self.searchquery, "scrapedcompetitors")
            else:
                Communicator.show_message(f"Not enough data collected to save. Only {len(data)} entries found.")
        return data

    def collect_data(self, all_results_links):
        Communicator.show_message(f"Collecting data from links: {all_results_links}")
        self.parser.main(all_results_links)
        return self.parser.finalData

    def get_all_results_links(self):
        results_links = []
        try:
            Communicator.show_message("Finding result links with CSS selector 'a.result-title'")
            elements = self.driver.find_elements(By.CSS_SELECTOR, "a.result-title")
            for elem in elements:
                link = elem.get_attribute("href")
                if link:
                    results_links.append(link)
        except Exception as e:
            Communicator.show_message(f"Error occurred while getting result links. Error: {str(e)}")
        Communicator.show_message(f"Results links collected: {results_links}")
        return results_links
