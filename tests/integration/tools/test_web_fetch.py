"""Tests for the web_fetch tool."""

import pytest

from tunacode.exceptions import ToolRetryError

from tunacode.tools.web_fetch import (
    _convert_html_to_text,
    _is_private_ip,
    _truncate_output,
    _validate_url,
)


class TestValidateUrl:
    """Tests for URL validation security."""

    def test_blocks_localhost(self):
        """Should block localhost URLs."""
        with pytest.raises(ToolRetryError, match="Cannot fetch from localhost"):
            _validate_url("http://localhost/")

    def test_blocks_localhost_with_port(self):
        """Should block localhost with port."""
        with pytest.raises(ToolRetryError, match="Cannot fetch from localhost"):
            _validate_url("http://localhost:8080/")

    def test_blocks_127_0_0_1(self):
        """Should block 127.0.0.1."""
        with pytest.raises(ToolRetryError, match="Cannot fetch from localhost"):
            _validate_url("http://127.0.0.1/")

    def test_blocks_private_ip_10(self):
        """Should block 10.x.x.x addresses."""
        with pytest.raises(ToolRetryError, match="private or reserved"):
            _validate_url("http://10.0.0.1/")

    def test_blocks_private_ip_192_168(self):
        """Should block 192.168.x.x addresses."""
        with pytest.raises(ToolRetryError, match="private or reserved"):
            _validate_url("http://192.168.1.1/")

    def test_blocks_private_ip_172(self):
        """Should block 172.16-31.x.x addresses."""
        with pytest.raises(ToolRetryError, match="private or reserved"):
            _validate_url("http://172.16.0.1/")

    def test_blocks_file_scheme(self):
        """Should block file:// URLs."""
        with pytest.raises(ToolRetryError, match="Invalid URL scheme"):
            _validate_url("file:///etc/passwd")

    def test_blocks_ftp_scheme(self):
        """Should block ftp:// URLs."""
        with pytest.raises(ToolRetryError, match="Invalid URL scheme"):
            _validate_url("ftp://example.com/")

    def test_allows_http(self):
        """Should allow http:// URLs."""
        result = _validate_url("http://example.com/")
        assert result == "http://example.com/"

    def test_allows_https(self):
        """Should allow https:// URLs."""
        result = _validate_url("https://example.com/")
        assert result == "https://example.com/"

    def test_blocks_empty_url(self):
        """Should block empty URLs."""
        with pytest.raises(ToolRetryError, match="cannot be empty"):
            _validate_url("")

    def test_blocks_missing_hostname(self):
        """Should block URLs without hostname."""
        with pytest.raises(ToolRetryError, match="missing hostname"):
            _validate_url("http:///path")


class TestIsPrivateIp:
    """Tests for private IP detection."""

    def test_127_is_private(self):
        """127.x.x.x should be private."""
        assert _is_private_ip("127.0.0.1") is True
        assert _is_private_ip("127.255.255.255") is True

    def test_10_is_private(self):
        """10.x.x.x should be private."""
        assert _is_private_ip("10.0.0.1") is True
        assert _is_private_ip("10.255.255.255") is True

    def test_172_16_to_31_is_private(self):
        """172.16-31.x.x should be private."""
        assert _is_private_ip("172.16.0.1") is True
        assert _is_private_ip("172.31.255.255") is True
        assert _is_private_ip("172.15.0.1") is False
        assert _is_private_ip("172.32.0.1") is False

    def test_192_168_is_private(self):
        """192.168.x.x should be private."""
        assert _is_private_ip("192.168.0.1") is True
        assert _is_private_ip("192.168.255.255") is True

    def test_public_ip_not_private(self):
        """Public IPs should not be private."""
        assert _is_private_ip("8.8.8.8") is False
        assert _is_private_ip("93.184.216.34") is False


class TestConvertHtmlToText:
    """Tests for HTML to text conversion."""

    def test_converts_simple_html(self):
        """Should convert simple HTML to text."""
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        result = _convert_html_to_text(html)
        assert "Hello" in result
        assert "World" in result

    def test_preserves_links(self):
        """Should preserve link URLs."""
        html = '<a href="https://example.com">Link</a>'
        result = _convert_html_to_text(html)
        assert "example.com" in result or "Link" in result


class TestTruncateOutput:
    """Tests for output truncation."""

    def test_no_truncation_for_small_content(self):
        """Should not truncate small content."""
        content = "Small content"
        result = _truncate_output(content, max_size=1000)
        assert result == content
        assert "[truncated]" not in result

    def test_truncates_large_content(self):
        """Should truncate large content."""
        content = "x" * 10000
        result = _truncate_output(content, max_size=1000)
        assert len(result) < len(content)
        assert "truncated" in result.lower()
