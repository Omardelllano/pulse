/**
 * Tooltip: Shows state name, emotion, intensity, and description on hover.
 * Activates when mouse is within threshold distance of a major node.
 * Hides while dragging so it doesn't interfere with drag UX.
 */
class Tooltip {
  constructor(el, canvas, renderer) {
    this.el       = el;
    this.canvas   = canvas;
    this.renderer = renderer;
    this._bind();
  }

  _bind() {
    this.canvas.addEventListener('mousemove', e => this._onMove(e));
    this.canvas.addEventListener('mouseleave', () => this._hide());
    this.canvas.addEventListener('touchmove', e => {
      e.preventDefault();
      const t = e.touches[0];
      this._onMove({ clientX: t.clientX, clientY: t.clientY });
    }, { passive: false });
  }

  _onMove(e) {
    // Hide tooltip while dragging a node
    if (this.renderer.isDragging) { this._hide(); return; }

    const rect = this.canvas.getBoundingClientRect();
    const mx   = (e.clientX - rect.left)  / rect.width;
    const my   = (e.clientY - rect.top)   / rect.height;
    const node = this._nearest(mx, my);
    if (node) {
      this._show(node, e.clientX, e.clientY);
    } else {
      this._hide();
    }
  }

  _nearest(mx, my) {
    let best = null, minD = Infinity;
    for (const n of this.renderer.nodes) {
      if (!n.isMajor) continue;
      const dx = n.x - mx, dy = n.y - my;
      const d  = Math.sqrt(dx * dx + dy * dy);
      if (d < minD && d < 0.05) { minD = d; best = n; }
    }
    return best;
  }

  _show(node, cx, cy) {
    const ecfg  = CONFIG.EMOTIONS[node.emotion] || {};
    const pct   = Math.round(node.intensity * 100);
    this.el.innerHTML = `
      <div class="tooltip-state">${node.stateName}</div>
      <div class="tooltip-emotion" style="color:${ecfg.color || '#fff'}">
        ${ecfg.label || node.emotion} &middot; ${pct}%
      </div>
      <div class="tooltip-desc">${node.description}</div>
    `;
    this.el.style.display = 'block';
    this.el.style.left    = `${cx + 14}px`;
    this.el.style.top     = `${cy - 10}px`;

    // Keep inside viewport
    const r = this.el.getBoundingClientRect();
    if (r.right  > window.innerWidth)  this.el.style.left = `${cx - r.width  - 14}px`;
    if (r.bottom > window.innerHeight) this.el.style.top  = `${cy - r.height}px`;
  }

  _hide() {
    this.el.style.display = 'none';
  }
}
