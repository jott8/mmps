import sqlite3

db_path = 'db/mmps_db.sqlite'
conn = sqlite3.connect(db_path)

author_table = '''
    CREATE TABLE IF NOT EXISTS "author" (
	"author_id"	INTEGER NOT NULL UNIQUE,
	"name"	TEXT NOT NULL UNIQUE,
	"last_name"	TEXT,
	PRIMARY KEY("author_id")
	);
'''

book_table = '''
	CREATE TABLE IF NOT EXISTS "book" (
		"book_id"	INTEGER NOT NULL UNIQUE,
		"title"	TEXT NOT NULL,
		"pages"	INTEGER,
		"medium"	TEXT,
		"author_id"	INTEGER NOT NULL,
		"medimops_url"	TEXT NOT NULL UNIQUE,
		"api_url"	TEXT NOT NULL UNIQUE,
		PRIMARY KEY("book_id")
	);
'''

monitoring_books_table = '''
	CREATE TABLE IF NOT EXISTS "monitoring_books" (
		"monitoring_id"	INTEGER NOT NULL,
		"book_id"	INTEGER NOT NULL,
		PRIMARY KEY("monitoring_id","book_id")
	);
'''

monitoring_order_table = '''
	CREATE TABLE IF NOT EXISTS "monitoring_order" (
		"monitoring_id"	INTEGER NOT NULL UNIQUE,
		"user_id"	INTEGER NOT NULL UNIQUE,
		PRIMARY KEY("monitoring_id" AUTOINCREMENT)
	);
'''

scan_log_table = '''
	CREATE TABLE IF NOT EXISTS "scan" (
		"scan_id"	INTEGER NOT NULL UNIQUE,
		"date"	TEXT NOT NULL,
		"start_time"	INTEGER NOT NULL,
		"execution_time"	INTEGER,
		"error_msg"	TEXT,
		"amount_books"	INTEGER,
		PRIMARY KEY("scan_id")
	);
'''

scan_result_table = '''
	CREATE TABLE IF NOT EXISTS "scan_result" (
		"scan_id"	INTEGER NOT NULL,
		"book_id"	INTEGER NOT NULL,
		"price"	INTEGER,
		"price_new"	INTEGER,
		"on_sale"	INTEGER NOT NULL,
		"sale_percentage"	INTEGER,
		"in_stock"	INTEGER
	);
'''

user_table = '''
	CREATE TABLE IF NOT EXISTS "user" (
		"user_id"	INTEGER NOT NULL UNIQUE,
		"name"	TEXT NOT NULL,
		"last_name"	TEXT NOT NULL,
		"email"	TEXT NOT NULL UNIQUE,
		PRIMARY KEY("user_id")
	);
'''

# TODO: 'conn.executescript(...) instead of many individual executions'
conn.execute(author_table)
conn.execute(book_table)
conn.execute(monitoring_books_table)
conn.execute(monitoring_order_table)
conn.execute(scan_log_table)
conn.execute(scan_result_table)
conn.execute(user_table)
