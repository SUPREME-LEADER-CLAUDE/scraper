from bs4 import BeautifulSoup
from error_codes import ERROR_CODES
from communicator import Communicator
from database import DataSaver
from base import Base
from common import Common

class Parser(Base):
    def __init__(self, driver, searchquery) -> None:
        self.driver = driver
        self.searchquery = searchquery  # Add searchquery to the constructor
        self.finalData = []
        self.comparing_tool_tips = {
            "location": "Copy address",
            "phone": "Copy phone number",
            "website": "Open website",
        }

    def init_data_saver(self):
        self.data_saver = DataSaver()

    def parse(self):
        """Our function to parse the html"""
        infoSheet = self.driver.execute_script(
            """return document.querySelector("[role='main']")"""
        )
        if infoSheet is None:
            Communicator.show_error_message("No information sheet found", ERROR_CODES['ERR_NO_INFO_SHEET'])
            return

        try:
            rating, totalReviews, address, websiteUrl, phone = (None, None, None, None, None)

            html = infoSheet.get_attribute("outerHTML")
            soup = BeautifulSoup(html, "html.parser")

            try:
                rating = soup.find("span", class_="ceNzKf").get("aria-label")
            except Exception as e:
                Communicator.show_message(f"Could not find rating: {e}")

            try:
                totalReviews = list(soup.find("div", class_="F7nice").children)
                totalReviews = totalReviews[1].get_text(strip=True)
            except Exception as e:
                Communicator.show_message(f"Could not find total reviews: {e}")

            try:
                name = soup.select_one(".tAiQdd h1.DUwDvf").text.strip()
            except Exception as e:
                Communicator.show_error_message(f"No name found: {e}", ERROR_CODES['ERR_NO_NAME'])
                return

            allInfoBars = soup.find_all("button", class_="CsEnBe")

            for infoBar in allInfoBars:
                data_tooltip = infoBar.get("data-tooltip")
                text = infoBar.find('div', class_='rogA2c').text.strip()

                if data_tooltip == self.comparing_tool_tips["location"]:
                    address = text
                elif data_tooltip == self.comparing_tool_tips["website"]:
                    try:
                        websiteUrl = infoBar.parent.get("href")
                    except Exception as e:
                        Communicator.show_message(f"Could not find website URL: {e}")
                        websiteUrl = None
                elif data_tooltip == self.comparing_tool_tips["phone"]:
                    phone = text

            data = {
                "Name": name,
                "Phone": phone,
                "Address": address,
                "Website": websiteUrl,
                "Total Reviews": totalReviews,
                "Rating": rating,
            }

            Communicator.show_message(f"Parsed data: {data}")
            self.finalData.append(data)

        except Exception as e:
            Communicator.show_error_message(f"Error occurred while parsing a location. Error is: {str(e)}.", ERROR_CODES['ERR_WHILE_PARSING_DETAILS'])

    def main(self, allResultsLinks):
        Communicator.show_message("Scrolling is done. Now going to scrape each location")
        try:
            for resultLink in allResultsLinks:
                if Common.close_thread_is_set():
                    self.driver.quit()
                    return

                self.openingurl(url=resultLink)
                self.parse()

        except Exception as e:
            Communicator.show_message(f"Error occurred while parsing the locations. Error: {str(e)}")
        finally:
            self.init_data_saver()
            Communicator.show_message(f"Final data collected: {self.finalData}")
            self.data_saver.save(datalist=self.finalData, query=self.searchquery)  # Pass searchquery to save

