import pytest
from unittest.mock import MagicMock, patch
from src import monitor

class TestFetchPage:
    def test_fetch_success(self):
        with patch("src.monitor.requests.get") as mock_get:
            mock_get.return_value.text = "<html><body>Hello</body></html>"
            mock_get.return_value.status_code = 200
            
            content = monitor.fetch_page("http://example.com")
            assert content == "<html><body>Hello</body></html>"
            mock_get.assert_called_once()

    def test_fetch_retry_failure(self):
        with patch("src.monitor.requests.get") as mock_get:
            # Simulate exception
            from requests.exceptions import RequestException
            mock_get.side_effect = RequestException("Error")
            
            # Reduce delays for test
            with patch("src.monitor.RETRY_DELAY", 0):
                content = monitor.fetch_page("http://example.com")
            
            assert content is None
            # Should match MAX_RETRIES (3)
            assert mock_get.call_count == 3

class TestExtractText:
    def test_extract_simple(self):
        html = "<html><body><p>Hello World</p></body></html>"
        text = monitor.extract_text(html)
        assert text == "Hello World"

    def test_remove_noise_tags(self):
        html = """
        <html>
            <body>
                <header>Menu</header>
                <div class="content">Real Content</div>
                <footer>Copyright</footer>
                <script>var x=1;</script>
            </body>
        </html>
        """
        text = monitor.extract_text(html)
        assert "Menu" not in text
        assert "Copyright" not in text
        assert "var x=1" not in text
        assert "Real Content" in text

    def test_selector(self):
        html = """
        <html>
            <body>
                <div id="ignore">Bad</div>
                <div id="keep">Good</div>
            </body>
        </html>
        """
        text = monitor.extract_text(html, selector="#keep")
        assert text == "Good"

    def test_selector_not_found(self):
        html = "<body><div>Content</div></body>"
        # If selector not found, it might fall back to full body or return empty depending on logic.
        # Code says: if target: soup = target. So if not found, it keeps original soup.
        text = monitor.extract_text(html, selector="#nonexistent")
        assert text == "Content"

    def test_remove_noise_patterns(self):
        html = "<div>Content 12/12/2023 10:00 sessionid=123</div>"
        text = monitor.extract_text(html)
        # Dates and sessionids should be removed
        assert "Content" in text
        assert "sessionid" not in text
        assert "2023" not in text  # Rough check, regex dependent

class TestCheckPage:
    def test_first_run(self):
        with patch("src.monitor.fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html>Content</html>"
            
            config = {"url": "http://test.com"}
            result = monitor.check_page(config, previous_content=None)
            
            assert result["first_run"] is True
            assert result["content"] == "Content"
            assert result["changed"] is False
            assert result["hash"] is not None

    def test_no_change(self):
        with patch("src.monitor.fetch_page") as mock_fetch:
            content = "Content"
            mock_fetch.return_value = f"<html>{content}</html>"
            
            config = {"url": "http://test.com"}
            # Need a valid hash for previous
            prev_hash = monitor.compute_hash(content)
            
            result = monitor.check_page(config, previous_content=content, previous_hash=prev_hash)
            
            assert result["changed"] is False
            assert result["diff"] is None

    def test_change_detected(self):
        with patch("src.monitor.fetch_page") as mock_fetch:
            mock_fetch.return_value = "<html>New Content</html>"
            
            config = {"url": "http://test.com"}
            prev_content = "Old Content"
            
            result = monitor.check_page(config, previous_content=prev_content)
            
            assert result["changed"] is True
            assert result["diff"] is not None
            assert "-Old Content" in result["diff"]
            assert "+New Content" in result["diff"]
