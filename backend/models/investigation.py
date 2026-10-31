
import uuid
from datetime import datetime, timezone

from backend.database import (
    get_connection,
    record_event
)


def current_timestamp():
    return datetime.now(timezone.utc).isoformat()


def create_investigation(question, title=None):

    investigation_id = str(uuid.uuid4())

    title = title or question[:80]

    timestamp = current_timestamp()

    conn = get_connection()

    try:
        with conn:

            conn.execute(
                """
                INSERT INTO investigations (
                    id,
                    title,
                    question,
                    status,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    investigation_id,
                    title,
                    question,
                    "created",
                    timestamp,
                    timestamp
                )
            )

            record_event(
                conn,
                investigation_id,
                "investigation.created",
                {
                    "title": title,
                    "question": question
                },
                timestamp
            )

        return get_investigation(investigation_id)

    finally:
        conn.close()


def get_investigation(investigation_id):

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM investigations
            WHERE id = ?
            """,
            (investigation_id,)
        ).fetchone()

        return dict(row) if row else None

    finally:
        conn.close()


def list_investigations():

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM investigations
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


def get_investigation_events(investigation_id):

    import json

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM events
            WHERE investigation_id = ?
            ORDER BY id ASC
            """,
            (investigation_id,)
        ).fetchall()

        result = []

        for row in rows:

            event = dict(row)
            event["payload"] = json.loads(
                event.pop("payload_json")
            )

            result.append(event)

        return result

    finally:
        conn.close()
