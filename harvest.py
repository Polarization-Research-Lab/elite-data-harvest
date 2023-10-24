# Script Args
import os, argparse
parser = argparse.ArgumentParser(description = 'Elite Data Harvest')
parser.add_argument('source', type = str, help = f'Which source to you want to pull from? Options: {[folder for folder in os.listdir("sources") if (~folder.startswith(".")) & (os.path.isdir(os.path.join("sources", folder)))]}')
parser.add_argument('-d', '--debug', action = 'store_true', help = 'Whether you want to run in debug mode')
args = parser.parse_args()

# Python Standard Library
import json, urllib, datetime, argparse

# External Resources
import dataset
import sqlalchemy as sql

# Internal Resources
import sources.floor.harvester
import sources.newsletters.harvester
import sources.statements.harvester
import sources.tv.harvester

sources = {
    'floor': sources.floor.harvester,
    'newsletters': sources.newsletters.harvester,
    'statements': sources.statements.harvester,
    'tv': sources.tv.harvester,
}

# Setup
with open('../../../.secrets/elite-ingest.json') as file: secrets = json.load(file)
with open('config.json') as file: config = json.load(file)

config['congress.gov api key'] = secrets['congress.gov api key']
config['propublica api key'] = secrets['propublica api key']

## Connect to DB
db = dataset.connect(
    f"{secrets['db']['dialect']}://{secrets['db']['username']}:{urllib.parse.quote(secrets['db']['password'])}@localhost:{secrets['db']['port']}/elite"
    # f"sqlite:///elite.db" # <-- sql version
)

### Make table if it doesnt exist
sources[args.source].init(db)

## Get Date Ranges
start_date = datetime.datetime.strptime(config['start-date'], '%Y-%m-%d').date()

max_date = sql.select(sql.func.max(db[args.source].table.c.date)).execute().first()[0]
if max_date: start_date = max_date + datetime.timedelta(days=1)

end_date = datetime.datetime.now().date()

# Execute Harvester
for d, day in enumerate(range((end_date - start_date).days + 1)):
    date = start_date + datetime.timedelta(days = day)
    print('collecting for:', date)
    if db[args.source].find_one(date = date):
        print(f'Skipping {date} since there are already existing entries for that date')
    else:
        if not args.debug:
            sources[args.source].ingest(date, date, db, config)

