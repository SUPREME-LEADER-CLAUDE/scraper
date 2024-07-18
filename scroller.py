import time
from communicator import Communicator
from common import Common
from bs4 import BeautifulSoup
from selenium.common.exceptions import JavascriptException
from parser import Parser

class Scroller:

    def __init__(self, driver, searchquery) -> None:
        self.driver = driver
        self.searchquery = searchquery
        self.__allResultsLinks = []

    def __init_parser(self):
        self.parser = Parser(self.driver, self.searchquery)

    def start_parsing(self):
        self.__init_parser()  # Init parser object on the fly

        if not self.__allResultsLinks:
            Communicator.show_error_message("No results to parse. Links list is empty.", "ERR_NO_RESULTS")
            return

        self.parser.main(self.__allResultsLinks)

    def scroll(self):
        """In case search results are not available"""
        scrollable_element = self.get_scrollable_element()

        if scrollable_element is None:
            Communicator.show_message(message="We are sorry but, No results found for your search query on google maps....")
            return

        Communicator.show_message(message="Starting scrolling")
        self.perform_scrolling(scrollable_element)
        Communicator.show_message(f"Total locations scrolled: {len(self.__allResultsLinks)}")
        self.start_parsing()

    def get_scrollable_element(self):
        try:
            return self.driver.execute_script("return document.querySelector('[role=\"feed\"]')")
        except JavascriptException as e:
            Communicator.show_error_message(f"Error finding scrollable element: {e}", 'ERR_SCROLLABLE_ELEMENT_NOT_FOUND')
            return None

    def perform_scrolling(self, scrollable_element):
        last_height = 0
        dynamic_sleep_time = 1

        while True:
            if Common.close_thread_is_set():
                self.driver.quit()
                return

            scrollable_element = self.get_scrollable_element()
            if scrollable_element is None:
                break

            self.driver.execute_script("arguments[0].scrollTo(0, arguments[0].scrollHeight);", scrollable_element)
            time.sleep(dynamic_sleep_time)

            new_height = self.driver.execute_script("return arguments[0].scrollHeight", scrollable_element)

            if new_height == last_height:
                if self.is_end_of_list():
                    break
                else:
                    self.try_click_last_element()
            else:
                last_height = new_height
                self.collect_results_links(scrollable_element)
                Communicator.show_message(f"Total locations scrolled: {len(self.__allResultsLinks)}")
                dynamic_sleep_time = max(1, dynamic_sleep_time - 0.1)  # Decrease sleep time for faster scrolling

    def is_end_of_list(self):
        try:
            end_alert_element = self.driver.execute_script("return document.querySelector('.PbZDve')")
            return end_alert_element is not None
        except JavascriptException as e:
            Communicator.show_error_message(f"Error checking end of list: {e}", 'ERR_END_OF_LIST_CHECK')
            return False

    def try_click_last_element(self):
        try:
            self.driver.execute_script("array=document.getElementsByClassName('hfpxzc');array[array.length-1].click();")
        except JavascriptException:
            pass

    def collect_results_links(self, scrollable_element):
        try:
            all_results_list_soup = BeautifulSoup(scrollable_element.get_attribute('outerHTML'), 'html.parser')
            all_results_anchor_tags = all_results_list_soup.find_all('a', class_='hfpxzc')
            self.__allResultsLinks = [anchor_tag.get('href') for anchor_tag in all_results_anchor_tags if anchor_tag.get('href')]
            if not self.__allResultsLinks:
                Communicator.show_message("No links found during scrolling.")
        except Exception as e:
            Communicator.show_error_message(f"Error collecting result links: {e}", 'ERR_COLLECTING_RESULTS_LINKS')
