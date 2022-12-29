import pytest
from sqlite_utils.db import Database


@pytest.fixture
def mock_db() -> Database:
    db = Database(memory=True)
    return db
