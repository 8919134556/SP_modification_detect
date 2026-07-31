from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
EXPORT_ROOT = BASE_DIR / "exported_sql"

load_dotenv(BASE_DIR / ".env")


@dataclass
class ChangeRecord:
    change_id: int
    event_type: str
    database_name: str
    schema_name: str
    object_name: str
    original_login_name: str | None
    changed_at: object
    object_definition: str | None
    command_text: str | None


def get_connection() -> pyodbc.Connection:
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    driver = os.getenv("DB_DRIVER")

    required_values = {
        "DB_SERVER": server,
        "DB_NAME": database,
        "DB_DRIVER": driver,
    }

    missing = [key for key, value in required_values.items() if not value]

    if missing:
        raise ValueError(
            f"Missing environment variables: {', '.join(missing)}"
        )

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )

    return pyodbc.connect(connection_string)


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", value)
    cleaned = cleaned.strip().strip(".")
    return cleaned or "unnamed"


def fetch_pending_changes(
    connection: pyodbc.Connection,
) -> list[ChangeRecord]:
    query = """
        SELECT TOP (20)
            ChangeId,
            EventType,
            DatabaseName,
            SchemaName,
            ObjectName,
            OriginalLoginName,
            ChangedAt,
            ObjectDefinition,
            CommandText
        FROM dbo.DatabaseObjectChangeLog
        WHERE GitStatus = 'Pending'
        ORDER BY ChangeId ASC;
    """

    cursor = connection.cursor()
    rows = cursor.execute(query).fetchall()

    return [
        ChangeRecord(
            change_id=row.ChangeId,
            event_type=row.EventType,
            database_name=row.DatabaseName,
            schema_name=row.SchemaName or "dbo",
            object_name=row.ObjectName,
            original_login_name=row.OriginalLoginName,
            changed_at=row.ChangedAt,
            object_definition=row.ObjectDefinition,
            command_text=row.CommandText,
        )
        for row in rows
    ]


def build_export_path(change: ChangeRecord) -> Path:
    database_name = safe_filename(change.database_name)
    schema_name = safe_filename(change.schema_name)
    object_name = safe_filename(change.object_name)

    return (
        EXPORT_ROOT
        / database_name
        / "StoredProcedures"
        / f"{schema_name}.{object_name}.sql"
    )


def export_change(change: ChangeRecord) -> Path:
    target_path = build_export_path(change)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if change.event_type == "DROP_PROCEDURE":
        if target_path.exists():
            target_path.unlink()
            print(f"Deleted file: {target_path}")
        else:
            print(f"File not found for deleted SP: {target_path}")

        return target_path

    definition = change.object_definition or change.command_text

    if not definition:
        raise ValueError(
            f"No SQL definition found for "
            f"{change.schema_name}.{change.object_name}"
        )

    header = (
        f"-- Database: {change.database_name}\n"
        f"-- Object: {change.schema_name}.{change.object_name}\n"
        f"-- Event: {change.event_type}\n"
        f"-- Changed By: {change.original_login_name or 'Unknown'}\n"
        f"-- Changed At: {change.changed_at}\n"
        f"-- Audit ChangeId: {change.change_id}\n"
        f"-- Auto-generated from SQL Server.\n\n"
    )

    target_path.write_text(
        header + definition.rstrip() + "\n",
        encoding="utf-8",
    )

    return target_path


def main() -> int:
    try:
        with get_connection() as connection:
            print("SQL Server connection successful.")

            changes = fetch_pending_changes(connection)

            if not changes:
                print("No pending stored procedure changes found.")
                return 0

            print(f"Pending changes found: {len(changes)}")
            print("-" * 100)

            for change in changes:
                exported_path = export_change(change)

                print(f"Change ID  : {change.change_id}")
                print(f"Event Type : {change.event_type}")
                print(
                    f"Object     : "
                    f"{change.schema_name}.{change.object_name}"
                )
                print(f"Exported   : {exported_path}")
                print("-" * 100)

        return 0

    except pyodbc.Error as exc:
        print(f"SQL Server connection error: {exc}")
        return 1

    except Exception as exc:
        print(f"Application error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())