import sqlite3


def convert_url(url: str) -> str:
    return f'https://www.medimops.de/api/page?path=/{url[24:]}'


# Not reliable, but at least checks basics
def valid_mm_url(url: str) -> bool:
        return url.startswith('https://www.medimops.de/') and url.endswith('.html')


def create_db_connection(db_file) -> sqlite3.Connection:
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as err:
        print(err)

    return conn
