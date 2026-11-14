
import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "outputs" / "experimentiq.db"

EXPECTED_TABLES = {
    "assignments",
    "audience_members",
    "conversion_events",
    "experiment_results",
    "experiment_state_events",
    "experiments",
    "exposure_events",
    "guardrail_metrics",
    "metric_definitions",
    "refund_events",
    "support_events",
    "variants",
}


@pytest.fixture
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    yield conn
    conn.close()


def test_database_exists():
    assert DB_PATH.exists()


def test_all_expected_tables_exist(connection):
    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert EXPECTED_TABLES.issubset(tables)


def test_experiment_count(connection):
    count = connection.execute(
        "SELECT COUNT(*) FROM experiments"
    ).fetchone()[0]
    assert count == 10


def test_audience_member_count(connection):
    count = connection.execute(
        "SELECT COUNT(*) FROM audience_members"
    ).fetchone()[0]
    assert count == 50000


def test_experiment_results_count(connection):
    count = connection.execute(
        "SELECT COUNT(*) FROM experiment_results"
    ).fetchone()[0]
    assert count == 10


def test_state_event_count(connection):
    count = connection.execute(
        "SELECT COUNT(*) FROM experiment_state_events"
    ).fetchone()[0]
    assert count == 30


def test_primary_keys_are_unique(connection):
    for table in EXPECTED_TABLES:
        primary_keys = [
            row[1]
            for row in connection.execute(
                f"PRAGMA table_info({table})"
            )
            if row[5] > 0
        ]

        assert primary_keys

        for column in primary_keys:
            total, distinct = connection.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT {column}) FROM {table}"
            ).fetchone()

            assert total == distinct, f"Duplicate key in {table}.{column}"


def test_foreign_key_integrity(connection):
    violations = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()
    assert violations == []


def test_validation_summary_passed():
    import json

    summary_path = ROOT / "outputs" / "validation_summary.json"

    with open(summary_path, encoding="utf-8") as file:
        summary = json.load(file)

    assert summary["status"] == "PASSED"
    assert all(summary["checks"].values())
