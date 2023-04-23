import csv
import sqlite3 as sql
import undetected_chromedriver as uc
from datetime import date, datetime
import time
import json
import random
from tqdm import tqdm

from classes.book import Book
from classes.author import Author
from classes.individual_price_data import IndividualPriceData
from classes.scan_data import ScanData

from functions import convert_url, create_db_connection

def get_scan_urls(conn: sql.Connection) -> list:
    sql = '''
        SELECT medimops_url,  book.book_id
        FROM book, monitoring_books as mb
        WHERE book.book_id = mb.book_id
    '''

    cursor = conn.cursor()
    data = cursor.execute(sql).fetchall()

    random.shuffle(data)

    return data


def handle_pre(pre: tuple, url: str) -> ScanData:
    data = json.loads(pre)

    content = data["content"]
    product = content["product"]
    productAttributes = content["productAttributes"]
    preferredVariant = content["preferredVariant"]

    title = product["title"]
    author = product["manufacturer"]
    pages = productAttributes["numberOfPages"]["value"]
    medium = productAttributes["medium"]["value"]
    stock = preferredVariant["stock"]

    if (not preferredVariant["price"]):
        price = None
        on_sale = False
    else:
        price = float(preferredVariant["price"])
        on_sale = preferredVariant["isSale"]

    if (not 'listPrice' in preferredVariant):
        if ('variants' in product):
            if (product['variants'][0]['condition'] == 'Neu'):
                price_new = product['variants'][0]['price']
        else:
            price_new = None
    else:
        price_new = preferredVariant["listPrice"]

    book = Book(title, pages, medium, url)
    author = Author(author, None)
    individual_scan_data = IndividualPriceData(
        price, price_new, None, on_sale, None, None, stock)

    return ScanData(book, author, individual_scan_data)


def get_api_data(urls: list) -> list:
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    driver = uc.Chrome(options=options)
    data = list()
    i = 0

    for url in tqdm(urls):
        driver.get(convert_url(url[0]))
        if (i == 0):
            time.sleep(random.uniform(8.0, 10.0))
        else:
            time.sleep(random.uniform(1.0, 3.0))

        data.append(handle_pre(driver.find_element(
            "tag name", 'pre').text, url[0]))
        i += 1
    driver.quit()
    return data


def insert_individual_scan(conn: sql.Connection, data: list, scan_id: int) -> None:
    cursor = conn.cursor()
    sql = 'SELECT book_id FROM book WHERE medimops_url=?'
    book_id = cursor.execute(sql, (data.book.medimops_url,)).fetchone()[0]

    sql = 'INSERT OR IGNORE INTO scan_result(scan_id, book_id, price, price_new, on_sale, in_stock) VALUES(?,?,?,?,?,?)'

    cursor.execute(sql, (scan_id, book_id, data.individual_scan_data.price, data.individual_scan_data.price_new,
                   data.individual_scan_data.on_sale, data.individual_scan_data.stock))


def insert_scan(conn: sql.Connection, start_time: float, execution_time: float, amount_books: int) -> None:
    sql = 'INSERT OR IGNORE INTO scan(date, start_time, execution_time, amount_books) VALUES(?,?,?,?)'

    cursor = conn.cursor()
    cursor.execute(sql, (date.today().strftime("%d/%m/%Y"),
                   start_time, execution_time, amount_books))

    with open('db/scan_log.csv', 'a', encoding='UTF8') as file:
        writer = csv.writer(file)
        writer.writerow((date.today().strftime("%d/%m/%Y"),
                         start_time, execution_time, amount_books))


def data_to_db(data: list, conn: sql.Connection, start_time: float, execution_time: float) -> None:
    cursor = conn.cursor()

    sql = 'SELECT scan_id FROM scan ORDER BY scan_id DESC LIMIT 1'

    scan_id = cursor.execute(
        sql).fetchone()[0] + 1

    for data_row in data:
        insert_individual_scan(conn, data_row, scan_id)

    insert_scan(conn, start_time, execution_time, len(data))

    conn.commit()


def scan() -> bool:
    conn = create_db_connection('db/mmps_db.sqlite')
    scan_urls = get_scan_urls(conn)

    if (len(scan_urls) > 0):
        conn = create_db_connection('db/mmps_db.sqlite')
        scan_urls = get_scan_urls(conn)

        start_time = time.time()

        now = datetime.now().strftime("%H:%M:%S")

        try:
            data = get_api_data(scan_urls)
            execution_time = round(time.time() - start_time, 2)
            data_to_db(data, conn, now, execution_time)
            return True
        except:
            print(Exception)
            return False

    else:
        return False
