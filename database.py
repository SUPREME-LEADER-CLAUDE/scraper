# database.py

import os
import sys
import pandas as pd
from datetime import datetime
from .communicator import Communicator
from .settings import OUTPUT_PATH
from .error_codes import ERROR_CODES
import json

# Add the root directory to the system path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(root_dir)

def save_and_upload_results(results, query):
    filename = f"{query}.json"
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
                dataFrame = pd.DataFrame(datalist)
                totalRecords = dataFrame.shape[0]
                filename = f"{query}.json"
                joinedPath = os.path.join(OUTPUT_PATH, filename)
                Communicator.show_message(f"Saving data to path: {joinedPath}")

                if os.path.exists(joinedPath):
                    with open(joinedPath, 'r') as file:
                        existing_data = json.load(file)
                else:
                    existing_data = []

                existing_data.extend(datalist)

                with open(joinedPath, 'w') as file:
                    json.dump(existing_data, file, indent=4)
                
                Communicator.show_message(f"Successfully saved, total records saved: {totalRecords}.")
                return joinedPath
            else:
                Communicator.show_error_message("Could not scrape the data because you did not scrape any record.", {ERROR_CODES['NO_RECORD_TO_SAVE']})
                return None
        except Exception as e:
            Communicator.show_error_message(f"Error while saving data: {e}")
            return None
