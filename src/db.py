import psycopg2
from psycopg2 import sql
from src.utils import getSubsAllData
import json
import time

def load_config():
    with open('config.json') as f:
        return json.load(f)

def connectPS(database, user, host, password, port):  # Matching the function name and arguments
    config = load_config()
    conn = psycopg2.connect(
        database=database,
        user=user,
        host=host,
        password=password,
        port=port
    )
    return conn

def create_database():
    print('[+] Creating database..')
    # load config with user data
    config = load_config()  
    db_config = config.get('database', {})

    # connect with postgres user to create database as defined in the config file and grant privileges
    conn = psycopg2.connect(dbname="postgres", user="postgres")
    conn.autocommit = True 
    cur = conn.cursor()
    try:    
        cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(db_config.get('name'))))
        cur.execute(sql.SQL('GRANT ALL PRIVILEGES ON DATABASE {} TO {}').format(sql.Identifier(db_config.get('name')),sql.Identifier((db_config.get('user')))))
    except psycopg2.Error as e:
        if e.pgcode == '42P04':  # Database already exists error code
            print(f"[-] Database {db_config.get('name')} already exists.")  
        else:
            print(f"Error creating database: {e}")

    # connect as postgres to new database to give schema privileges to user
    try:
        conn = psycopg2.connect(dbname=db_config.get('name'), user="postgres")
        cur = conn.cursor()
        cur.execute(sql.SQL('GRANT ALL ON SCHEMA public TO {}').format(sql.Identifier(db_config.get('user'))))
        conn.commit()
        print("[+] Privileges granted successfully!")
        conn.close()
    except Exception as e:
        print(f"Error granting privileges on schema public: {e}")   

    # create table
    try:
        conn = connectPS(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port'))
        cur = conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS phone_num (number text NOT NULL, data jsonb)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_phone_num_number ON phone_num (number)')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_phone_num_name ON phone_num ((data->\'name\'->>\'str_name\'))')
        cur.execute('CREATE INDEX IF NOT EXISTS idx_phone_num_address ON phone_num ((data->\'address\'->>\'str_address\'))')
        print(f"[*] Database {db_config.get('name')} ready!")
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f'Error {e}')



def insert_data_to_db(conn, json_files: list):
	cur = conn.cursor()
	for r in range(len(json_files)):
		try:
			print(f'[*] Inserting file {r+1}/{len(json_files)}..name: {json_files[r]}')
			subscriber = getSubsAllData(json_files[r])
			subs_data = json.dumps(subscriber, ensure_ascii = False)
			for phone in subscriber['phones']:
            	# Inserting each phone number along with the rest of the subscriber data
				cur.execute("INSERT INTO phone_num (number, data) VALUES (%s, %s::jsonb)", (phone['number'], subs_data))
		except Exception as e:
			print(f'Error {e} in file {json_files[r]}')
	conn.commit()
	cur.close()


def getFromDb(queryItem):
    config = load_config()
    db_config = config.get('database', {})
    conn = connectPS(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port'))

    if not queryItem.phone and not queryItem.name and not queryItem.address:
        return ()

    query = "SELECT NUMBER, DATA FROM phone_num WHERE "
    conditions = []
    params = []

    if queryItem.phone:
        conditions.append("NUMBER LIKE %s")
        params.append(f"%{queryItem.phone}%")
    if queryItem.name:
        # Split the name into individual words
        name_components = queryItem.name.split()
        for component in name_components:
            conditions.append("data->'name'->>'str_name' iLIKE %s")
            params.append(f"%{component}%")
    if queryItem.address:
        # Split the address into individual words
        address_components = queryItem.address.split()
        for component in address_components:
            conditions.append("data->'address'->>'str_add' iLIKE %s")
            params.append(f"%{component}%")

    query += " AND ".join(conditions)
    cur = conn.cursor()
    cur.execute(query, params)
    values = cur.fetchall()
    cur.close()
    conn.close()

    return values



def database_exists(database, user, host, password, port):
    try:
        conn = psycopg2.connect(
            database="postgres",
            user=user,
            host=host,
            password=password,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [database])
        exists = cur.fetchone()
        cur.close()
        conn.close()
        return exists is not None
    except Exception as e:
        print(f'Error checking database existence: {e}')
        return False

def truncate_table(database, user, host, password, port):
    try:
        conn = psycopg2.connect(
            database=database,
            user=user,
            host=host,
            password=password,
            port=port
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE phone_num RESTART IDENTITY")
        cur.close()
        conn.close()
    except Exception as e:
        print(f'Error truncating table: {e}')        

def drop_database():
    # load config with user data
    config = load_config()  
    db_config = config.get('database', {})
    # connect with postgres and drop
    conn = psycopg2.connect(dbname="postgres", user="postgres")
    conn.autocommit = True 
    cur = conn.cursor()    
    try:    
        cur.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(db_config.get('name'))))
    except psycopg2.Error as e:
        print(f'Error dropping db: {e}')

        
