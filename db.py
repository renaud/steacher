import sqlite3
import json
from typing import List, Dict


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
            question_id TEXT,
            data TEXT
        )
    ''')
    # Create a new table for grading results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS grading_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            question_id TEXT,
            created_at TEXT,
            score INTEGER,
            rubric_evaluated TEXT
        )
    ''')
    conn.commit()
    conn.close()


def save_messages(student_id: str, question_id: str, messages: List[Dict]):

    # Do not store empty chats
    if not any(msg['role'] == 'user' for msg in messages):
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    # Use 'REPLACE INTO' to overwrite existing chat with the same chat_id
    cursor.execute(
        "REPLACE INTO history (student_id, question_id, data) VALUES (?, ?, ?)",
        (student_id, question_id, json.dumps(messages))
    )
    conn.commit()
    conn.close()


def get_messages(student_id: str, question_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT data FROM history WHERE student_id = ? AND question_id = ?", (student_id, question_id))
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row['data'])
    return None


def save_grading_result(student_id: str, question_id: str, created_at: str, score: int, rubric_evaluated: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO grading_results (student_id, question_id, created_at, score, rubric_evaluated) VALUES (?, ?, ?, ?, ?)",
        (student_id, question_id, created_at, score, rubric_evaluated)
    )
    conn.commit()
    conn.close()
