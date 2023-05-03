import sqlite3

def create_connection():
    conn = sqlite3.connect('amazon_data.db')
    return conn

def create_table(conn):
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS product_data (
                        id INTEGER PRIMARY KEY,
                        query TEXT NOT NULL,
                        timestamp TEXT NOT NULL,
                        item_name TEXT NOT NULL,
                        com_price REAL,
                        co_uk_price REAL,
                        de_price REAL,
                        ca_price REAL)''')
    conn.commit()

def init_db():
    conn = create_connection()
    create_table(conn)
    conn.close()

def count_searches_today():
    conn = create_connection()
    cursor = conn.cursor()
    today = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute("SELECT COUNT(*) FROM product_data WHERE timestamp LIKE ?", (f"{today}%",))
    result = cursor.fetchone()
    conn.close()
    return result[0]