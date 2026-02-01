import os
import json
import pytest
from src import config

class TestConfig:
    def test_load_pages(self, temp_env):
        data = {"pages": []}
        with open(temp_env["pages_file"], "w") as f:
            json.dump(data, f)
            
        assert config.load_pages() == data

    def test_get_telegram_token_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env_token")
        assert config.get_telegram_token() == "env_token"

    def test_get_telegram_chat_id_env(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "env_id")
        assert config.get_telegram_chat_id() == "env_id"

    def test_get_telegram_chat_id_config(self, monkeypatch, temp_env):
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        
        with open(temp_env["pages_file"], "w") as f:
            json.dump({"settings": {"telegram_chat_id": "conf_id"}}, f)
            
        assert config.get_telegram_chat_id() == "conf_id"
