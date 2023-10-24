'''
---
title: House and Senate Floor Speech Ingester
---
'''
# Python Standard Library
import os, json, datetime, tempfile, time, requests, zipfile, io

# External Resources
import dataset

# Internal Resources
from . import congressionalrecordparser

tablename = 'floor'

def init(db):
    table = db.create_table(tablename, primary_id = 'id', primary_type = db.types.integer, primary_increment = True)
    table.create_column('date', db.types.date)
    table.create_column('bioguide_id', db.types.string(50))
    table.create_column('text', db.types.text)
    table.create_column('chamber', db.types.string(50))
    table.create_column('source_id', db.types.string(100))
    table.create_column('file_id', db.types.string(100))
    table.create_column('item_id', db.types.string(100))
    table.create_column('cr_vol', db.types.integer)
    table.create_column('cr_num', db.types.integer)


def ingest(start_date, end_date, db, config):
    '''
    Ingest the Data
    '''
    # for i in range(start_date, end_date, datetime.timedelta(days = 1)):
    for i in range((end_date - start_date).days + 1):
        entries = []
        date = start_date + datetime.timedelta(days = i)

        # # use Congress.gov API to get all congressional records for that date
        response = requests.get(
            "https://api.congress.gov/v3/congressional-record",
            params = {'format': 'json',  'y': date.year, 'm': date.month, 'd': date.day, 'offset': 0, 'limit': 100,},
            headers = {'x-api-key': config['congress.gov api key']}
        )

        response.raise_for_status()
        issues = response.json().get('Results', {}).get('Issues', None)
        if issues:
            for issue in issues:
                with tempfile.TemporaryDirectory() as temp_dir:
                    # temp_dir = '.tmp/'

                    # Find out the record that we're downloading
                    full_record = issue.get("Links", {}).get("FullRecord", {}).get("PDF", [])[0]
                    record_name = full_record.get("Url", "").split('/')[-1].split('.')[0]
                    download_url = f"https://www.govinfo.gov/content/pkg/{record_name}.zip"

                    # Download and process record zip file
                    with requests.get(download_url, stream=True) as zip_response:
                        zip_response.raise_for_status()

                        zip_file_path = os.path.join(temp_dir, f"{date.year}-{date.month}-{date.day}.zip")
                        with open(zip_file_path, 'wb') as zip_file:
                            for chunk in zip_response.iter_content(chunk_size=8192):
                                zip_file.write(chunk)

                    # Extract zip file
                    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)

                    # Parse with congressionrecordparser and loop through all speeches
                    crfiles = congressionalrecordparser.parse(os.path.join(temp_dir, record_name))
                    for crfile in crfiles:
                        for i, speech in enumerate(crfile.crdoc['content']):
                            if speech.get('speaker_bioguide'):
                                entries.append({
                                    # id (auto increment)
                                    'date': datetime.datetime.strptime(
                                        crfile.crdoc['header']['year'] + '-' + str(datetime.datetime.strptime(crfile.crdoc['header']["month"],'%B').month) + '-' + crfile.crdoc['header']['day'],
                                        '%Y-%m-%d'
                                    ).date(),
                                    'bioguide_id': speech['speaker_bioguide'],
                                    'text': speech['text'],
                                    'chamber': crfile.chamber,
                                    'source_id': record_name,
                                    'file_id': crfile.access_path,
                                    'item_id': f'{i}',
                                    'cr_vol': crfile.cr_vol,
                                    'cr_num': crfile.cr_num,
                                })

        for entry in entries:
            db[tablename].insert(entry)
            db.commit()