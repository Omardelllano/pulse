"""Tests for NewsFetcher (httpx mocked — no real network calls)."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from pulso.news.fetcher import (
    NewsFetcher, _parse_rss, _deduplicate, NewsItem,
    MAX_ITEMS_TOTAL, MAX_PER_FEED,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────

RSS_4_ITEMS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Sismo en CDMX</title>
      <link>https://example.com/1</link>
      <pubDate>Wed, 01 Jan 2025 12:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Dolar sube</title>
      <link>https://example.com/2</link>
      <pubDate>Wed, 01 Jan 2025 11:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Elecciones en Jalisco</title>
      <link>https://example.com/3</link>
      <pubDate>Wed, 01 Jan 2025 10:00:00 +0000</pubDate>
    </item>
    <item>
      <title>Cuarta noticia extra</title>
      <link>https://example.com/4</link>
      <pubDate>Wed, 01 Jan 2025 09:00:00 +0000</pubDate>
    </item>
  </channel>
</rss>"""

ATOM_SAMPLE = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Test</title>
  <entry>
    <title>Noticia Atom 1</title>
    <link href="https://example.com/a1"/>
    <updated>2025-01-01T12:00:00Z</updated>
  </entry>
  <entry>
    <title>Noticia Atom 2</title>
    <link href="https://example.com/a2"/>
    <updated>2025-01-01T11:00:00Z</updated>
  </entry>
</feed>"""

ATOM_PUBLISHED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>Atom con published</title>
    <link href="https://example.com/p1"/>
    <published>2025-06-15T09:00:00Z</published>
  </entry>
</feed>"""

CDATA_SAMPLE = b"""<rss version="2.0"><channel>
  <item>
    <title><![CDATA[Titular envuelto en marcador & caracteres especiales]]></title>
    <link>https://x.com/1</link>
    <pubDate>Wed, 01 Jan 2025 10:00:00 +0000</pubDate>
  </item>
</channel></rss>"""

RSS_2_ITEMS = b"""<rss version="2.0"><channel>
  <item><title>Noticia 1</title><link>https://x.com/1</link>
        <pubDate>Wed, 01 Jan 2025 12:00:00 +0000</pubDate></item>
  <item><title>Noticia 2</title><link>https://x.com/2</link>
        <pubDate>Wed, 01 Jan 2025 11:00:00 +0000</pubDate></item>
</channel></rss>"""


def _mock_resp(content: bytes = RSS_2_ITEMS, status_code: int = 200):
    """Build a MagicMock that looks like an httpx Response."""
    resp = MagicMock()
    resp.content = content
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
    return resp


# ── _parse_rss ─────────────────────────────────────────────────────────────────

class TestParseRss:
    def test_parses_rss_all_items_up_to_per_feed_cap(self):
        items = _parse_rss(RSS_4_ITEMS, "Test")
        # All 4 items fit within MAX_PER_FEED=6
        assert len(items) == 4

    def test_rss_item_has_headline(self):
        items = _parse_rss(RSS_4_ITEMS, "Test")
        assert items[0].headline == "Sismo en CDMX"

    def test_rss_item_has_source(self):
        items = _parse_rss(RSS_4_ITEMS, "El Universal")
        assert all(i.source == "El Universal" for i in items)

    def test_rss_item_has_url(self):
        items = _parse_rss(RSS_4_ITEMS, "Test")
        assert items[0].url == "https://example.com/1"

    def test_rss_item_has_timestamp(self):
        items = _parse_rss(RSS_4_ITEMS, "Test")
        assert isinstance(items[0].timestamp, datetime)

    def test_parses_atom_feed(self):
        items = _parse_rss(ATOM_SAMPLE, "Atom")
        assert len(items) == 2
        assert items[0].headline == "Noticia Atom 1"

    def test_atom_uses_published_date(self):
        items = _parse_rss(ATOM_PUBLISHED, "Atom")
        assert len(items) == 1
        # published date should be parsed correctly
        assert items[0].timestamp.year == 2025

    def test_cdata_title_stripped(self):
        items = _parse_rss(CDATA_SAMPLE, "Test")
        assert len(items) == 1
        # ET strips CDATA markers; raw text should be present
        assert "Titular envuelto" in items[0].headline
        # CDATA syntax markers should not appear
        assert "<![CDATA[" not in items[0].headline

    def test_returns_empty_on_invalid_xml(self):
        items = _parse_rss(b"not xml at all <<<", "Bad")
        assert items == []

    def test_returns_empty_on_empty_bytes(self):
        items = _parse_rss(b"", "Empty")
        assert items == []

    def test_skips_items_without_title(self):
        xml = b"<rss><channel><item><link>https://x.com</link></item></channel></rss>"
        items = _parse_rss(xml, "Test")
        assert items == []

    def test_per_feed_cap_respected(self):
        # Build 10 items — should be capped at MAX_PER_FEED
        items_xml = "".join(
            f"<item><title>Noticia {i}</title><link>https://x.com/{i}</link>"
            f"<pubDate>Wed, 01 Jan 2025 12:0{i:01d}:00 +0000</pubDate></item>"
            for i in range(10)
        )
        xml = f"<rss><channel>{items_xml}</channel></rss>".encode()
        items = _parse_rss(xml, "Test")
        assert len(items) <= MAX_PER_FEED


# ── _deduplicate ───────────────────────────────────────────────────────────────

class TestDeduplicate:
    def _item(self, headline: str) -> NewsItem:
        return NewsItem(headline=headline, source="X", url="", timestamp=datetime.utcnow())

    def test_identical_headlines_deduplicated(self):
        items = [self._item("Sismo en CDMX sacude la capital"), self._item("Sismo en CDMX sacude la capital")]
        result = _deduplicate(items)
        assert len(result) == 1

    def test_similar_headlines_deduplicated(self):
        # 80% word overlap — should be considered duplicate
        items = [
            self._item("Sismo de magnitud 5 sacude la Ciudad de Mexico"),
            self._item("Sismo de magnitud 5 sacude Ciudad de Mexico hoy"),
        ]
        result = _deduplicate(items)
        assert len(result) == 1

    def test_different_headlines_kept(self):
        items = [
            self._item("Sismo en Oaxaca deja danos materiales"),
            self._item("Dolar sube ante incertidumbre economica"),
        ]
        result = _deduplicate(items)
        assert len(result) == 2

    def test_empty_list_returns_empty(self):
        assert _deduplicate([]) == []

    def test_keeps_first_occurrence(self):
        items = [self._item("Mexico gana el mundial"), self._item("Mexico gana el mundial de futbol")]
        result = _deduplicate(items)
        assert result[0].headline == "Mexico gana el mundial"


# ── NewsFetcher ────────────────────────────────────────────────────────────────

class TestNewsFetcher:
    @pytest.mark.asyncio
    async def test_fetch_returns_list(self):
        fetcher = NewsFetcher()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=_mock_resp(RSS_2_ITEMS))
        with patch("pulso.news.fetcher.httpx.AsyncClient", return_value=mock_client):
            items = await fetcher.fetch()
        assert isinstance(items, list)

    @pytest.mark.asyncio
    async def test_fetch_caps_at_max_items(self):
        fetcher = NewsFetcher()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=_mock_resp(RSS_2_ITEMS))
        with patch("pulso.news.fetcher.httpx.AsyncClient", return_value=mock_client):
            items = await fetcher.fetch()
        assert len(items) <= MAX_ITEMS_TOTAL

    @pytest.mark.asyncio
    async def test_fetch_never_raises_on_network_error(self):
        fetcher = NewsFetcher()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(side_effect=Exception("connection refused"))
        with patch("pulso.news.fetcher.httpx.AsyncClient", return_value=mock_client):
            items = await fetcher.fetch()  # must not raise
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_returns_news_items(self):
        fetcher = NewsFetcher()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=_mock_resp(RSS_2_ITEMS))
        with patch("pulso.news.fetcher.httpx.AsyncClient", return_value=mock_client):
            items = await fetcher.fetch()
        for item in items:
            assert isinstance(item, NewsItem)
            assert item.headline
            assert item.source

    @pytest.mark.asyncio
    async def test_fetch_one_returns_empty_on_http_error(self):
        fetcher = NewsFetcher()
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=_mock_resp(b"", 500))
        with patch("pulso.news.fetcher.httpx.AsyncClient", return_value=mock_client):
            items = await fetcher._fetch_one("Test", "https://example.com/rss")
        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_deduplicates_across_sources(self):
        """Same headline from two different feeds should appear only once."""
        fetcher = NewsFetcher()
        duplicate_rss = b"""<rss><channel>
          <item><title>Sismo en la Ciudad de Mexico sacude la capital</title>
                <link>https://a.com/1</link>
                <pubDate>Wed, 01 Jan 2025 12:00:00 +0000</pubDate></item>
          <item><title>Sismo en Ciudad de Mexico sacude la capital hoy</title>
                <link>https://b.com/1</link>
                <pubDate>Wed, 01 Jan 2025 11:00:00 +0000</pubDate></item>
        </channel></rss>"""
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=_mock_resp(duplicate_rss))
        with patch("pulso.news.fetcher.httpx.AsyncClient", return_value=mock_client):
            items = await fetcher.fetch()
        # Despite 10 feeds × 2 items, duplicates collapsed to 1
        unique_stories = {i.headline for i in items}
        assert len(unique_stories) == 1
