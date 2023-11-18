import sqlite3

def get_db_connection():
    conn = sqlite3.connect('games.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    # Include 'reviews' and 'requirements' columns of type TEXT
    conn.execute('''CREATE TABLE IF NOT EXISTS games (
                        appid INTEGER,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL,
                        icon_url TEXT,
                        source TEXT)''')
    conn.commit()
    conn.close()

create_tables()
