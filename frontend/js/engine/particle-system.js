/**
 * ParticleSystem — Two-tier glowing dots that travel along connections.
 *
 * Tier 1 (state-to-state):
 *   core dot 1.8px + glow ring 5px, speed 0.008–0.020, α fades with progress
 *
 * Tier 2 (within cluster):
 *   tiny dot 0.7px only, speed 0.015–0.035, α fades with progress
 *
 * 'lighter' compositing — glow adds to background light, stays emotion-colored.
 * Pre-allocated pool (zero GC).
 */
class ParticleSystem {
  constructor(poolSize = 400) {
    this._pool   = [];
    this._active = [];
    for (let i = 0; i < poolSize; i++) {
      this._pool.push({
        active: false, edgeA: null, edgeB: null,
        progress: 0, speed: 0.015,
        colorRGB: [200, 200, 255],
        tier: 1,
        life: 0, maxLife: 120,
      });
    }
  }

  /**
   * Spawn a particle along edge (a → b).
   * @param {Object}   edge  — { a, b } node refs
   * @param {number[]} rgb   — [r,g,b] glow color from CONFIG.EMOTIONS[e].g
   * @param {number}   tier  — 1 (state) or 2 (cluster)
   */
  spawn(edge, rgb, tier = 1) {
    const p = this._pool.find(x => !x.active);
    if (!p) return;

    p.active   = true;
    p.edgeA    = edge.a;
    p.edgeB    = edge.b;
    p.progress = 0;
    p.colorRGB = rgb || [200, 200, 255];
    p.tier     = tier;

    if (tier === 1) {
      p.speed = 0.008 + Math.random() * 0.012;   // 0.008–0.020
    } else {
      p.speed = 0.015 + Math.random() * 0.020;   // 0.015–0.035
    }

    p.life    = 0;
    p.maxLife = Math.ceil(1 / p.speed) + 10;
    this._active.push(p);
  }

  /**
   * Advance & draw all active particles.
   * Call once per frame inside the render loop.
   */
  update(ctx, W, H) {
    if (this._active.length === 0) return;

    const dead = [];

    ctx.save();
    ctx.globalCompositeOperation = 'lighter';

    for (const p of this._active) {
      p.progress += p.speed;
      p.life++;

      if (p.progress >= 1.0 || p.life > p.maxLife) {
        p.active = false;
        dead.push(p);
        continue;
      }

      const px   = (p.edgeA.x + (p.edgeB.x - p.edgeA.x) * p.progress) * W;
      const py   = (p.edgeA.y + (p.edgeB.y - p.edgeA.y) * p.progress) * H;
      const fade = 1 - p.progress;
      const cr   = p.colorRGB[0], cg = p.colorRGB[1], cb = p.colorRGB[2];

      if (p.tier === 1) {
        // Tier 1: dot (1.8px) + glow ring (5px)
        ctx.beginPath();
        ctx.arc(px, py, 5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${cr},${cg},${cb},${(fade * 0.15).toFixed(3)})`;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(px, py, 1.8, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${cr},${cg},${cb},${(fade * 0.70).toFixed(3)})`;
        ctx.fill();
      } else {
        // Tier 2: tiny dot only
        ctx.beginPath();
        ctx.arc(px, py, 0.7, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${cr},${cg},${cb},${(fade * 0.30).toFixed(3)})`;
        ctx.fill();
      }
    }

    ctx.restore();

    for (const p of dead) {
      const i = this._active.indexOf(p);
      if (i !== -1) this._active.splice(i, 1);
    }
  }
}
