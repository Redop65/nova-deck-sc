from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def clean_test_backups():
    yield
    directory = Path(__file__).parent / "backups"
    if directory.exists():
        for item in directory.iterdir():
            item.unlink(missing_ok=True)
        directory.rmdir()
