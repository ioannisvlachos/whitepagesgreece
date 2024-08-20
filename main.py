import os
import json
import argparse
import uvicorn
import warnings
import time
import threading
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.db import connectPS, insert_data_to_db, getFromDb, database_exists, load_config, create_database, truncate_table, drop_database
from src.utils import prepareMapItem, exportMap, getDb, download_data, prepareQueryItem, get_sitemap, load_sitemap, to_be_downloaded

# Ignore DeprecationWarning
warnings.filterwarnings("ignore", category=DeprecationWarning)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def init_db():
    config = load_config()
    db_config = config.get('database', {})
    files = getDb(os.getcwd() + '/wp_db')
    conn = connectPS(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port'))
    insert_data_to_db(conn, files)
    conn.close()

def init_update(update_list):
    config = load_config()
    db_config = config.get('database', {})
    conn = connectPS(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port'))
    insert_data_to_db(conn, update_list)
    conn.close()

@app.on_event("startup")
async def startup_event():
    config = load_config()
    db_config = config.get('database', {})
    if not database_exists(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port')):
        download_data()
        init_db()

@app.get("/", response_class=HTMLResponse)
async def get_search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

@app.post("/search", response_class=HTMLResponse)
async def handle_search(
    request: Request,
    phone: str = Form(None),
    name: str = Form(None),
    address: str = Form(None)
):
    query = prepareQueryItem({'phone': phone, 'name': name, 'address': address})
    values = sorted(getFromDb(query), key=lambda x: x[0])
    map_item = prepareMapItem(values)
    exportMap(map_item)
    data_to_send = json.dumps(values, ensure_ascii=False)
    print(data_to_send)
    return templates.TemplateResponse("map.html", {"request": request, "data": data_to_send})

def auto_update():
    print('[*] Auto updating..')
    while True:
        ttime = time.time()
        try:
            old_sitemap = load_sitemap()
        except Exception:
            old_sitemap = []
        
        new_sitemap = get_sitemap()
        sitemap = to_be_downloaded(old_sitemap, new_sitemap)
        print(f'[*] New contacts found: {len(sitemap)}')
        download_data(sitemap, sample=False)
        updated_list = [os.getcwd() + '/wp_db/' + str(x['id']) + '.json' for x in sitemap]
        init_update(updated_list)
        
        # Sleep until the next minute
        time.sleep(3600 - (time.time() - ttime))

def main(args):
    config = load_config()
    db_config = config.get('database', {})

    if args.sample:
        drop_database()
        create_database()
        print("[*] Downloading sample data..")
        sitemap = get_sitemap()
        download_data(sitemap, sample=True)
        init_db()
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.force_download:
        drop_database()
        create_database()
        print("[*] Downloading all data..")
        sitemap = get_sitemap()
        download_data(sitemap, sample=True)
        init_db()
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.truncate_table:
        print("[*] Truncating all data in database...")
        truncate_table(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port'))
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.drop_database:
        print("[*] Dropping database..")
        drop_database()
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.create_database:
        print("[*] Creating database..")
        create_database()
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.insert_only:
        create_database()
        print("[*] Inserting downloaded data from folder..")
        files = getDb(os.getcwd() + '/wp_db')
        conn = connectPS(db_config.get('name'), db_config.get('user'), db_config.get('host'), db_config.get('password'), db_config.get('port'))
        insert_data_to_db(conn, files)
        conn.close()
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.update_db:
        print("[*] Updating db..")
        try:
            old_sitemap = load_sitemap()
        except Exception:
            old_sitemap = []
        new_sitemap = get_sitemap()
        sitemap = to_be_downloaded(old_sitemap, new_sitemap)
        print(f'New contacts found: {len(sitemap)}')
        download_data(sitemap, sample=False)
        updated_list = [os.getcwd() + '/wp_db/' + str(x['id']) + '.json' for x in sitemap]
        init_update(updated_list)
        uvicorn.run(app, host="0.0.0.0", port=6563)

    elif args.auto_update:
        # Start the auto-update thread
        thread = threading.Thread(target=auto_update)
        thread.daemon = True
        thread.start()

        # Run the FastAPI application
        uvicorn.run(app, host="0.0.0.0", port=6563)

    else:
        uvicorn.run(app, host="0.0.0.0", port=6563)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run the FastAPI application.')
    parser.add_argument('-s', '--sample', action='store_true', help='Download sample data and run the FastAPI endpoint.')
    parser.add_argument('-f', '--force-download', action='store_true', help='Download all data, truncate existing data, and run the FastAPI endpoint.')
    parser.add_argument('-c', '--create-database', action='store_true', help='Create database with config file data.')
    parser.add_argument('-t', '--truncate-table', action='store_true', help='Delete all data in database.')
    parser.add_argument('-d', '--drop-database', action='store_true', help='Drop database.')
    parser.add_argument('-i', '--insert-only', action='store_true', help='Insert downloaded data from folder wp_db/ to database.')
    parser.add_argument('-u', '--update-db', action='store_true', help='Updates db.')
    parser.add_argument('-a', '--auto-update', action='store_true', help='Auto-update the database every minute.')

    args = parser.parse_args()
    main(args)
