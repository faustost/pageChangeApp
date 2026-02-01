import json
import pytest
from src import storage

class TestStorage:
    def test_load_snapshots_empty(self, temp_env):
        # File doesn't exist yet
        data = storage.load_snapshots()
        assert data == {"pages": {}}

    def test_save_and_load(self, temp_env):
        data = {"pages": {"1": {"test": "data"}}}
        storage.save_snapshots(data)
        
        loaded = storage.load_snapshots()
        assert loaded == data

    def test_save_page_snapshot_new(self, temp_env):
        # Need to mock load_pages to avoid FileNotFoundError for pages.json
        # The code in storage.save_page_snapshot calls load_pages() for settings
        with open(temp_env["pages_file"], "w") as f:
            json.dump({"settings": {}}, f)
            
        storage.save_page_snapshot("p1", "content", "hash123")
        
        snapshots = storage.load_snapshots()
        page = snapshots["pages"]["p1"]
        assert page["current_hash"] == "hash123"
        assert page["current_content"] == "content"
        assert len(page["history"]) == 0

    def test_save_page_snapshot_update_history(self, temp_env):
        with open(temp_env["pages_file"], "w") as f:
            json.dump({"settings": {"max_history_per_page": 2}}, f)
            
        # Initial
        storage.save_page_snapshot("p1", "old", "hash1")
        
        # Update with change
        storage.save_page_snapshot("p1", "new", "hash2", diff="diff", changed=True)
        
        snapshots = storage.load_snapshots()
        hist = snapshots["pages"]["p1"]["history"]
        assert len(hist) == 1
        assert hist[0]["new_hash"] == "hash2"
        
        # Another change
        storage.save_page_snapshot("p1", "newer", "hash3", diff="diff2", changed=True)
        snapshots = storage.load_snapshots()
        hist = snapshots["pages"]["p1"]["history"]
        assert len(hist) == 2
        assert hist[0]["new_hash"] == "hash3"
        
        # Overflow history (max 2)
        storage.save_page_snapshot("p1", "newest", "hash4", diff="diff3", changed=True)
        snapshots = storage.load_snapshots()
        hist = snapshots["pages"]["p1"]["history"]
        assert len(hist) == 2
        assert hist[0]["new_hash"] == "hash4"
        # Oldest should be gone
        assert hist[-1]["new_hash"] == "hash3"

    def test_meta_timestamps(self, temp_env):
        assert storage.get_last_no_changes_ts() is None
        
        storage.set_last_no_changes_ts()
        ts = storage.get_last_no_changes_ts()
        assert ts is not None
        assert isinstance(ts, str)
