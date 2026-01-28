from .db import db_connection


def get_label(key: str) -> str | None:
    with db_connection() as conn:
        row = conn.execute("SELECT value FROM ui_labels WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def L(key: str, default_value: str) -> str:
    value = get_label(key)
    return value if value is not None and value != "" else default_value


def upsert_ui_label(key: str, value: str) -> None:
    with db_connection() as conn:
        conn.execute(
            """
            INSERT INTO ui_labels (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def list_ui_labels(keys: list[str]) -> dict[str, str]:
    if not keys:
        return {}
    placeholders = ",".join("?" for _ in keys)
    with db_connection() as conn:
        rows = conn.execute(
            f"SELECT key, value FROM ui_labels WHERE key IN ({placeholders})",
            tuple(keys),
        ).fetchall()
    return {row["key"]: row["value"] for row in rows}
