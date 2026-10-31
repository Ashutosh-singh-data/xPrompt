
import sqlite3
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Database location
DB_PATH = Path(
    os.getenv("DATABASE_PATH", "data/consultos.db")
)

if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH

# Ensure database directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection():
    """Create and return a SQLite database connection."""

    conn = sqlite3.connect(
        DB_PATH,
        timeout=30
    )

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")

    return conn


def init_db():
    """Initialize all ConsultOS database tables."""

    conn = get_connection()

    try:
        conn.executescript("""

        CREATE TABLE IF NOT EXISTS investigations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            question TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            version INTEGER NOT NULL,
            plan_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,

            FOREIGN KEY (investigation_id)
                REFERENCES investigations(id),

            UNIQUE(investigation_id, version)
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            dependencies TEXT NOT NULL DEFAULT '[]',
            assigned_tool TEXT,
            expected_output TEXT,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            result_json TEXT,
            error TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,

            FOREIGN KEY (investigation_id)
                REFERENCES investigations(id),

            FOREIGN KEY (plan_id)
                REFERENCES plans(id)
        );

        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            task_id TEXT,
            source_file TEXT,
            evidence_type TEXT NOT NULL,
            query_or_method TEXT,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (investigation_id)
                REFERENCES investigations(id),

            FOREIGN KEY (task_id)
                REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investigation_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (investigation_id)
                REFERENCES investigations(id)
        );

        CREATE TABLE IF NOT EXISTS tool_runs (
            id TEXT PRIMARY KEY,
            investigation_id TEXT NOT NULL,
            task_id TEXT,
            tool_name TEXT NOT NULL,
            status TEXT NOT NULL,
            duration_ms INTEGER,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            error TEXT,
            created_at TEXT NOT NULL,

            FOREIGN KEY (investigation_id)
                REFERENCES investigations(id),

            FOREIGN KEY (task_id)
                REFERENCES tasks(id)
        );

        CREATE INDEX IF NOT EXISTS idx_events_investigation
        ON events(investigation_id, id);

        CREATE INDEX IF NOT EXISTS idx_tasks_investigation
        ON tasks(investigation_id);

        CREATE INDEX IF NOT EXISTS idx_evidence_investigation
        ON evidence(investigation_id);

        CREATE INDEX IF NOT EXISTS idx_tool_runs_investigation
        ON tool_runs(investigation_id);

        """)

        conn.commit()

    finally:
        conn.close()


def record_event(
    conn,
    investigation_id,
    event_type,
    payload,
    timestamp
):
    """
    Record an event inside the caller's transaction.
    The caller is responsible for committing the transaction.
    """

    import json

    conn.execute(
        """
        INSERT INTO events (
            investigation_id,
            event_type,
            payload_json,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            investigation_id,
            event_type,
            json.dumps(payload),
            timestamp
        )
    )
