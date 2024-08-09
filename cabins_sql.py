import os
from glob import glob
from dotenv import load_dotenv

import pandas as pd
from sqlalchemy import create_engine, text


# Load environment variables from the .env file (if present)
load_dotenv()

# Access environment variables 
POSTGRES_USER = os.getenv('PostgreSQL_USERNAME')
POSTGRES_PSW = os.getenv('PostgreSQL_PSW')

# Define the folder path
FOLDER_PATH = 'data\cabins'

# Get the list of CSV files sorted by the date in the filename
csv_files = sorted(glob(os.path.join(FOLDER_PATH, 'etuovi_data_*.csv')), key=lambda x: os.path.basename(x).split('_')[-1].split('.')[0], reverse=False)

def update_database(new_data):

    new_data['winterized'] = new_data['winterized'].apply(lambda x: True if x == 'YES' else False)

    # Convert date columns from text to datetime
    new_data['first_posting_date'] = pd.to_datetime(new_data['first_posting_date']).dt.date
    new_data['last_posting_date'] = pd.to_datetime(new_data['last_posting_date']).dt.date

    # Database connection
    engine = create_engine(f'postgresql://{POSTGRES_USER}:{POSTGRES_PSW}@localhost:5432/cabins_main')
    
    # Insert new data into temporary table
    new_data.to_sql('cabins_temp', engine, if_exists='replace', index=False)
    
    # Upsert data into main table
    with engine.connect() as conn:

        conn.execute(text("""
            INSERT INTO cabins_main (
            address, url, description, rooms, winterized, price, surface, year, original_price,
            latitude, longitude, distance, duration, first_posting_date, last_posting_date
            )
            SELECT 
                address, url, description, rooms, winterized, price, surface, year, original_price,
                latitude, longitude, distance, duration, first_posting_date, last_posting_date
            FROM cabins_temp
            ON CONFLICT (url) DO UPDATE SET
                address = EXCLUDED.address,
                description = EXCLUDED.description,
                rooms = EXCLUDED.rooms,
                winterized = EXCLUDED.winterized,
                price = EXCLUDED.price,
                surface = EXCLUDED.surface,
                year = EXCLUDED.year,
                original_price = EXCLUDED.original_price,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude,
                distance = EXCLUDED.distance,
                duration = EXCLUDED.duration,
                first_posting_date = EXCLUDED.first_posting_date,
                last_posting_date = EXCLUDED.last_posting_date;

        """))

# Process and update the database for each CSV file
for file in csv_files:
    # Read the CSV file into a DataFrame
    new_data = pd.read_csv(file)

    # Update the database with the new data
    update_database(new_data)
    