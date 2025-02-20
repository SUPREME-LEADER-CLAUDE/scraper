import os
import sys
import pandas as pd
from datetime import datetime
from communicator import Communicator
from error_codes import ERROR_CODES
import json

# Set the output path to the current directory
OUTPUT_PATH = os.path.dirname(os.path.abspath(__file__))

def save_and_upload_results(results, query):
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{query}-{current_time}.json"
    file_path = os.path.join(OUTPUT_PATH, filename)
    
    try:
        if not os.path.exists(OUTPUT_PATH):
            os.makedirs(OUTPUT_PATH)
        
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                existing_data = json.load(file)
        else:
            existing_data = []
        
        existing_data.extend(results)
        
        with open(file_path, 'w') as file:
            json.dump(existing_data, file, indent=4)
        
        print(f"Saved local JSON file: {file_path}")
    except Exception as e:
        print(f"Error in save_and_upload_results: {e}")

class DataSaver:
    def __init__(self) -> None:
        self.outputFormat = Communicator.get_output_format()

    def save(self, datalist, query):
        Communicator.show_message(f"Starting save function with datalist: {datalist} and query: {query}")
        try:
            if len(datalist) > 0:
                Communicator.show_message("Saving the scraped data")
                totalRecords = len(datalist)
                current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{query}-{current_time}.json"
                file_path = os.path.join(OUTPUT_PATH, filename)
                Communicator.show_message(f"Saving data to path: {file_path}")

                if os.path.exists(file_path):
                    with open(file_path, 'r') as file:
                        existing_data = json.load(file)
                else:
                    existing_data = []

                existing_data.extend(datalist)

                with open(file_path, 'w') as file:
                    json.dump(existing_data, file, indent=4)
                
                Communicator.show_message(f"Successfully saved, total records saved: {totalRecords}.")
                return file_path
            else:
                Communicator.show_error_message("Could not scrape the data because you did not scrape any record.", {ERROR_CODES['NO_RECORD_TO_SAVE']})
                return None
        except Exception as e:
            Communicator.show_error_message(f"Error while saving data: {e}")
            return None
