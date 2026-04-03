"""
News fetcher: pulls headlines from Mexican RSS feeds using httpx + xml parsing.
Stores the latest 30 headlines in memory — no DB.
Updates every PULSO_NEWS_FETCH_INTERVAL_MINUTES (default: 3).

Handles:
- RSS 2.0 (<item>) and Atom (<entry>) formats
- CDATA-wrapped titles (stripped automatically by ElementTree)
- <published> and <updated> Atom date fields
- <link> as text node (RSS 2.0) or href attribute (Atom)
- UTF-8 and latin-1 encoded feeds
- Deduplication by headline similarity (≥70% word overlap)
"""
import asyncio
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

RSS_FEEDS = [
    ("El Universal",        "https://www.eluniversal.com.mx/rss.xml"),
    ("Proceso",             "https://www.proceso.com.mx/rss"),
    ("Milenio",             "https://www.milenio.com/rss"),
    ("Animal Político",     "https://www.animalpolitico.com/feed"),
    ("Reforma",             "https://www.reforma.com/rss/portada.xml"),
    ("Aristegui Noticias",  "https://aristeguinoticias.com/feed/"),
    ("Infobae México",      "https://www.infobae.com/mexico/rss/"),
    ("El Financiero",       "https://www.elfinanciero.com.mx/arc/outboundfeeds/rss/"),
    ("Forbes México",       "https://www.forbes.com.mx/feed/"),
    ("Sin Embargo",         "https://www.sinembargo.mx/feed/"),
]

MAX_ITEMS_TOTAL = 30
MAX_PER_FEED = 6
FETCH_TIMEOUT_SECONDS = 5.0

# Atom namespace
_ATOM_NS = {"a": "http://www.w3.org/2005/Atom"}


@dataclass
class NewsItem:
    headline: str
    source: str
    url: str
    timestamp: datetime
    sentiment: Optional[dict] = None  # filled later by processor


# ── XML helpers ────────────────────────────────────────────────────────────────

def _strip_cdata(text: str) -> str:
    """Strip any residual CDATA markers that ET didn't handle."""
    return re.sub(r"<!\[CDATA\[(.*?)]]>", r"\1", text, flags=re.DOTALL).strip()


def _text(el, tag: str, default: str = "") -> str:
    """Get text of a child element, stripping CDATA and whitespace."""
    child = el.find(tag)
    if child is None:
        return default
    return _strip_cdata(child.text or "").strip()


def _parse_datetime(raw: str) -> datetime:
    """Parse RFC 2822 or ISO 8601 datetime, falling back to utcnow."""
    raw = raw.strip()
    if not raw:
        return datetime.utcnow()
    # Try RFC 2822 (pubDate in RSS 2.0)
    try:
        ts = parsedate_to_datetime(raw)
        return ts.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        pass
    # Try ISO 8601 (Atom)
    try:
        return datetime.fromisoformat(raw.rstrip("Z"))
    except Exception:
        pass
    return datetime.utcnow()


def _parse_rss(xml_bytes: bytes, source_name: str) -> list[NewsItem]:
    """
    Parse raw RSS/Atom bytes and return up to MAX_PER_FEED NewsItems.
    Tries UTF-8 first, then latin-1 as fallback.
    """
    # Decode bytes — try UTF-8 then latin-1
    for enc in ("utf-8", "latin-1"):
        try:
            xml_text = xml_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        xml_text = xml_bytes.decode("utf-8", errors="replace")

    # Strip XML declaration if encoding attr would confuse ET
    xml_text = re.sub(r"<\?xml[^?]*\?>", "", xml_text, count=1).strip()

    items: list[NewsItem] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        logger.debug("[NewsFetcher] XML parse error for %s: %s", source_name, exc)
        return items

    # ── RSS 2.0: <item> elements ─────────────────────────────────────────────
    for item_el in root.findall(".//item"):
        if len(items) >= MAX_PER_FEED:
            break
        title = _text(item_el, "title")
        if not title:
            continue
        link = _text(item_el, "link")
        # Some RSS 2.0 feeds put link as element text OR as <link> tail
        if not link:
            link_el = item_el.find("link")
            if link_el is not None:
                link = (link_el.tail or "").strip() or (link_el.text or "").strip()
        pub_date = _text(item_el, "pubDate") or _text(item_el, "dc:date")
        ts = _parse_datetime(pub_date)
        items.append(NewsItem(headline=title, source=source_name, url=link, timestamp=ts))

    if items:
        return items

    # ── Atom: <entry> elements ───────────────────────────────────────────────
    # Try both namespaced and bare <entry>
    entries = root.findall(".//a:entry", _ATOM_NS)
    if not entries:
        entries = root.findall(".//entry")
    for entry_el in entries:
        if len(items) >= MAX_PER_FEED:
            break

        # Title — try namespaced then bare
        title_el = entry_el.find("a:title", _ATOM_NS)
        if title_el is None:
            title_el = entry_el.find("title")
        title = _strip_cdata((title_el.text or "") if title_el is not None else "").strip()
        if not title:
            continue

        # Link — <link href="..."> or <link>text</link>
        link = ""
        link_el = entry_el.find("a:link", _ATOM_NS)
        if link_el is None:
            link_el = entry_el.find("link")
        if link_el is not None:
            link = link_el.get("href", "") or _strip_cdata(link_el.text or "").strip()

        # Date — prefer <published>, fall back to <updated>
        pub_el = entry_el.find("a:published", _ATOM_NS)
        if pub_el is None:
            pub_el = entry_el.find("published")
        if pub_el is None:
            pub_el = entry_el.find("a:updated", _ATOM_NS)
        if pub_el is None:
            pub_el = entry_el.find("updated")
        raw_date = _strip_cdata((pub_el.text or "") if pub_el is not None else "")
        ts = _parse_datetime(raw_date)

        items.append(NewsItem(headline=title, source=source_name, url=link, timestamp=ts))

    return items


# ── Deduplication ──────────────────────────────────────────────────────────────

def _word_set(headline: str) -> set[str]:
    """Lowercase word set for similarity comparison."""
    return set(re.findall(r"[a-záéíóúüñ]+", headline.lower()))


def _deduplicate(items: list[NewsItem]) -> list[NewsItem]:
    """
    Remove duplicate headlines: two items are duplicates if ≥70% of the
    words in the shorter headline also appear in the longer one.
    Keeps the first occurrence (newest-first after sorting).
    """
    result: list[NewsItem] = []
    for item in items:
        ws = _word_set(item.headline)
        is_dup = False
        for existing in result:
            ew = _word_set(existing.headline)
            shorter = min(len(ws), len(ew))
            if shorter == 0:
                continue
            overlap = len(ws & ew) / shorter
            if overlap >= 0.70:
                is_dup = True
                break
        if not is_dup:
            result.append(item)
    return result


# ── Fetcher class ──────────────────────────────────────────────────────────────

class NewsFetcher:
    """
    Fetches headlines from 10 Mexican RSS feeds concurrently.
    Returns up to MAX_ITEMS_TOTAL deduplicated items, sorted newest-first.
    Never raises.
    """

    async def fetch(self) -> list[NewsItem]:
        tasks = [self._fetch_one(name, url) for name, url in RSS_FEEDS]
        results = await asyncio.gather(*tasks)
        all_items: list[NewsItem] = []
        for batch in results:
            all_items.extend(batch)

        all_items.sort(key=lambda x: x.timestamp, reverse=True)
        all_items = _deduplicate(all_items)
        return all_items[:MAX_ITEMS_TOTAL]

    async def _fetch_one(self, name: str, url: str) -> list[NewsItem]:
        """Fetch one RSS feed. Returns empty list on any error."""
        try:
            async with httpx.AsyncClient(
                timeout=FETCH_TIMEOUT_SECONDS,
                follow_redirects=True,
            ) as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "PULSO/2.0 (+https://pulso.mx)"},
                )
                resp.raise_for_status()
                return _parse_rss(resp.content, name)
        except Exception as exc:
            logger.debug("[NewsFetcher] Failed to fetch %s: %s", name, exc)
            return []
