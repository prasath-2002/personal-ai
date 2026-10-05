import json
import sqlite3
from pathlib import Path
from app.core.config import DATA_DIR


DB_PATH = DATA_DIR / "personal_ai.db"


# =========================================
# DATABASE CONNECTION
# =========================================

def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH
    )

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# =========================================
# DATABASE INITIALIZATION
# =========================================

def initialize_database():
    connection = get_connection()

    cursor = connection.cursor()


    # -------------------------------------
    # Messages
    # -------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # -------------------------------------
    # Sessions
    # -------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # -------------------------------------
    # Documents
    # -------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            filename TEXT NOT NULL,
            file_hash TEXT,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
        """
    )


    # -------------------------------------
    # Document chunks
    # -------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding TEXT,
            FOREIGN KEY (document_id)
                REFERENCES documents(id)
                ON DELETE CASCADE
        )
        """
    )


    # =====================================
    # SAFE MIGRATIONS
    # =====================================

    # -------------------------------------
    # documents.file_hash migration
    # -------------------------------------

    document_columns = (
        connection.execute(
            "PRAGMA table_info(documents)"
        ).fetchall()
    )

    document_column_names = [
        column[1]
        for column in document_columns
    ]

    if (
        "file_hash"
        not in document_column_names
    ):
        connection.execute(
            """
            ALTER TABLE documents
            ADD COLUMN file_hash TEXT
            """
        )


    # -------------------------------------
    # document_chunks.embedding migration
    # -------------------------------------

    chunk_columns = (
        connection.execute(
            "PRAGMA table_info(document_chunks)"
        ).fetchall()
    )

    chunk_column_names = [
        column[1]
        for column in chunk_columns
    ]

    if (
        "embedding"
        not in chunk_column_names
    ):
        connection.execute(
            """
            ALTER TABLE document_chunks
            ADD COLUMN embedding TEXT
            """
        )


    # -------------------------------------
    # Helpful indexes
    # -------------------------------------

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_messages_session
        ON messages(session_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_documents_session
        ON documents(session_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chunks_session
        ON document_chunks(session_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS
        idx_chunks_document
        ON document_chunks(document_id)
        """
    )


    connection.commit()
    connection.close()


# =========================================
# CHAT MESSAGES
# =========================================

def save_message(
    session_id: str,
    role: str,
    content: str,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO messages (
            session_id,
            role,
            content
        )
        VALUES (?, ?, ?)
        """,
        (
            session_id,
            role,
            content,
        ),
    )

    connection.commit()
    connection.close()


def save_turn(session_id: str, message: str, response: str):
    connection = get_connection()
    try:
        with connection:
            connection.executemany(
                "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                [(session_id, "user", message), (session_id, "assistant", response)],
            )
    finally:
        connection.close()


def get_messages(
    session_id: str,
):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            role,
            content
        FROM messages
        WHERE session_id = ?
        ORDER BY id ASC
        """,
        (
            session_id,
        ),
    ).fetchall()

    connection.close()

    return [
        {
            "role": role,
            "content": content,
        }
        for role, content in rows
    ]


def clear_messages(
    session_id: str,
):
    connection = get_connection()

    connection.execute(
        """
        DELETE FROM messages
        WHERE session_id = ?
        """,
        (
            session_id,
        ),
    )

    connection.commit()
    connection.close()


# =========================================
# SESSIONS
# =========================================

def create_session(
    session_id: str,
    title: str,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO sessions (
            session_id,
            title
        )
        VALUES (?, ?)
        """,
        (
            session_id,
            title,
        ),
    )

    connection.commit()
    connection.close()


def get_sessions():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            session_id,
            title,
            created_at
        FROM sessions
        ORDER BY created_at DESC
        """
    ).fetchall()

    connection.close()

    return [
        {
            "session_id": row[0],
            "title": row[1],
            "created_at": row[2],
        }
        for row in rows
    ]


def rename_session(
    session_id: str,
    new_title: str,
):
    connection = get_connection()

    connection.execute(
        """
        UPDATE sessions
        SET title = ?
        WHERE session_id = ?
        """,
        (
            new_title,
            session_id,
        ),
    )

    connection.commit()
    connection.close()


def delete_session(
    session_id: str,
):
    connection = get_connection()

    connection.execute(
        """
        DELETE FROM document_chunks
        WHERE session_id = ?
        """,
        (
            session_id,
        ),
    )

    connection.execute(
        """
        DELETE FROM documents
        WHERE session_id = ?
        """,
        (
            session_id,
        ),
    )

    connection.execute(
        """
        DELETE FROM messages
        WHERE session_id = ?
        """,
        (
            session_id,
        ),
    )

    connection.execute(
        """
        DELETE FROM sessions
        WHERE session_id = ?
        """,
        (
            session_id,
        ),
    )

    connection.commit()
    connection.close()


# =========================================
# DOCUMENTS
# =========================================

def document_hash_exists(
    session_id: str,
    file_hash: str,
) -> bool:
    """
    Prevent the exact same file from being
    uploaded twice to the same chat.
    """

    connection = get_connection()

    row = connection.execute(
        """
        SELECT id
        FROM documents
        WHERE session_id = ?
        AND file_hash = ?
        LIMIT 1
        """,
        (
            session_id,
            file_hash,
        ),
    ).fetchone()

    connection.close()

    return row is not None


def create_document(
    session_id: str,
    filename: str,
    file_hash: str,
) -> int:
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO documents (
            session_id,
            filename,
            file_hash
        )
        VALUES (?, ?, ?)
        """,
        (
            session_id,
            filename,
            file_hash,
        ),
    )

    document_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return document_id


def get_documents(
    session_id: str,
):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            filename,
            created_at
        FROM documents
        WHERE session_id = ?
        ORDER BY id DESC
        """,
        (
            session_id,
        ),
    ).fetchall()

    connection.close()

    return [
        {
            "document_id": row[0],
            "filename": row[1],
            "created_at": row[2],
        }
        for row in rows
    ]


# =========================================
# DOCUMENT CHUNKS + EMBEDDINGS
# =========================================

def save_document_chunks(
    document_id: int,
    session_id: str,
    chunks: list[str],
):
    """
    Generate a local semantic embedding
    for every uploaded document chunk.

    No OpenAI/Groq API call.
    """

    from app.services.embedding_service import (
        generate_embedding,
    )

    # Compute vectors before opening a write transaction: model loading and
    # inference must not block unrelated chat writes in SQLite.
    rows = [
        (document_id, session_id, index, chunk, json.dumps(generate_embedding(chunk)))
        for index, chunk in enumerate(chunks)
    ]
    connection = get_connection()
    try:
        with connection:
            connection.executemany(
                """INSERT INTO document_chunks
                (document_id, session_id, chunk_index, content, embedding)
                VALUES (?, ?, ?, ?, ?)""",
                rows,
            )
    finally:
        connection.close()


# =========================================
# DELETE DOCUMENT
# =========================================

def delete_document(
    document_id: int,
):
    """
    Delete only this document and its chunks.

    Chat history remains untouched.
    """

    connection = get_connection()

    row = connection.execute(
        """
        SELECT session_id
        FROM documents
        WHERE id = ?
        """,
        (
            document_id,
        ),
    ).fetchone()

    if not row:
        connection.close()
        return None

    session_id = row[0]

    connection.execute(
        """
        DELETE FROM document_chunks
        WHERE document_id = ?
        """,
        (
            document_id,
        ),
    )

    connection.execute(
        """
        DELETE FROM documents
        WHERE id = ?
        """,
        (
            document_id,
        ),
    )

    connection.commit()
    connection.close()

    return session_id


# =========================================
# SEMANTIC RAG SEARCH
# =========================================

def search_document_chunks(
    session_id: str,
    query: str,
    limit: int = 5,
) -> list[dict]:
    """
    Semantic RAG retrieval with source metadata.

    Returns:
    [
        {
            "content": "...",
            "filename": "notes.txt",
            "document_id": 12,
            "score": 0.78
        }
    ]
    """

    from app.services.embedding_service import (
        cosine_similarity,
        generate_embedding,
    )

    clean_query = query.strip()

    if not clean_query:
        return []

    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                dc.id,
                dc.document_id,
                dc.content,
                dc.embedding,
                d.filename
            FROM document_chunks dc
            JOIN documents d
                ON d.id = dc.document_id
            WHERE dc.session_id = ?
            ORDER BY dc.document_id DESC,
                     dc.chunk_index ASC
            """,
            (session_id,),
        ).fetchall()

        if not rows:
            return []

        query_embedding = generate_embedding(
            clean_query
        )

        if not query_embedding:
            return []

        scored_chunks = []

        for (
            chunk_id,
            document_id,
            content,
            embedding_json,
            filename,
        ) in rows:
            chunk_embedding = None

            if embedding_json:
                try:
                    chunk_embedding = json.loads(
                        embedding_json
                    )
                except (
                    json.JSONDecodeError,
                    TypeError,
                ):
                    chunk_embedding = None

            # Backfill old chunks
            if not chunk_embedding:
                chunk_embedding = generate_embedding(
                    content
                )

                if chunk_embedding:
                    connection.execute(
                        """
                        UPDATE document_chunks
                        SET embedding = ?
                        WHERE id = ?
                        """,
                        (
                            json.dumps(
                                chunk_embedding
                            ),
                            chunk_id,
                        ),
                    )

            if not chunk_embedding:
                continue

            score = cosine_similarity(
                query_embedding,
                chunk_embedding,
            )

            scored_chunks.append(
                {
                    "content": content,
                    "filename": filename,
                    "document_id": document_id,
                    "score": score,
                }
            )

        connection.commit()

    finally:
        connection.close()

    scored_chunks.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    results = [
        item
        for item in scored_chunks
        if item["score"] >= 0.15
    ]

    if results:
        return results[:limit]

    return scored_chunks[:limit]
