import sqlite3 as sql
import undetected_chromedriver as uc
import time
import json
import random
from tqdm import tqdm

from classes.book import Book
from classes.author import Author
from classes.entry_data import EntryData
from classes.user import User

from functions import convert_url, valid_mm_url, create_db_connection


def insert_author(conn: sql.Connection, author: Author) -> int:
    sql = 'INSERT OR IGNORE INTO author(name, last_name) VALUES(?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (author.name, author.last_name))

    sql = 'SELECT author_id FROM author WHERE name=?'
    author_id = cursor.execute(sql, (author.name,)).fetchone()[0]

    return author_id


def insert_book(conn: sql.Connection, author_id: int, book: Book) -> None:
    sql = 'INSERT OR IGNORE INTO book(title, pages, medium, author_id, medimops_url, api_url) VALUES(?,?,?,?,?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (book.title, book.pages, book.medium, author_id,
                   book.medimops_url, book.api_url))


def book_exists(conn: sql.Connection, url: str) -> bool:
    sql = 'SELECT EXISTS(SELECT 1 FROM book WHERE medimops_url=?)'

    cursor = conn.cursor()
    exists = cursor.execute(sql, (url,)).fetchone()[0]

    return exists == 1


def monitoring_book_exists(conn: sql.Connection, url: str) -> bool:
    sql = '''
        SELECT EXISTS (SELECT 1 FROM book, monitoring_books 
        WHERE book.medimops_url=?
        AND book.book_id = monitoring_books.book_id) 
    '''

    cursor = conn.cursor()
    if (cursor.execute(sql, (url,)).fetchone()[0]):
        return True

    else:
        return False


def get_missing_urls(conn: sql.Connection, urls: list) -> list:
    missing_urls = list()
    for url in urls:
        if (not book_exists(conn, url)):
            missing_urls.append(url)

    return missing_urls


def get_monitoring_urls(conn: sql.Connection) -> list:
    monitoring_urls = list()

    sql = '''
        SELECT medimops_url
        FROM book, monitoring_books as mb
        WHERE book.book_id = mb.book_id
    '''

    cursor = conn.cursor()
    temp_data = cursor.execute(sql).fetchall()

    for temp in temp_data:
        monitoring_urls.append(temp[0])

    return monitoring_urls


def get_unwanted_urls(conn: sql.Connection) -> list:
    unwanted_urls = list()
    monitoring_urls = get_monitoring_urls(conn)
    csv_urls = get_csv_urls(URL_FILES)

    for url in monitoring_urls:
        if (not url in csv_urls):
            unwanted_urls.append(url)

    return unwanted_urls


def insert_entry(conn: sql.Connection, entry_data: EntryData) -> None:
    author_id = insert_author(conn, entry_data.author)
    insert_book(conn, author_id, entry_data.book)


def handle_pre(pre: tuple, url: str) -> EntryData:
    data = json.loads(pre)

    product = data["content"]["product"]
    productAttributes = data["content"]["productAttributes"]

    title = product["title"]
    author = product["manufacturer"]
    pages = productAttributes["numberOfPages"]["value"]
    medium = productAttributes["medium"]["value"]

    book = Book(title, pages, medium, url)
    author = Author(author, None)

    return EntryData(book, author)


def get_api_data(urls: list) -> list:
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options)
    data = list()
    i = 0

    for url in tqdm(urls):
        driver.get(convert_url(url))
        if (i == 0):
            time.sleep(5)
        else:
            time.sleep(random.uniform(1.0, 3.0))

        data.append(handle_pre(driver.find_element(
            "tag name", 'pre').text, url))
        i += 1
    driver.quit()
    return data


def user_exists(conn: sql.Connection, mail: str) -> bool:
    sql = '''
        SELECT EXISTS (SELECT 1 FROM user
        WHERE user.email=?) 
    '''

    cursor = conn.cursor()
    if (cursor.execute(sql, (mail,)).fetchone()[0]):
        return True

    else:
        return False


def insert_user(conn: sql.Connection, name: str, last_name: str, email: str):
    sql = 'INSERT OR IGNORE INTO user(name, last_name, email) VALUES(?,?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (name, last_name, email))


def fetch_insert_missing(conn: sql.Connection, missing_urls: list[str]):
    data = get_api_data(missing_urls)

    for data_row in data:
        insert_entry(conn, data_row)


def get_users_url_dir() -> list:
    import glob
    
    users = list()

    for filepath in glob.iglob('db/urls/*.txt'):
        with open(filepath, 'r') as file:
            lines = [line.rstrip() for line in file]
            
            user = User(lines[0], lines[1], lines[2])
            user.urls = [lines[i] for i in range(len(lines)) if i > 2 and valid_mm_url(lines[i])]
            users.append(user)
            
    return users


def check_users(conn: sql.Connection, users: list[User]) -> list:
    all_urls = list()
    
    for user in users:
        if(not user_exists(conn, user.email)):
            print(f'User: "{user.email}" does not exist yet.')
            insert_user(conn, user.name, user.last_name, user.email)
           
        user_id = get_user_id(conn, user.email)
        if(not monitoring_order_exists(conn, user_id)):
            insert_monitoring_order(conn, user_id)
            
        for url in user.urls:
            all_urls.append(url)
            
    return all_urls


def monitoring_order_exists(conn: sql.Connection, user_id: int) -> bool:
    return conn.cursor().execute('SELECT EXISTS (SELECT 1 FROM monitoring_order WHERE user_id=?)', (user_id,)).fetchone()[0] == 1


def insert_monitoring_order(conn: sql.Connection, user_id: int) -> None:
    print(user_id)
    sql = 'INSERT OR IGNORE INTO monitoring_order(user_id) VALUES(?)'

    cursor = conn.cursor()
    cursor.execute(sql, (user_id, ))
    

def insert_monitoring_book(conn: sql.Connection, monitoring_id: int, book_id: int) -> None:
    sql = 'INSERT OR IGNORE INTO monitoring_books(monitoring_id, book_id) VALUES(?,?)'
    cursor = conn.cursor()
    cursor.execute(sql, (monitoring_id, book_id))


def get_user_id(conn: sql.Connection, email: str) -> int:
    return conn.cursor().execute('SELECT user_id FROM user WHERE email=?', (email,)).fetchone()[0]


def get_monitoring_id(conn: sql.Connection, email: str) -> int:
    sql = '''
        SELECT monitoring_id
        FROM monitoring_order, user
        WHERE user.user_id = monitoring_order.user_id
        AND user.email = ?    
    '''
    return conn.cursor().execute(sql, (email,)).fetchone()[0]



def get_book_id(conn: sql.Connection, url: str) -> int:
    return conn.cursor().execute('SELECT book_id FROM book WHERE medimops_url=?', (url,)).fetchone()[0]
    

def check_books(conn: sql.Connection, urls: list[str], users: list[User]) -> None:
    missing = get_missing_urls(conn, urls)
    monitoring_books = get_monitoring_urls(conn)
    
    if(missing): fetch_insert_missing(conn, missing)
    
    for user in users:
        monitoring_id = get_monitoring_id(conn, user.email)
        
        for url in user.urls:
            if(not monitoring_book_exists(conn, url)):
                book_id = get_book_id(conn, url) 
                
                insert_monitoring_book(conn, monitoring_id, book_id)         
        
        
                 

# Iterates through csv file and checks if there is a book entry for each url
# If not, stores missing urls and gets data from the website afterwards
def update_books() -> None:
    conn = create_db_connection('db/mmps_db.sqlite')
    
    users = get_users_url_dir()
    user_urls = check_users(conn, users)
    check_books(conn, user_urls, users)
    
    conn.commit()


if __name__ == "__main__":
    update_books()
    