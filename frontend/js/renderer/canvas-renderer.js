/**
 * CanvasRenderer — 60 fps render loop for PULSO.
 *
 * Visual features:
 *  • Major nodes: 4-layer colored glow halo, pulsing halo radius
 *  • Satellite nodes: mini halo + core + center dot, emotion color
 *  • 'lighter' compositing — glow overlaps ADD light, clusters bloom
 *  • Radial wave: sweeps from CDMX, each node flashes bright as front arrives
 *  • Tier-1 particles (state edges): 3–4/frame, 1.8px dot + 5px glow ring
 *  • Tier-2 particles (cluster edges): 2–3/frame, 0.7px tiny dot
 *  • Tier-1 connections: emotion color α=0.12, lineWidth 0.8
 *  • Tier-2 connections: white α=0.02, lineWidth 0.2
 *  • Drag + jelly spring: satellites follow dragged node with elastic lag
 *  • Emotion filter fades non-matching nodes to α=0.04
 *  • Plain dark background #050510
 */
class CanvasRenderer {
  constructor(canvas) {
    this.canvas        = canvas;
    this.ctx           = canvas.getContext('2d');
    this.nodes         = [];
    this.edges         = [];
    this._tier1Edges   = [];
    this._tier2Edges   = [];
    this.activeFilters = new Set();
    this.particles     = new ParticleSystem(CONFIG.CANVAS.PARTICLE_POOL_SIZE);
    this._animId       = null;
    this._startTime    = null;
    this._prevTime     = 0;
    this._time         = 0;
    this._deltaTime    = 0;
    this._frameCount   = 0;
    this.fps           = 60;
    this._fpsFrames    = 0;
    this._fpsLast      = 0;

    // Radial wave that flashes nodes as the front sweeps outward from CDMX
    this._wave = {
      active:  false,
      time:    0,
      centerX: 0.47,   // CDMX x (matches mexico.js)
      centerY: 0.58,   // CDMX y
      speed:   0.25,   // normalized units / second
      width:   0.06,   // detection band thickness
    };

    // Drag state
    this._drag = { active: false, node: null, sats: [] };

    this._resize();
    this._bindEvents();
    window.addEventListener('resize', () => this._resize());
  }

  // ── public API ───────────────────────────────────────────────

  get W() { return this.canvas.offsetWidth;  }
  get H() { return this.canvas.offsetHeight; }
  get isDragging() { return this._drag.active; }

  load(nodes, edges) {
    this.nodes       = nodes;
    this.edges       = edges;
    this._tier1Edges = edges.filter(e => e.tier === 1);
    this._tier2Edges = edges.filter(e => e.tier === 2);

    // All nodes fade in together from frame 1 (aliveDelay=0).
    // alive=0 → 1 over ~1 s before the wave arrives at 0.5 s.
    nodes.forEach((n, i) => {
      n.idx         = i;
      n.alive       = 0;
      n.aliveDelay  = 0;
      n.flash       = 0;
      n.flashed     = false;
      n.vx = 0; n.vy = 0;
      n.springing   = false;
      n.springDelay = 0;
      n.dragging    = false;
    });

    this.start();
  }

  start() {
    if (this._animId) cancelAnimationFrame(this._animId);
    this._startTime  = null;
    this._frameCount = 0;
    this._loop(0);
  }

  stop() {
    if (this._animId) { cancelAnimationFrame(this._animId); this._animId = null; }
  }

  setFilters(filters) { this.activeFilters = filters; }

  /**
   * Start the traveling wave ring from CDMX.
   * Nodes keep their current brightness; wave ADDS boost as it passes.
   */
  startWave() {
    this._wave.active = true;
    this._wave.time   = 0;
    for (const node of this.nodes) { node.flash = 0; node.flashed = false; }
  }

  /** Flash all nodes of a given emotion (e.g., on filter button click). */
  flashEmotion(emotion) {
    for (const node of this.nodes) {
      if (node.emotion === emotion) node.flash = 0.6;
    }
  }

  /** Replay wave (does not reset node brightness). */
  replayWave() { this.startWave(); }

  // ── event binding ────────────────────────────────────────────

  _bindEvents() {
    this.canvas.addEventListener('mousedown',  e => this._onMouseDown(e));
    this.canvas.addEventListener('mousemove',  e => this._onMouseMove(e));
    window .addEventListener('mouseup',    () => this._onMouseUp());
    this.canvas.addEventListener('mouseleave', () => {
      if (!this._drag.active) this.canvas.style.cursor = 'crosshair';
    });

    this.canvas.addEventListener('touchstart', e => this._onTouchStart(e), { passive: false });
    this.canvas.addEventListener('touchmove',  e => this._onTouchMove(e),  { passive: false });
    this.canvas.addEventListener('touchend',   e => this._onTouchEnd(e),   { passive: false });
  }

  _canvasToNorm(e) {
    const r = this.canvas.getBoundingClientRect();
    return { nx: (e.clientX - r.left) / r.width, ny: (e.clientY - r.top) / r.height };
  }

  _touchToNorm(touch) {
    const r = this.canvas.getBoundingClientRect();
    return { nx: (touch.clientX - r.left) / r.width, ny: (touch.clientY - r.top) / r.height };
  }

  _majorAtPoint(nx, ny, threshold = 0.045) {
    let best = null, minD = Infinity;
    for (const node of this.nodes) {
      if (!node.isMajor || node.alive < 0.1) continue;
      const dx = node.x - nx, dy = node.y - ny;
      const d  = Math.sqrt(dx * dx + dy * dy);
      if (d < minD && d < threshold) { minD = d; best = node; }
    }
    return best;
  }

  _startDrag(nx, ny) {
    const node = this._majorAtPoint(nx, ny);
    if (!node) return;
    node.dragging  = true;
    node.springing = false;
    const sats = this.nodes.filter(n => !n.isMajor && n.stateCode === node.stateCode);
    this._drag = {
      active: true,
      node,
      sats: sats.map(s => ({ node: s, ox: s.originX - node.originX, oy: s.originY - node.originY })),
    };
    this.canvas.style.cursor = 'grabbing';
  }

  _moveDrag(nx, ny) {
    if (!this._drag.active || !this._drag.node) return;
    this._drag.node.x = Math.max(0.01, Math.min(0.99, nx));
    this._drag.node.y = Math.max(0.01, Math.min(0.99, ny));
  }

  _endDrag() {
    if (!this._drag.active) return;
    const node = this._drag.node;
    node.dragging  = false;
    node.springing = true;
    node.vx = 0; node.vy = 0;
    node.springDelay = 0;
    for (const { node: sat } of this._drag.sats) {
      sat.springing  = true;
      sat.vx = 0; sat.vy = 0;
      sat.springDelay = Math.floor(Math.random() * 14);   // 0–0.23 s stagger
    }
    this._drag = { active: false, node: null, sats: [] };
    this.canvas.style.cursor = 'crosshair';
  }

  _onMouseDown(e) { const { nx, ny } = this._canvasToNorm(e); this._startDrag(nx, ny); }
  _onMouseMove(e) {
    const { nx, ny } = this._canvasToNorm(e);
    if (this._drag.active) {
      this._moveDrag(nx, ny);
    } else {
      this.canvas.style.cursor = this._majorAtPoint(nx, ny) ? 'grab' : 'crosshair';
    }
  }
  _onMouseUp() { this._endDrag(); }
  _onTouchStart(e) { e.preventDefault(); this._startDrag(...Object.values(this._touchToNorm(e.touches[0]))); }
  _onTouchMove(e)  { e.preventDefault(); const { nx, ny } = this._touchToNorm(e.touches[0]); this._moveDrag(nx, ny); }
  _onTouchEnd(e)   { e.preventDefault(); this._endDrag(); }

  // ── animation loop ───────────────────────────────────────────

  _loop(ts) {
    if (!this._startTime) { this._startTime = ts; this._prevTime = ts; }
    this._deltaTime  = Math.min((ts - this._prevTime) / 1000, 0.1);  // cap at 100 ms
    this._prevTime   = ts;
    this._time       = (ts - this._startTime) / 1000;
    this._frameCount++;

    this._fpsFrames++;
    if (ts - this._fpsLast >= 1000) {
      this.fps = this._fpsFrames;
      this._fpsFrames = 0;
      this._fpsLast = ts;
    }

    this._render();
    this._animId = requestAnimationFrame(t => this._loop(t));
  }

  // ── render ───────────────────────────────────────────────────

  _render() {
    const ctx = this.ctx;
    const W = this.W, H = this.H;
    const t  = this._time;
    const dt = this._deltaTime;
    const fc = this._frameCount;

    // 1 ── Background ──────────────────────────────────────────
    ctx.fillStyle = CONFIG.CANVAS.BACKGROUND_COLOR;
    ctx.fillRect(0, 0, W, H);

    // 2 ── Node fade-in (all nodes, aliveDelay=0, quick unified rise)
    for (const node of this.nodes) {
      if (fc >= node.aliveDelay) {
        node.alive = Math.min(1, node.alive + (1 - node.alive) * 0.04);
      }
    }

    // 3 ── Radial wave: flash each node once when front sweeps over it ──
    const wave = this._wave;
    if (wave.active) {
      wave.time += dt;
      const waveFront = wave.time * wave.speed;

      // Trigger a one-shot flash on each node as the expanding front arrives
      for (const node of this.nodes) {
        const dist = Math.hypot(node.x - wave.centerX, node.y - wave.centerY);
        if (!node.flashed && dist < waveFront && dist > waveFront - wave.width) {
          node.flash   = 1.0;
          node.flashed = true;
        }
      }

      if (waveFront > 1.0) wave.active = false;
    }

    // Always decay flash — runs during and after wave
    for (const node of this.nodes) {
      if (node.flash > 0.01) node.flash *= 0.92;
      else node.flash = 0;
    }

    // 4 ── Spring-back physics ─────────────────────────────────
    for (const node of this.nodes) {
      if (!node.springing) continue;
      if (node.springDelay > 0) { node.springDelay--; continue; }
      node.vx = (node.vx + (node.originX - node.x) * 0.08) * 0.85;
      node.vy = (node.vy + (node.originY - node.y) * 0.08) * 0.85;
      node.x += node.vx;
      node.y += node.vy;
      if (Math.abs(node.vx) < 0.00008 && Math.abs(node.vy) < 0.00008 &&
          Math.abs(node.x - node.originX) < 0.0005) {
        node.x = node.originX; node.y = node.originY;
        node.vx = 0; node.vy = 0;
        node.springing = false;
      }
    }

    // 5 ── Satellite drift (skip dragged cluster + springing) ──
    const dragCode = this._drag.active && this._drag.node ? this._drag.node.stateCode : null;
    for (const node of this.nodes) {
      if (!node.isMajor && !node.springing && node.stateCode !== dragCode) {
        node.x = node.originX + Math.sin(t * node.driftSpeed + node.driftPhase)            * 0.003;
        node.y = node.originY + Math.cos(t * node.driftSpeed * 0.65 + node.driftPhase + 1) * 0.003;
      }
    }

    // 6 ── Jelly spring: satellites follow dragged node with elastic lag
    if (this._drag.active && this._drag.node) {
      const dn = this._drag.node;
      this._drag.sats.forEach(({ node: sat, ox, oy }, i) => {
        const targetX      = dn.x + ox;
        const targetY      = dn.y + oy;
        const springFactor = 0.03 + i * 0.002;   // staggered delay — index 0 is fastest
        sat.x = Math.max(0.01, Math.min(0.99, sat.x + (targetX - sat.x) * springFactor));
        sat.y = Math.max(0.01, Math.min(0.99, sat.y + (targetY - sat.y) * springFactor));
      });
    }

    // 7 ── Tier-2 connections (satellite within-cluster) ───────
    ctx.save();
    ctx.lineWidth = 0.2;
    for (const edge of this._tier2Edges) {
      const aF = Math.min(edge.a.alive, edge.b.alive);
      if (aF < 0.02) continue;
      const fa = Math.min(this._filterAlpha(edge.a), this._filterAlpha(edge.b));
      ctx.globalAlpha = aF * fa;
      ctx.strokeStyle = 'rgba(255,255,255,0.02)';
      ctx.beginPath();
      ctx.moveTo(edge.a.x * W, edge.a.y * H);
      ctx.lineTo(edge.b.x * W, edge.b.y * H);
      ctx.stroke();
    }
    ctx.restore();

    // 8 ── Tier-1 connections (state-to-state, emotion colored) ─
    ctx.save();
    ctx.lineWidth = 0.8;
    for (const edge of this._tier1Edges) {
      const aF = Math.min(edge.a.alive, edge.b.alive);
      if (aF < 0.02) continue;
      const fa = Math.min(this._filterAlpha(edge.a), this._filterAlpha(edge.b));
      const em = CONFIG.EMOTIONS[edge.a.emotion];
      if (!em) continue;
      ctx.strokeStyle = `rgba(${em.c[0]},${em.c[1]},${em.c[2]},0.12)`;
      ctx.globalAlpha = aF * fa;
      ctx.beginPath();
      ctx.moveTo(edge.a.x * W, edge.a.y * H);
      ctx.lineTo(edge.b.x * W, edge.b.y * H);
      ctx.stroke();
    }
    ctx.restore();

    // 9 ── Spawn tier-1 particles (state edges, 3–4/frame) ─────
    if (this._tier1Edges.length) {
      const count = 3 + (Math.random() < 0.5 ? 1 : 0);
      for (let s = 0; s < count; s++) {
        const edge = this._tier1Edges[Math.floor(Math.random() * this._tier1Edges.length)];
        if (edge.a.alive > 0.35 && this._filterAlpha(edge.a) > 0.5) {
          const ecfg = CONFIG.EMOTIONS[edge.a.emotion];
          if (ecfg && ecfg.g) this.particles.spawn(edge, ecfg.g, 1);
        }
      }
    }

    // 10 ── Spawn tier-2 particles (cluster edges, 2–3/frame) ──
    if (this._tier2Edges.length) {
      const count = 2 + (Math.random() < 0.5 ? 1 : 0);
      for (let s = 0; s < count; s++) {
        const edge = this._tier2Edges[Math.floor(Math.random() * this._tier2Edges.length)];
        if (edge.a.alive > 0.35 && this._filterAlpha(edge.a) > 0.5) {
          const ecfg = CONFIG.EMOTIONS[edge.a.emotion];
          if (ecfg && ecfg.g) this.particles.spawn(edge, ecfg.g, 2);
        }
      }
    }

    // 11 ── Draw particles ─────────────────────────────────────
    this.particles.update(ctx, W, H);

    // 12 ── Satellites (lighter composite) ─────────────────────
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (const node of this.nodes) {
      if (!node.isMajor) this._drawSatNode(ctx, node, W, H, t);
    }
    ctx.restore();

    // 13 ── Major nodes (lighter composite) ────────────────────
    ctx.save();
    ctx.globalCompositeOperation = 'lighter';
    for (const node of this.nodes) {
      if (node.isMajor) this._drawMajorNode(ctx, node, W, H, t);
    }
    ctx.restore();

    // 14 ── State-code labels (source-over) ────────────────────
    for (const node of this.nodes) {
      if (node.isMajor && node.alive > 0.12) {
        this._drawLabel(ctx, node, W, H);
      }
    }
  }

  // ── major node: 4-layer colored glow + wave boost ─────────────

  _drawMajorNode(ctx, node, W, H, t) {
    if (node.alive < 0.01) return;
    const fa = this._filterAlpha(node);
    let alive = node.alive * fa;
    if (alive < 0.008) return;

    if (node.dragging) alive = Math.min(1, alive * 1.3);

    const em = CONFIG.EMOTIONS[node.emotion];
    if (!em) return;

    const flash = node.flash || 0;
    const pulse = Math.sin(t * 1.8 + node.idx * 0.17) * 0.4 + 0.6;
    const cx = node.x * W, cy = node.y * H;
    const r  = node.radius;

    // Layer 1: BIG soft halo — flares when wave hits this node
    const haloR     = r + node.intensity * (55 + flash * 30) * pulse;
    const haloAlpha = (0.30 + flash * 0.5) * node.intensity * alive * (0.7 + pulse * 0.3);
    if (haloR > 1 && haloAlpha > 0.002) {
      const g1 = ctx.createRadialGradient(cx, cy, 0, cx, cy, haloR);
      g1.addColorStop(0,   `rgba(${em.g[0]},${em.g[1]},${em.g[2]},${haloAlpha.toFixed(3)})`);
      g1.addColorStop(0.3, `rgba(${em.c[0]},${em.c[1]},${em.c[2]},${(haloAlpha * 0.4).toFixed(3)})`);
      g1.addColorStop(1,   'rgba(0,0,0,0)');
      ctx.beginPath();
      ctx.arc(cx, cy, haloR, 0, Math.PI * 2);
      ctx.fillStyle = g1;
      ctx.fill();
    }

    // Layer 2: Medium bright ring — also boosted by wave
    const ringR = r + 8 * pulse;
    if (ringR > 1) {
      const g2 = ctx.createRadialGradient(cx, cy, 0, cx, cy, ringR);
      g2.addColorStop(0,   `rgba(${em.g[0]},${em.g[1]},${em.g[2]},${((0.4 + flash * 0.3) * alive).toFixed(3)})`);
      g2.addColorStop(0.5, `rgba(${em.c[0]},${em.c[1]},${em.c[2]},${(0.25 * alive).toFixed(3)})`);
      g2.addColorStop(1,   `rgba(${em.c[0]},${em.c[1]},${em.c[2]},${(0.03 * alive).toFixed(3)})`);
      ctx.beginPath();
      ctx.arc(cx, cy, ringR, 0, Math.PI * 2);
      ctx.fillStyle = g2;
      ctx.fill();
    }

    // Layer 3: Solid core — core brightens on flash
    ctx.beginPath();
    ctx.arc(cx, cy, r * (0.85 + pulse * 0.15), 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${em.c[0]},${em.c[1]},${em.c[2]},${((0.85 + flash * 0.15) * alive).toFixed(3)})`;
    ctx.fill();

    // Layer 4: Bright centre (glow color, never white)
    ctx.beginPath();
    ctx.arc(cx, cy, r * 0.3, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${em.g[0]},${em.g[1]},${em.g[2]},${(0.9 * alive).toFixed(3)})`;
    ctx.fill();
  }

  // ── satellite node: 3-layer compact glow + wave boost ─────────

  _drawSatNode(ctx, node, W, H, t) {
    if (node.alive < 0.01) return;
    const fa = this._filterAlpha(node);
    const alive = node.alive * fa * node.alpha;
    if (alive < 0.008) return;

    const em = CONFIG.EMOTIONS[node.emotion];
    if (!em) return;

    const flash = node.flash || 0;
    const pulse = Math.sin(t * 1.8 + node.idx * 0.17) * 0.4 + 0.6;
    const cx = node.x * W, cy = node.y * H;
    const sr = node.radius * (0.75 + pulse * 0.25);

    // Mini halo — flares when wave hits this node
    ctx.beginPath();
    ctx.arc(cx, cy, sr + 6, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${em.g[0]},${em.g[1]},${em.g[2]},${((0.15 + flash * 0.35) * alive * node.intensity).toFixed(3)})`;
    ctx.fill();

    // Core
    ctx.beginPath();
    ctx.arc(cx, cy, sr, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${em.c[0]},${em.c[1]},${em.c[2]},${(0.65 * alive * node.intensity).toFixed(3)})`;
    ctx.fill();

    // Centre bright dot
    ctx.beginPath();
    ctx.arc(cx, cy, sr * 0.35, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(${em.g[0]},${em.g[1]},${em.g[2]},${(0.80 * alive * node.intensity).toFixed(3)})`;
    ctx.fill();
  }

  // ── label ────────────────────────────────────────────────────

  _drawLabel(ctx, node, W, H) {
    const fa = this._filterAlpha(node);
    if (fa < 0.1) return;
    const x    = node.x * W;
    const y    = node.y * H;
    const size = Math.max(8, Math.min(11, node.radius * 1.1));
    const a    = node.alive * fa;
    ctx.save();
    ctx.globalCompositeOperation = 'source-over';
    ctx.font      = `${size}px monospace`;
    ctx.fillStyle = `rgba(255,255,255,${(0.70 * a).toFixed(3)})`;
    ctx.textAlign = 'center';
    const ecfg = CONFIG.EMOTIONS[node.emotion] || {};
    ctx.shadowColor = ecfg.glow || '#ffffff';
    ctx.shadowBlur  = 6;
    ctx.fillText(node.stateCode, x, y + node.radius + size + 3);
    ctx.restore();
  }

  // ── filter ───────────────────────────────────────────────────

  _filterAlpha(node) {
    if (this.activeFilters.size === 0) return 1.0;
    return this.activeFilters.has(node.emotion) ? 1.0 : 0.04;
  }

  // ── resize ───────────────────────────────────────────────────

  _resize() {
    const dpr = window.devicePixelRatio || 1;
    this.canvas.width  = this.canvas.offsetWidth  * dpr;
    this.canvas.height = this.canvas.offsetHeight * dpr;
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
}
