import os
os.chdir('/app')
import time
import json
import sqlite3
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from module import download_data, generate_datalake



# ------------------------------------------------------------------------------------

load_dotenv()

WORK_DIR = 'app'
JSON_DIR = 'app/json'
DB_PATH = 'app/local.db'
DECODER_FILE = 'app/decoder.xlsx'
SERVER_NAME = os.getenv('SERVER_NAME')
DASHBOARD_HOST = os.getenv('DASHBOARD_HOST')
SCTO_USERNAME = os.getenv('SCTO_USERNAME')
SCTO_PASSWORD = os.getenv('SCTO_PASSWORD')

# ------------------------------------------------------------------------------------

def update():
    # load list_surveys table
    conn = sqlite3.connect(DB_PATH)
    list_surveys = pd.read_sql_query('SELECT * FROM list_surveys', conn)
    conn.close()

    # get parameters
    for i in range(len(list_surveys)):
        survey_name = list_surveys.loc[i,'Survey Name']
        form_id = list_surveys.loc[i,'Form ID']
        last_download = list_surveys.loc[i,'Last Download']
        wilayah = json.loads(list_surveys.loc[i,'Wilayah'])
        targets = json.loads(list_surveys.loc[i,'Target'])
        target_column = list_surveys.loc[i,'Target Column']
        try:
            decoder = json.loads(list_surveys.loc[i,'Decoder'])
        except:
            decoder = None
    
        # download data
        df = download_data(form_id, wilayah, decoder)
        
        # data preprocessing
        conn = sqlite3.connect(DB_PATH)
        metadata = pd.read_sql_query(f'SELECT * FROM {survey_name}_metadata', conn)
        conn.close()
        generate_datalake(survey_name, df, targets, target_column, metadata)
        
        # update last_download in list_surveys table
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        update_sql = '''
            UPDATE list_surveys 
            SET [Last Download] = ?
            WHERE [Survey Name] = ?
        '''
        last_download = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(update_sql, (last_download, survey_name))
        conn.commit()
        conn.close()


# ------------------------------------------------------------------------------------

# Run the scheduler continuously
while True:
    update()
    time.sleep(3600)
