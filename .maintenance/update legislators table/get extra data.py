import json
import urllib
import pandas as pd
import numpy as np
import dataset
import os
import urllib.request

# Load database configuration from a JSON file
with open('../../../../../.secrets/db.json') as file:
    config = json.load(file)

# Database configuration
db_url = f"{config['dialect']}://{config['username']}:{urllib.parse.quote(config['password'])}@localhost:{config['port']}/elite"

# Connect to the database using dataset
db = dataset.connect(db_url)

# Access the legislators table
legislators = db['legislators']
legislators.create_column('serving_current_chamber_since', db.types.datetime, nullable = True)
legislators.create_column('serving_congress_since', db.types.datetime, nullable = True)

for legislator in legislators.all():
    bioguide_id = legislator['bioguide_id']
    json_file_path = f'.tmp/{bioguide_id}.json'

    # Download Data for Politician
    if not os.path.exists(json_file_path): # <-- Check if the file exists
        try:
            with urllib.request.urlopen(f'https://bioguide.congress.gov/search/bio/{bioguide_id}.json') as response:
                if response.status == 200:
                    # Save the downloaded JSON to the .tmp directory
                    with open(json_file_path, 'wb') as file:
                        file.write(response.read())
                    print(f'Downloaded and saved {json_file_path}')
                else:
                    print(f'Failed to download data for bioguide_id {bioguide_id}')
        except urllib.error.URLError as e:
            print(f'Error downloading data for bioguide_id {bioguide_id}: {e.reason}')

    with open(f'.tmp/{bioguide_id}.json', 'r') as file: 
        extended_data = json.load(file)
        
        job_positions = extended_data['data']['jobPositions']
        # Filter out items without a startDate
        job_positions_filtered = [item for item in job_positions if 'startDate' in item['congressAffiliation']['congress']]

        # Order the filtered jobPositions list by start date in ascending order
        job_positions_sorted = sorted(job_positions_filtered, key=lambda x: x['congressAffiliation']['congress']['startDate'])

        # job_positions_sorted = sorted(job_positions, key=lambda x: x['congressAffiliation']['congress']['startDate'])

        # Get the last job name and initial serving_since value
        last_item = job_positions_sorted[-1]
        last_job = last_item['job']['name']
        serving_since = last_item['congressAffiliation']['congress']['startDate']

        # Iterate backward through the jobPositions list
        for item in reversed(job_positions_sorted[:-1]):  # Exclude the last item since we already have its data
            current_job = item['job']['name']

            if current_job == last_job:
                # Update serving_since if the current job matches the last job
                serving_since = item['congressAffiliation']['congress']['startDate']
            else:
                # If the current job is different, break out of the loop
                break

        legislator['serving_congress_since'] = job_positions_sorted[0]['congressAffiliation']['congress']['startDate']
        legislator['serving_current_chamber_since'] = serving_since

        legislators.update(legislator, ['id'])
