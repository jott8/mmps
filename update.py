import sqlite3
import undetected_chromedriver as uc
import time
import json
import random
from tqdm import tqdm

from classes.book import Book
from classes.author import Author
from classes.entry_data import EntryData

from functions import convert_url, valid_mm_url, create_db_connection


# Iterates through csv file entries and checks if there is a book which is not on the monitoring list
def urls_to_monitoring_list(conn: sqlite3.Connection) -> None:
    monitoring_id = 1

    for _ in URL_FILES:
        urls = get_csv_urls_i(monitoring_id-1, URL_FILES)

        for url in urls:
            cursor = conn.cursor()

            sql = 'SELECT book_id FROM book WHERE medimops_url=?'
            book_id = cursor.execute(sql, (url,)).fetchone()[0]

            sql = 'INSERT OR IGNORE INTO monitoring_books(monitoring_id, book_id) VALUES(?,?)'
            cursor = conn.cursor()
            cursor.execute(sql, (monitoring_id, book_id))
        monitoring_id += 1

    conn.commit()
           
    return urls


def insert_author(conn: sqlite3.Connection, author: Author) -> int:
    sql = 'INSERT OR IGNORE INTO author(name, last_name) VALUES(?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (author.name, author.last_name))

    sql = 'SELECT author_id FROM author WHERE name=?'
    author_id = cursor.execute(sql, (author.name,)).fetchone()[0]

    return author_id


def insert_book(conn: sqlite3.Connection, author_id: int, book: Book) -> None:
    sql = 'INSERT OR IGNORE INTO book(title, pages, medium, author_id, medimops_url, api_url) VALUES(?,?,?,?,?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (book.title, book.pages, book.medium, author_id,
                   book.medimops_url, book.api_url))


def book_exists(conn: sqlite3.Connection, url: str) -> bool:
    sql = 'SELECT EXISTS(SELECT 1 FROM book WHERE medimops_url=?)'

    cursor = conn.cursor()
    exists = cursor.execute(sql, (url,)).fetchone()[0]

    return exists == 1


def monitoring_book_exists(conn: sqlite3.Connection, url: str) -> bool:
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


def get_missing_urls(conn: sqlite3.Connection, urls: list) -> list:
    missing_urls = list()
    for url in urls:
        if (not book_exists(conn, url)):
            missing_urls.append(url)

    return missing_urls


def get_monitoring_urls(conn: sqlite3.Connection) -> list:
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


def get_unwanted_urls(conn: sqlite3.Connection) -> list:
    unwanted_urls = list()
    monitoring_urls = get_monitoring_urls(conn)
    csv_urls = get_csv_urls(URL_FILES)

    for url in monitoring_urls:
        if (not url in csv_urls):
            unwanted_urls.append(url)

    return unwanted_urls


def insert_entry(conn: sqlite3.Connection, entry_data: EntryData) -> None:
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


def user_exists(conn: sqlite3.Connection, mail: str) -> bool:
    sql = '''
        SELECT EXISTS (SELECT 1 FROM user
        WHERE user.email=?) 
    '''

    cursor = conn.cursor()
    if (cursor.execute(sql, (mail,)).fetchone()[0]):
        return True

    else:
        return False


def insert_user(conn: sqlite3.Connection, name: str, last_name: str, email: str):
    sql = 'INSERT OR IGNORE INTO user(name, last_name, email) VALUES(?,?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (name, last_name, email))


def check_users(conn: sqlite3.Connection) -> list:
    import glob

    urls = list()

    for filepath in glob.iglob('db/urls/*.txt'):
        with open(filepath, 'r') as file:
            lines = [line.rstrip() for line in file]
            
            name = lines[0]
            last_name = lines[1]
            email = lines[2]
            
            if(not user_exists(conn, lines[2])):
                print(f'"{email}" does not exist yet.')
                insert_user(conn, name, last_name, email)
                
            for i in range(len(lines)):
                if(i > 2 and valid_mm_url(lines[i])):
                    urls.append(lines[i])
            
            # urls.append([lines[i] for i in range(len(lines)) if i > 2 and valid_mm_url(lines[i])])
           
    return urls
                

# Iterates through csv file and checks if there is a book entry for each url
# If not, stores missing urls and gets data from the website afterwards
def update_books() -> None:
    # conn = create_db_connection('db/mmps_db.sqlite')
    # missing_urls = get_missing_urls(conn)
    # unwanted_urls = get_unwanted_urls(conn)
    
    conn = create_db_connection("db/mmps_db.sqlite")
    user_urls = check_users(conn)
    missing_urls = get_missing_urls(conn, user_urls)

    # TODO: actually removing unwanted urls
    # print(f'Unwanted urls: \n{unwanted_urls}\n')

    if (not missing_urls):
        print('Database is up-to-date. No urls are missing!')
        return

    print(missing_urls)

    amount_books = len(missing_urls)
    data = get_api_data(missing_urls)

    for data_row in data:
        insert_entry(conn, data_row)

    # urls_to_monitoring_list(conn)

    conn.commit()

    print(f'--> Update done. {len(missing_urls)} new book(s)')
        


if __name__ == "__main__":
    update_books()
    
