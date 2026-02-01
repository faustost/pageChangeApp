import sys
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def mock_response():
    """Helper to create a mock response."""
    def _create(text="content", status_code=200, raise_for_status=None):
        mock = MagicMock()
        mock.text = text
        mock.status_code = status_code
        if raise_for_status:
            mock.raise_for_status.side_effect = raise_for_status
        return mock
    return _create

@pytest.fixture
def temp_env(tmp_path, monkeypatch):
    """Fixture to set up temporary data directory and redirect config paths."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pages_file = data_dir / "pages.json"
    snapshots_file = data_dir / "snapshots.json"
    
    # Update the module-level constants in src.config and src.storage
    monkeypatch.setattr("src.config.PAGES_FILE", pages_file)
    monkeypatch.setattr("src.config.SNAPSHOTS_FILE", snapshots_file)
    monkeypatch.setattr("src.storage.SNAPSHOTS_FILE", snapshots_file)
    
    return {
        "root": tmp_path,
        "pages_file": pages_file,
        "snapshots_file": snapshots_file
    }