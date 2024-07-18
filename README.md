## Notes

This is a Google Maps Scraper. This tool allows you to extract data from Google Maps, without missing any possible results from a query using a strategy to invoke more workers based on population size. 

## Features

- Scrapes data from Google Maps: business names, addresses, phone number, website, total reviews and overall rating.
- 1 worker if population = < 100,000
- 2 workers if population = > 100,000
- Each increase of 200,000 population = additional worker, this works by creating another division within a locations zone, this provides the ability to not miss results due to densely populated results 

## Starting

To get started with the scraper, follow these steps:

1. Clone the repo:

   ```shell
   git clone https://github.com/CSG1000/scraper.git
   ```

2. Install the required dependencies by running the following command:
   ```shell
   pip install -r requirements.txt
   ```

3. Run the command in root directory:
   ```shell
   python "scraper\starter.py" headless --search_query "Air Quality Testing" --locations_file "locations.txt" --headless_mode 1
   ```


