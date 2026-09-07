import os
import sqlite3


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "data",
    "automail.db"
)


def get_connection():

    os.makedirs(
        os.path.dirname(DATABASE_PATH),
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------
    # Base tables
    # --------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            message_id TEXT,
            error TEXT,
            sent_at TEXT,
            FOREIGN KEY (campaign_id)
                REFERENCES campaigns(id)
        )
    """)

    # --------------------------------------------
    # Campaign configuration migration
    # --------------------------------------------

    cursor.execute(
        "PRAGMA table_info(campaigns)"
    )

    existing_columns = {
        row["name"]
        for row in cursor.fetchall()
    }

    if "template" not in existing_columns:

        cursor.execute("""
            ALTER TABLE campaigns
            ADD COLUMN template TEXT
        """)

    if "attachment_path" not in existing_columns:

        cursor.execute("""
            ALTER TABLE campaigns
            ADD COLUMN attachment_path TEXT
        """)

    if "delay_seconds" not in existing_columns:

        cursor.execute("""
            ALTER TABLE campaigns
            ADD COLUMN delay_seconds INTEGER
        """)

    connection.commit()
    connection.close()