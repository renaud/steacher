import sqlite3
import datetime
import json

def get_db_connection():
    conn = sqlite3.connect('history.db')
    conn.row_factory = sqlite3.Row  # Enable fetching columns by name
    return conn


def initialize_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            student_id TEXT PRIMARY KEY,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_messages(student_id, messages):

    # Do not store empty chats
    if not any(msg['role'] == 'user' for msg in messages):
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Use 'REPLACE INTO' to overwrite existing chat with the same chat_id
    cursor.execute(
        "REPLACE INTO history (student_id, data) VALUES (?, ?)",
        (student_id, json.dumps(messages))
    )
    conn.commit()
    conn.close()


def get_messages(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM history WHERE student_id = ?", (student_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['data'])
    return None
