import pytest
from unittest.mock import patch
from src import notify

class TestNotify:
    def test_escape_markdown(self):
        raw = "Hello_World [Link]!"
        escaped = notify.escape_markdown(raw)
        assert "\\" in escaped
        assert r"\_" in escaped
        assert r"\[" in escaped
        assert r"\!" in escaped
        # Verify it doesn't double escape if we were to run it? No, simple replace.
        
    def test_format_telegram_message_first_run(self):
        msg = notify.format_telegram_message("Name", "http://url", None, first_run=True)
        assert "New page added" in msg
        assert "Name" in msg
        assert "http://url" in msg

    def test_format_telegram_message_change(self):
        msg = notify.format_telegram_message("Name", "http://url", "The Diff")
        assert "Page changed" in msg
        assert "The Diff" in msg

    def test_send_telegram_success(self):
        with patch("src.notify.get_telegram_token", return_value="tok"), \
             patch("src.notify.get_telegram_chat_id", return_value="123"), \
             patch("src.notify.requests.post") as mock_post:
            
            mock_post.return_value.status_code = 200
            
            success = notify.send_telegram("Message")
            assert success is True
            mock_post.assert_called_once()
            
    def test_send_telegram_missing_config(self):
        with patch("src.notify.get_telegram_token", return_value=""), \
             patch("src.notify.get_telegram_chat_id", return_value=""):
            
            success = notify.send_telegram("Message")
            assert success is False

    def test_notify_failure(self):
        with patch("src.notify.send_telegram") as mock_send:
            notify.notify_failure(["Page 1", "Page 2"])
            mock_send.assert_called_once()
            args = mock_send.call_args[0][0]
            assert "Page 1" in args
            assert "Page 2" in args
