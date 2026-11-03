import os
import sys

# Must be set before app.py is imported: it calls init_db() on import.
os.environ.setdefault("WORLDBANK_DB", ":memory:")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

import database as db  # noqa: E402
from app import app  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Test client backed by a fresh temporary database for every test."""
    monkeypatch.setattr(db, "DB_NAME", str(tmp_path / "test.db"))
    db.init_db()
    app.config["TESTING"] = True
    return app.test_client()