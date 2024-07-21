from selenium import webdriver
import undetected_chromedriver as uc
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_driver():
    options = uc.ChromeOptions()
    options.add_argument('--headless')  # Use add_argument for headless mode
    options.add_argument('--disable-gpu')  # Disable GPU acceleration for headless mode

    try:
        driver = uc.Chrome(options=options)
        logging.info("ChromeDriver initialized successfully.")
        driver.get("http://www.google.com")
        logging.info(f"Page title: {driver.title}")
        driver.quit()
    except Exception as e:
        logging.error(f"Error initializing or running ChromeDriver: {e}")

if __name__ == "__main__":
    test_driver()
