/**
 * NewsFeed — live news sidebar with rotating ticker effect.
 *
 * Features:
 *  - Renders headlines with sentiment dot, source · time-ago meta
 *  - Ticker: scrolls up one item every 12 seconds (smooth easing)
 *  - Hover: pauses ticker; resumes 2 s after mouse leaves
 *  - New headlines: highlighted with a 3 s glow on arrival
 *  - Relative times refresh every 60 s without re-fetching
 *  - Polls /api/news every 3 min (or custom interval)
 */
class NewsFeed {
  /** @param {HTMLElement} container — the #news-list element */
  constructor(container) {
    this.container   = container;
    this._items      = [];       // master item array (most recent first)
    this._paused     = false;    // true while mouse is over sidebar
    this._resumeId   = null;     // setTimeout for 2-s resume delay
    this._tickerId   = null;     // setInterval for 12-s ticker
    this._pollId     = null;     // setInterval for 3-min data refresh
    this._timeId     = null;     // setInterval for 1-min relative-time refresh

    this._setupHoverPause();
  }

  /* ── Emotion → CSS color ─────────────────────────────────────────────────── */

  static EMOTION_COLORS = {
    anger:   'rgb(226, 75, 74)',
    joy:     'rgb(239, 175, 50)',
    fear:    'rgb(140, 130, 235)',
    hope:    'rgb(40, 180, 130)',
    sadness: 'rgb(70, 150, 230)',
  };
  static DEFAULT_COLOR = 'rgba(255,255,255,0.18)';

  /* ── Public API ──────────────────────────────────────────────────────────── */

  /**
   * Replace the visible list with new items.
   * Detects which headlines are genuinely new (not in the previous list) and
   * briefly highlights them.
   * @param {Array} items   — array of item objects from /api/news
   */
  render(items) {
    if (!items || items.length === 0) {
      if (this._items.length === 0 && this.container) {
        this.container.innerHTML = '<div class="news-empty">Sin noticias recientes</div>';
      }
      return;
    }

    const prevHeadlines = new Set(this._items.map(i => i.headline));
    this._items = items;

    if (!this.container) return;

    // Build DOM
    this.container.innerHTML = items.map(item => {
      const isNew = !prevHeadlines.has(item.headline) && prevHeadlines.size > 0;
      return this._buildItemHTML(item, isNew);
    }).join('');

    // Schedule glow removal for new items
    const newEls = this.container.querySelectorAll('.news-item--new');
    if (newEls.length) {
      setTimeout(() => {
        newEls.forEach(el => el.classList.remove('news-item--new'));
      }, 3000);
    }
  }

  /**
   * Start polling + ticker.
   * @param {object} apiClient — has .getNews() method
   * @param {number} intervalMs — how often to re-fetch (ms)
   */
  startPolling(apiClient, intervalMs) {
    const fetch = () => {
      apiClient.getNews()
        .then(data => this.render(data.items || []))
        .catch(() => { /* silent — keep stale list */ });
    };

    fetch();  // immediate first fetch
    this._pollId   = setInterval(fetch, intervalMs);
    this._tickerId = setInterval(() => this._tick(), 12000);
    this._timeId   = setInterval(() => this._refreshTimes(), 60000);
  }

  stopPolling() {
    [this._pollId, this._tickerId, this._timeId].forEach(id => clearInterval(id));
    this._pollId = this._tickerId = this._timeId = null;
    if (this._resumeId) { clearTimeout(this._resumeId); this._resumeId = null; }
  }

  /* ── Private: item HTML ──────────────────────────────────────────────────── */

  _buildItemHTML(item, isNew) {
    const emotion  = item.sentiment && item.sentiment.emotion ? item.sentiment.emotion : null;
    const dotColor = emotion
      ? (NewsFeed.EMOTION_COLORS[emotion] || NewsFeed.DEFAULT_COLOR)
      : NewsFeed.DEFAULT_COLOR;

    const href   = item.url || '#';
    const target = item.url ? ' target="_blank" rel="noopener noreferrer"' : '';
    const source = item.source ? _escapeHtml(item.source) : '';
    const ts     = item.timestamp || '';
    const timeStr = ts ? _timeAgo(ts) : '';
    // Combined "Source · hace N min"
    const meta = [source, timeStr].filter(Boolean).join(' · ');

    const newClass = isNew ? ' news-item--new' : '';
    return `<div class="news-item${newClass}">` +
      `<span class="news-dot" style="background:${dotColor}"></span>` +
      `<div class="news-content">` +
        `<a class="news-headline" href="${href}"${target}>${_escapeHtml(item.headline)}</a>` +
        (meta ? `<span class="news-meta" data-ts="${_escapeHtml(ts)}">${_escapeHtml(meta)}</span>` : '') +
      `</div>` +
    `</div>`;
  }

  /* ── Private: ticker ─────────────────────────────────────────────────────── */

  /**
   * Scroll the list up by one item height every tick.
   * When the last item is reached, instantly jump back to top.
   */
  _tick() {
    if (this._paused || !this.container) return;
    const el = this.container;
    const firstItem = el.querySelector('.news-item');
    if (!firstItem || el.scrollHeight <= el.clientHeight) return;  // nothing to scroll

    const itemH = firstItem.offsetHeight;
    const maxScroll = el.scrollHeight - el.clientHeight;

    if (el.scrollTop + itemH >= maxScroll - 1) {
      // Near the bottom — snap back to top, no animation
      el.scrollTop = 0;
    } else {
      _smoothScroll(el, el.scrollTop + itemH, 500);
    }
  }

  /* ── Private: hover pause ────────────────────────────────────────────────── */

  _setupHoverPause() {
    if (!this.container) return;

    this.container.addEventListener('mouseenter', () => {
      this._paused = true;
      if (this._resumeId) { clearTimeout(this._resumeId); this._resumeId = null; }
    });

    this.container.addEventListener('mouseleave', () => {
      this._resumeId = setTimeout(() => {
        this._paused = false;
        this._resumeId = null;
      }, 2000);
    });
  }

  /* ── Private: time refresh ───────────────────────────────────────────────── */

  /**
   * Update all .news-meta elements' time part every minute using data-ts.
   */
  _refreshTimes() {
    if (!this.container) return;
    this.container.querySelectorAll('.news-meta[data-ts]').forEach(el => {
      const ts      = el.dataset.ts;
      const source  = el.dataset.source || '';
      const timeStr = ts ? _timeAgo(ts) : '';
      const meta    = [source, timeStr].filter(Boolean).join(' · ');
      // Rebuild text preserving the same data attribute
      if (meta) el.textContent = meta;
    });
  }
}

/* ── Sidebar toggle ──────────────────────────────────────────────────────────── */

/**
 * Wire up the sidebar toggle button.
 * @param {HTMLElement} toggleBtn
 */
function initNewsSidebarToggle(toggleBtn) {
  if (!toggleBtn) return;

  function _apply(open) {
    if (open) {
      document.body.classList.add('sidebar-open');
      toggleBtn.setAttribute('aria-label', 'Cerrar noticias');
      toggleBtn.title = 'Cerrar noticias';
    } else {
      document.body.classList.remove('sidebar-open');
      toggleBtn.setAttribute('aria-label', 'Ver noticias');
      toggleBtn.title = 'Ver noticias';
    }
    // Fire resize after the 0.28-s CSS transition so the canvas recalculates
    setTimeout(() => window.dispatchEvent(new Event('resize')), 300);
  }

  // Start open on wide screens, hidden on mobile (< 768px)
  _apply(window.innerWidth >= 768);

  toggleBtn.addEventListener('click', () => {
    _apply(!document.body.classList.contains('sidebar-open'));
  });
}

/* ── Helpers ─────────────────────────────────────────────────────────────────── */

/**
 * Smooth scroll a container element to a target scrollTop over `duration` ms.
 * Uses an ease-in-out quadratic easing.
 */
function _smoothScroll(el, target, duration) {
  const start     = el.scrollTop;
  const distance  = target - start;
  const startTime = performance.now();

  function step(now) {
    const elapsed  = now - startTime;
    const t        = Math.min(elapsed / duration, 1);
    const ease     = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
    el.scrollTop   = start + distance * ease;
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

/** Convert ISO/date-string to Spanish relative time ("hace N min", "hace Nh", etc.). */
function _timeAgo(isoString) {
  try {
    const then    = new Date(isoString);
    if (isNaN(then.getTime())) return '';
    const diffSec = Math.floor((Date.now() - then.getTime()) / 1000);
    if (diffSec < 90)    return 'hace un momento';
    if (diffSec < 3600)  return `hace ${Math.floor(diffSec / 60)} min`;
    if (diffSec < 86400) return `hace ${Math.floor(diffSec / 3600)}h`;
    return `hace ${Math.floor(diffSec / 86400)}d`;
  } catch (_) { return ''; }
}

/** Minimal HTML escape to prevent XSS from external news headline text. */
function _escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
