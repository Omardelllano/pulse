/**
 * EmotionFilter: Creates filter buttons and wires them to the renderer.
 * Each emotion button shows a small colored dot before the label.
 * Clicking a button toggles visibility of nodes with that emotion.
 */
class EmotionFilter {
  constructor(container, renderer) {
    this.container    = container;
    this.renderer     = renderer;
    this.activeSet    = new Set();
    this._build();
  }

  _build() {
    this.container.innerHTML = '';

    // "Todos" (show all) button — no dot
    const allBtn = this._makeBtn('Todos', null, 'filter-btn--all');
    allBtn.classList.add('active');
    allBtn.addEventListener('click', () => this._showAll());
    this.container.appendChild(allBtn);

    // One button per emotion, with colored dot
    for (const [emotion, cfg] of Object.entries(CONFIG.EMOTIONS)) {
      const btn = this._makeBtn(cfg.label, emotion, 'filter-btn--emotion');
      btn.style.setProperty('--emotion-color', cfg.color);
      btn.addEventListener('click', () => this._toggle(emotion));
      this.container.appendChild(btn);
    }
  }

  _makeBtn(label, emotion, extraClass) {
    const btn = document.createElement('button');
    btn.className = `filter-btn ${extraClass}`;
    if (emotion) {
      btn.dataset.emotion = emotion;
      const dot = document.createElement('span');
      dot.className = 'filter-dot';
      btn.appendChild(dot);
    }
    btn.appendChild(document.createTextNode(label));
    return btn;
  }

  _toggle(emotion) {
    this._btn(null).classList.remove('active');

    if (this.activeSet.has(emotion)) {
      this.activeSet.delete(emotion);
      this._btn(emotion).classList.remove('active');
    } else {
      this.activeSet.add(emotion);
      this._btn(emotion).classList.add('active');
    }

    if (this.activeSet.size === 0) {
      this._btn(null).classList.add('active');
    }

    this.renderer.setFilters(new Set(this.activeSet));
    // Quick pulse on nodes of this emotion for satisfying visual feedback
    this.renderer.flashEmotion(emotion);
  }

  _showAll() {
    this.activeSet.clear();
    this.container.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    this._btn(null).classList.add('active');
    this.renderer.setFilters(new Set());
  }

  _btn(emotion) {
    if (!emotion) return this.container.querySelector('.filter-btn--all');
    return this.container.querySelector(`[data-emotion="${emotion}"]`);
  }
}
