import argparse
import os
import numpy as np
from multiprocessing import Pool, current_process
from scraper import Backend
from database import DataSaver
import signal
import sys
import json
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname=s - %(message)s')

# Global variable to keep track of processes and drivers
processes = []
all_results = []
search_query = ""
data_saver = DataSaver()
progress_file = "progress.json"

def get_city_data(city_name):
    locations_file_path = 'locations.txt'
    with open(locations_file_path, 'r') as file:
        for line in file:
            if line.startswith(city_name):
                name, population, lat, long = line.strip().split(',')
                return {'population': int(population), 'lat': float(lat), 'long': float(long)}
    return {'population': 0, 'lat': None, 'long': None}

def read_locations_from_file(filename):
    with open(filename, 'r') as file:
        locations = [line.strip().split(',') for line in file.readlines()]
    return [loc[0] for loc in locations]

def read_industries_from_file(filename):
    with open(filename, 'r') as file:
        industries = [line.strip() for line in file.readlines()]
    return industries

def read_progress():
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as file:
            return json.load(file)
    return {}

def write_progress(progress):
    with open(progress_file, 'w') as file:
        json.dump(progress, file, indent=4)

def determine_num_divisions(population):
    if population <= 100000:
        return 1
    else:
        return max(2, population // 200000)

def generate_pie_subregions(lat_center, long_center, num_divisions):
    angles = np.linspace(0, 2 * np.pi, num_divisions + 1)
    subregions = []
    
    for i in range(num_divisions):
        start_angle = angles[i]
        end_angle = angles[i + 1]
        subregions.append((lat_center, long_center, start_angle, end_angle))
    
    return subregions

def scrape_subregion(args):
    global all_results
    search_query, headless_mode, lat_center, long_center, start_angle, end_angle = args
    backend = Backend(
        searchquery=search_query,
        outputformat='json',
        headlessmode=headless_mode,
        lat_center=lat_center,
        long_center=long_center,
        start_angle=start_angle,
        end_angle=end_angle
    )
    processes.append(current_process())
    result = backend.mainscraping()
    all_results.extend(result)
    backend.cleanup()  # Ensure the driver is closed after scraping
    return result

def signal_handler(sig, frame):
    logging.info('CTRL+C detected. Saving results...')
    try:
        data_saver.save(all_results, search_query)
    except Exception as e:
        logging.error(f"Error during saving results: {e}")
    finally:
        logging.info('Shutting down processes...')
        for process in processes:
            process.terminate()
        sys.exit(0)

# Register the signal handler for CTRL+C
signal.signal(signal.SIGINT, signal_handler)

def main():
    global search_query
    parser = argparse.ArgumentParser()

    parser.add_argument("value", type=str, help="""Arguments being passed to script.
                        It can be: 
                        headless: To start the scraper in headless mode (CLI)""")
    parser.add_argument("--locations_file", type=str, help="File with list of locations", required=False)
    parser.add_argument("--industries_file", type=str, help="File with list of industries", required=False)
    parser.add_argument("--num_locations", type=int, default=1, help="Number of locations to select from the file", required=False)
    parser.add_argument("--headless_mode", type=int, choices=[0, 1], default=1, help="Headless mode (1 for true, 0 for false)")

    args = parser.parse_args()

    if args.value == "headless":
        if not args.locations_file or not args.industries_file:
            logging.error("Error: --locations_file and --industries_file are required for headless mode")
            return

        locations_file_path = args.locations_file
        industries_file_path = args.industries_file
        
        locations = read_locations_from_file(locations_file_path)
        industries = read_industries_from_file(industries_file_path)
        progress = read_progress()

        total_locations = len(locations)

        for industry in industries:
            logging.info(f"Processing industry: {industry}")
            search_query = industry

            if industry not in progress:
                progress[industry] = []

            # Check if the industry is completed
            if len(progress[industry]) >= total_locations:
                logging.info(f"Skipping completed industry: {industry}")
                continue

            for location in locations:
                if location in progress[industry]:
                    logging.info(f"Skipping already completed location: {location} for industry: {industry}")
                    continue

                logging.info(f"Processing location: {location} for industry: {industry}")
                city_data = get_city_data(location)
                population = city_data['population']
                lat_center = city_data['lat']
                long_center = city_data['long']
                logging.info(f"Population of {location}: {population}, lat: {lat_center}, long: {long_center}")
                
                if population == 0:
                    logging.warning(f"Warning: Population data for {location} not found.")
                    continue

                num_divisions = determine_num_divisions(population)
                logging.info(f"Number of divisions for {location}: {num_divisions}")

                if num_divisions > 1:
                    if not lat_center or not long_center:
                        logging.error(f"Error: Coordinates for {location} not found.")
                        return
                    
                    subregions = generate_pie_subregions(lat_center, long_center, num_divisions)
                    tasks = [(search_query, args.headless_mode, lat_center, long_center, start_angle, end_angle) for lat_center, long_center, start_angle, end_angle in subregions]
                    
                    try:
                        with Pool(processes=os.cpu_count()) as pool:
                            results = pool.map(scrape_subregion, tasks)
                            all_results.extend(results)
                    except Exception as e:
                        logging.error(f"Error during multiprocessing: {e}")
                        results = []
                        for task in tasks:
                            results.append(scrape_subregion(task))
                        all_results.extend(results)
                else:
                    backend = Backend(
                        searchquery=search_query,
                        outputformat='json',
                        headlessmode=args.headless_mode,
                        location=location
                    )
                    results = backend.mainscraping()
                    logging.info(f"Results for {location}: {results}")
                    all_results.extend(results)

                # Save results for the current location
                data_saver.save(results, industry)

                # Update progress
                progress[industry].append(location)
                write_progress(progress)

            logging.info(f"All results collected for industry '{industry}': {all_results}")
            all_results = []  # Reset for next industry

    else:
        logging.error("Invalid argument. Use 'headless' for headless execution.")

if __name__ == "__main__":
    main()
