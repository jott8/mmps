import time
from functions import create_db_connection
import sqlite3


SIGNIFICANCE_RATE = -0.25


def get_recent_scan_ids(conn: sqlite3.Connection) -> list:
    cursor = conn.cursor()
    ids = list()

    sql = '''
        SELECT scan_id 
        FROM (SELECT scan_id FROM scan ORDER BY scan_id DESC LIMIT 2)
        ORDER BY scan_id ASC
    '''

    temp_result = cursor.execute(sql).fetchall()

    for i in range(2):
        ids.append(temp_result[i][0])

    return ids


def get_scan_result(conn: sqlite3.Connection, scan_id: int):
    cursor = conn.cursor()

    sql = '''
        SELECT *
        FROM scan_result
        WHERE scan_id = ?
        ORDER BY book_id ASC    
    '''

    return cursor.execute(sql, (scan_id, )).fetchall()


def get_all_results(conn: sqlite3.Connection, scan_ids: list):
    scan_results = list()

    for scan_id in scan_ids:
        scan_results.append(get_scan_result(conn, scan_id))

    return scan_results


# Monitoring id('s) for each book with a significant price change
def get_monitoring_id(conn: sqlite3.Connection, book_id: list) -> list:
    cursor = conn.cursor()
    ids = list()
    temp_ids = list()

    sql = '''
        SELECT monitoring_id 
        FROM monitoring_books
        WHERE book_id = ?
    '''
    temp_ids.append(cursor.execute(sql, (book_id,)).fetchall())

    i = 0
    for temp_id in temp_ids:
        ids.append(temp_id[i][0])

    return ids


def get_significant_changes(conn: sqlite3.Connection, scan_results: list) -> list:
    i = 0
    significant_changes = list()

    for data in scan_results[1]:
        if (scan_results[0][i][1] == data[1]):
            price1 = scan_results[0][i][2]
            price2 = data[2]
            if (not price1 == None and not price2 == None):
                percentage = round((price2-price1) / price1, 5)

                if (percentage < SIGNIFICANCE_RATE):
                    significant_changes.append(
                        {'book_id': data[1], 'percentage': percentage, 'user': get_users(conn, get_monitoring_id(conn, data[1]))})
                print(f'{price1}       {price2}       {percentage}')
        i += 1
    return significant_changes


def get_users(conn: sqlite3.Connection, monitoring_id: list) -> list:
    cursor = conn.cursor()
    users = list()
    temp_users = list()

    if (not monitoring_id):
        return users

    for m_id in monitoring_id:
        sql = '''
            SELECT U.user_id, U.name, U.email
            FROM monitoring_order M, user U
            WHERE U.user_id = M.user_id
            AND monitoring_id = ?
        '''

        temp_users.append(cursor.execute(sql, (m_id, )).fetchall())

    i = 0

    for temp in temp_users:
        users.append(
            {'user_id': temp[i][0], 'name': temp[i][1], 'mail': temp[i][2]})

    return users


def compare():
    conn = create_db_connection('db/mmps_db.sqlite')
    scan_ids = get_recent_scan_ids(conn)
    scan_results = get_all_results(conn, scan_ids)
    significant_changes = get_significant_changes(conn, scan_results)
    print(significant_changes)
