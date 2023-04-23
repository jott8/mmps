import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import math


def isNan(num):
    return num != num


def create_db_connection(db_file) -> sqlite3.Connection:
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as err:
        print(err)

    return conn


def get_entries(conn: sqlite3.Connection) -> list:
    entries = []

    cursor = conn.cursor()
    sql = 'SELECT book_id FROM monitoring_books'
    result = cursor.execute(sql).fetchall()

    for entry in result:
        entries.append(entry[0])

    return entries


def generate_graphs() -> None:
    conn = create_db_connection('db/mmps_db.sqlite')
    cursor = conn.cursor()

    entries = get_entries(conn)
    i = 0

    for entry in entries:
        # if (i > 1):
        #     break
        sql = 'SELECT book.title FROM book WHERE book_id=?'
        title = cursor.execute(sql, (entry,)).fetchone()[0]

        sql = sql = f'''
            SELECT max(price)
            FROM scan_result, scan
            WHERE scan_result.scan_id = scan.scan_id
            AND scan_result.book_id = {entry}
            AND NOT scan.scan_id = 1'''

        max_price = cursor.execute(sql).fetchone()[0]

        if (not max_price):
            max_price = 10
        elif (max_price - max_price == 0):
            max_price += 10
        else:
            max_price += 10

        sql = f'''
            SELECT scan.scan_id AS scan_id, price, date
            FROM scan_result, scan, book
            WHERE scan_result.scan_id = scan.scan_id
            AND book.book_id = scan_result.book_id
            AND book.book_id = {entry}
            AND NOT scan.scan_id = 1'''
        data = pd.read_sql(sql, conn)

        length = len(data.date)
        # print(f'{i}: {length}')

        # TODO: Adapt x-axis for books that haven't been watched since scan 1, show dates?
        # TODO: Signal if book is currently unavailable (now: e.g. recent scan_id = 160, x-axis stops at 140 if it hasn't been available since scan 140)
        _, ax = plt.subplots()

        if (length > 4 and isNan(data.price[length-1]) and isNan(data.price[length-2]) and isNan(data.price[length-3]) and isNan(data.price[length-4])):
            color = "red"
        else:
            color = "green"

        ax.plot(data.scan_id, data.price, color=color)

        plt.title(title)
        plt.xlabel('scan_id')
        plt.ylabel('Price in €')
        plt.ylim(0, max_price)

        if length > 50:
            pos1 = 0
            pos2 = math.ceil(length*(1/5))
            pos3 = round(length/2)
            pos4 = round(length*(4/5))
            pos5 = length-1

            positions = [pos1, pos2, pos3, pos4, pos5]

            plt.xticks(positions, [
                (data.date[x][:6] + data.date[x][8:]) for x in positions])

        plt.subplots_adjust(bottom=0.15)

        plt.savefig(f'plotting/graphs/graph{i}.png')
        plt.cla()
        plt.close()
        i += 1
