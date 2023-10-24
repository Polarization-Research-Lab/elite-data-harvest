import json
import urllib
import pandas as pd
import numpy as np
import dataset

# Load database configuration from a JSON file
with open('../../../../../.secrets/db.json') as file:
    config = json.load(file)

# Database configuration
db_url = f"{config['dialect']}://{config['username']}:{urllib.parse.quote(config['password'])}@localhost:{config['port']}/elite"

# Connect to the database using dataset
db = dataset.connect(db_url)

# Access the legislators table
legislators_table = db['legislators']

# Load your DataFrame from 'legislators.csv'
legislators_df = pd.read_csv('legislators - 2023-9-12.csv')  # Replace 'legislators.csv' with your actual file path

# Convert NaN values to None
legislators_df = legislators_df.where(pd.notna(legislators_df), "")

legislators_table.upsert_many(
    legislators_df.to_dict(orient='records'), 
    keys=['bioguide_id'], 
)

exit()
# Use a context manager for the database transaction
for _, legislator_data in legislators_df.iterrows():
    print(_)    
    # Check if a row with the given bioguide_id exists
    existing_legislator = legislators_table.find_one(bioguide_id=legislator_data['bioguide_id'])

    if existing_legislator:
        # Update the existing row
        legislators_table.update(legislator_data, ['bioguide_id'])

    else:
        # Insert a new row
        legislators_table.insert(legislator_data)

