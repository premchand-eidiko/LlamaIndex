"""
Persistent Chat History Service
================================

RESPONSIBILITY
--------------
This file stores and retrieves conversations from SQLite.

WHY DO WE NEED IT?
------------------
LlamaIndex Chat Engine memory is normally kept in application
memory. If the application restarts, that memory disappears.

Our application needs:

    New Chat
        ↓
    Continue later
        ↓
    Restart backend
        ↓
    Previous chats still available

Therefore we store conversations permanently in SQLite.

FLOW
----
Frontend
    ↓
conversations.py / chat.py
    ↓
chat_history.py
    ↓
SQLite database
    ↓
data/chat_history.db
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional

from app.config import CHAT_DATABASE


# ==================================================
# DATABASE CONNECTION
# ==================================================

def get_connection():
    """
    Creates a connection to the SQLite database.

    Called by:
        - create_chat()
        - list_chats()
        - get_chat_messages()
        - add_message()
        - delete_chat()

    Returns:
        sqlite3.Connection
    """

    connection = sqlite3.connect(
        CHAT_DATABASE
    )

    connection.row_factory = sqlite3.Row

    return connection


# ==================================================
# INITIALIZE DATABASE
# ==================================================

def initialize_database():
    """
    Creates the required database tables.

    Tables:

        chats
        messages

    This function is called when the FastAPI
    application starts.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # --------------------------------------------------
    # Chat table
    # --------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (

            id TEXT PRIMARY KEY,

            title TEXT NOT NULL,

            created_at TEXT NOT NULL,

            updated_at TEXT NOT NULL
        )
        """
    )

    # --------------------------------------------------
    # Message table
    # --------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            chat_id TEXT NOT NULL,

            role TEXT NOT NULL,

            content TEXT NOT NULL,

            sources TEXT,

            created_at TEXT NOT NULL,

            FOREIGN KEY(chat_id)
                REFERENCES chats(id)
                ON DELETE CASCADE
        )
        """
    )

    connection.commit()

    connection.close()


# ==================================================
# CREATE CHAT
# ==================================================

def create_chat(
    chat_id: str,
    title: str = "New Chat",
):
    """
    Creates a new conversation.

    Input:
        chat_id
        title

    Output:
        None

    Database:
        chats table
    """

    now = datetime.now().isoformat()

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO chats (
            id,
            title,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            chat_id,
            title,
            now,
            now,
        ),
    )

    connection.commit()

    connection.close()


# ==================================================
# LIST CHATS
# ==================================================

def list_chats():
    """
    Returns all previous conversations.

    Newest conversations are returned first.

    Output example:

    [
        {
            "id": "abc",
            "title": "Employee Benefits",
            "created_at": "...",
            "updated_at": "..."
        }
    ]
    """

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            id,
            title,
            created_at,
            updated_at

        FROM chats

        ORDER BY updated_at DESC
        """
    ).fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


# ==================================================
# GET ONE CHAT
# ==================================================

def get_chat(chat_id: str):
    """
    Retrieves a single chat's metadata.
    """

    connection = get_connection()

    row = connection.execute(
        """
        SELECT
            id,
            title,
            created_at,
            updated_at

        FROM chats

        WHERE id = ?
        """,
        (chat_id,),
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


# ==================================================
# GET CHAT MESSAGES
# ==================================================

def get_chat_messages(
    chat_id: str,
):
    """
    Retrieves all messages belonging to one chat.

    Output:

    [
        {
            "role": "user",
            "content": "...",
            "sources": [...]
        },
        {
            "role": "assistant",
            "content": "...",
            "sources": [...]
        }
    ]
    """

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            role,
            content,
            sources,
            created_at

        FROM messages

        WHERE chat_id = ?

        ORDER BY id ASC
        """,
        (chat_id,),
    ).fetchall()

    connection.close()

    messages = []

    for row in rows:

        sources = []

        if row["sources"]:

            try:

                sources = json.loads(
                    row["sources"]
                )

            except json.JSONDecodeError:

                sources = []

        messages.append(
            {
                "role": row["role"],
                "content": row["content"],
                "sources": sources,
                "created_at": row["created_at"],
            }
        )

    return messages


# ==================================================
# ADD MESSAGE
# ==================================================

def add_message(
    chat_id: str,
    role: str,
    content: str,
    sources: Optional[list] = None,
):
    """
    Saves one message to the database.

    Called by:
        chat.py

    Input:
        chat_id
        role
        content
        sources

    Output:
        None
    """

    now = datetime.now().isoformat()

    sources_json = json.dumps(
        sources or []
    )

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO messages (
            chat_id,
            role,
            content,
            sources,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            chat_id,
            role,
            content,
            sources_json,
            now,
        ),
    )

    # Update the chat's latest activity.

    connection.execute(
        """
        UPDATE chats

        SET updated_at = ?

        WHERE id = ?
        """,
        (
            now,
            chat_id,
        ),
    )

    connection.commit()

    connection.close()


# ==================================================
# UPDATE CHAT TITLE
# ==================================================

def update_chat_title(
    chat_id: str,
    title: str,
):
    """
    Updates the title displayed in the frontend sidebar.
    """

    connection = get_connection()

    connection.execute(
        """
        UPDATE chats

        SET title = ?

        WHERE id = ?
        """,
        (
            title,
            chat_id,
        ),
    )

    connection.commit()

    connection.close()


def remove_document_sources(file_name: str) -> None:
    """Remove saved source excerpts for a deleted file from chat messages."""
    connection = get_connection()
    rows = connection.execute(
        "SELECT id, sources FROM messages WHERE sources IS NOT NULL"
    ).fetchall()

    for row in rows:
        try:
            sources = json.loads(row["sources"])
        except json.JSONDecodeError:
            continue

        remaining_sources = [
            source
            for source in sources
            if source.get("file_name") != file_name
        ]

        if len(remaining_sources) != len(sources):
            connection.execute(
                "UPDATE messages SET sources = ? WHERE id = ?",
                (json.dumps(remaining_sources), row["id"]),
            )

    connection.commit()
    connection.close()


# ==================================================
# DELETE CHAT
# ==================================================

def delete_chat(
    chat_id: str,
):
    """
    Deletes an entire conversation.

    Because messages use ON DELETE CASCADE,
    associated messages are also removed.
    """

    connection = get_connection()

    connection.execute(
        """
        DELETE FROM messages

        WHERE chat_id = ?
        """,
        (chat_id,),
    )

    connection.execute(
        """
        DELETE FROM chats

        WHERE id = ?
        """,
        (chat_id,),
    )

    connection.commit()

    connection.close()