
# WhitePagesGreece Scrapper

This repository contains a comprehensive application that downloads white pages data (www.11888.gr), stores them in a PostgreSQL database, and provides an interface to search phone numbers, print the results and visualize them on a Keplergl map using a FastAPI endpoint. The application supports downloading all data, downloading sample data, managing psql database, and running the Fastapi endpoint.

## Features

- **Download Data**: Download all white pages data or a sample subset of it.
- **Database Management**: Automatically checks for the existence of the database, creates it if it does not exist, and manages table data.
- **FastAPI Integration**: Provides a web interface for searching phone numbers and displaying results on a map.
- **Multi-threaded Downloading**: Uses multi-threading to speed up the data download process.

## Requirements

- Python 3.x
- PostgreSQL
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/whitepages-fastapi.git
   cd whitepages-fastapi

2. Install the required Python packages:
    ```
    pip install -r requirements.txt
    
    ```
    
3. Configure the database and other settings in config.json:
    
    ```

    {
      "database": {
        "name": "your_db_name",
        "user": "your_db_user",
        "host": "localhost",
        "password": "your_db_password",
        "port": "5432"
      }
    }

    ```
  

## Usage
The application can be run with different modes using command-line arguments.

Command-Line Arguments
  ```
    
    -s or --sample: Download a small sample of data for testing.
    -f or --force-download: Download all data.
    -c or --create-database: Create database with config file data.
    -t or --truncate-table: Delete/Truncate all data in database.
    -d or --drop-database: Drop database.
    -i or --insert-only: Insert downloaded data from local folder wp_db/ to database.
  ```


## Running the Application
   
To download a sample of data and start the FastAPI server:
    ```
    python3 main.py -s
    ```
    
To force download all data and start the FastAPI server:
    ```
    python3 main.py -f
    ```
    
To delete all data and drop the database:
    ```
    python3 main.py -d
    ```
    
To simply run the FastAPI server without downloading or modifying data (make sure there is data inserted in the db):
      ```
      python3 main.py
      ```

### FastAPI Endpoints
- GET /: Renders the search page.
- POST /search: Handles search requests, retrieves data from the database, and displays results on a map.

### Directory Structure
```
whitepages-fastapi/
├── src/
│   ├── data_models.py
│   ├── db.py
│   └── utils.py
├── templates/
│   ├── search.html
│   └── map.html
├── static/
│   └── index.html
├── wp_db/
├── config.json
├── main.py
├── requirements.txt
└── README.md
```

## Disclaimer
The phone data are public and are maintained by greek service providers in public phonebooks, after receiving approval of their subscribers, in accordance with article 6 of Law 3471/2006, article 3 of Law 3783/2009 and Law 4624/19.

## Contributing
Feel free to open issues or submit pull requests if you have any improvements or bug fixes.

## License
This project is licensed under the MIT License. See the **LICENSE** file for more details.

```
Feel free to modify this description as needed to better fit your project's details.
```# whitepagesgreece
