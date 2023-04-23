import sqlite3 as sql


def convert_url(url: str) -> str:
    return f'https://www.medimops.de/api/page?path=/{url[24:]}'


# Not reliable, but at least checks basics
def valid_mm_url(url: str) -> bool:
        return url.startswith('https://www.medimops.de/') and url.endswith('.html')


def create_db_connection(db_file) -> sql.Connection:
    conn = None
    try:
        conn = sql.connect(db_file)
    except sql.Error as err:
        print(err)

    return conn
