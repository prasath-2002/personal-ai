import sqlite3
from pathlib import Path


DB_PATH = Path("data/personal_ai.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


def save_message(session_id: str, role: str, content: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO messages (session_id, role, content)
        VALUES (?, ?, ?)
        """,
        (session_id, role, content),
    )

    connection.commit()
    connection.close()


def get_messages(session_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT role, content
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (session_id,),
    )

    rows = cursor.fetchall()
    connection.close()

    return [
        {
            "role": role,
            "content": content,
        }
        for role, content in rows
    ]

def clear_messages(session_id: str):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM messages
        WHERE session_id = ?
        """,
        (session_id,),
    )

    connection.commit()
    connection.close()