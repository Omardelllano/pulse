/**
 * GlowEffects — Four-layer radial-gradient glow for PULSO nodes.
 *
 * Rendering order (back to front):
 *  1. Outer halo   radius + intensity×45   — 'lighter', coreColor, α 0–0.12
 *  2. Medium ring  radius + 12             — 'lighter', glowColor, α 0–0.25
 *  3. Solid core   radius                  — source-over, coreColor, α 0.92
 *  4. Bright dot   radius × 0.30           — source-over, glowColor, α 0.70
 *
 * Key: NO white (255,255,255) anywhere. All layers use the node's own emotion
 * color palette so dense clusters stay colored, not washed to white.
 * Outer halo uses coreColor (saturated) to anchor the dominant hue.
 */
class GlowEffects {
  /**
   * @param {CanvasRenderingContext2D} ctx
   * @param {number} x, y       pixel coords (already pulse-scaled)
   * @param {number} radius     core radius in pixels
   * @param {string} coreColor  rgb(r,g,b) — saturated emotion color
   * @param {string} glowColor  rgb(r,g,b) — lighter tint of emotion color
   * @param {number} intensity  0–1
   * @param {number} alpha      composite opacity (alive × filter × node.alpha)
   */
  drawGlowNode(ctx, x, y, radius, coreColor, glowColor, intensity, alpha) {
    if (alpha < 0.008 || radius < 0.1) return;

    const outerR = radius + intensity * 45;          // large halo
    const midR   = Math.max(radius + 3, radius + 12); // medium ring
    const coreR  = Math.max(0.5, radius);
    const dotR   = Math.max(0.25, radius * 0.30);

    ctx.save();

    // ── Layer 1: Outer halo ('lighter', coreColor) ───────────────
    // Uses CORE color (saturated) so halo anchors the dominant hue.
    // Max opacity 0.12 — prevents saturation to white in dense clusters.
    ctx.globalCompositeOperation = 'lighter';
    const haloA = alpha * intensity * 0.12;
    if (haloA > 0.002 && outerR > 1) {
      const g1 = ctx.createRadialGradient(x, y, 0, x, y, outerR);
      g1.addColorStop(0,   this._rgba(coreColor, haloA));
      g1.addColorStop(0.5, this._rgba(coreColor, haloA * 0.4));
      g1.addColorStop(1,   this._rgba(coreColor, 0));
      ctx.beginPath();
      ctx.arc(x, y, outerR, 0, Math.PI * 2);
      ctx.fillStyle = g1;
      ctx.fill();
    }

    // ── Layer 2: Medium ring ('lighter', glowColor) ──────────────
    // Max opacity 0.25 — adds brightness without whitening.
    const midA = alpha * intensity * 0.25;
    if (midA > 0.003 && midR > 1) {
      const g2 = ctx.createRadialGradient(x, y, 0, x, y, midR);
      g2.addColorStop(0,   this._rgba(glowColor, midA));
      g2.addColorStop(0.5, this._rgba(glowColor, midA * 0.3));
      g2.addColorStop(1,   this._rgba(glowColor, 0));
      ctx.beginPath();
      ctx.arc(x, y, midR, 0, Math.PI * 2);
      ctx.fillStyle = g2;
      ctx.fill();
    }

    // ── Layer 3: Solid core (source-over, coreColor) ─────────────
    ctx.globalCompositeOperation = 'source-over';
    ctx.beginPath();
    ctx.arc(x, y, coreR, 0, Math.PI * 2);
    ctx.fillStyle = this._rgba(coreColor, alpha * 0.92);
    ctx.fill();

    // ── Layer 4: Bright centre dot (glowColor, NOT white) ────────
    // Using glowColor keeps the center tinted, not blown to white.
    ctx.beginPath();
    ctx.arc(x, y, dotR, 0, Math.PI * 2);
    ctx.fillStyle = this._rgba(glowColor, alpha * 0.70);
    ctx.fill();

    ctx.restore();
  }

  _rgba(color, alpha) {
    if (!color) return `rgba(200,200,255,0)`;
    const a = Math.max(0, Math.min(1, alpha));
    if (color.startsWith('#')) {
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);
      return `rgba(${r},${g},${b},${a.toFixed(3)})`;
    }
    if (color.startsWith('rgb(')) {
      return color.replace('rgb(', 'rgba(').replace(')', `,${a.toFixed(3)})`);
    }
    if (color.startsWith('rgba(')) {
      return color.replace(/,\s*[\d.]+\s*\)$/, `,${a.toFixed(3)})`);
    }
    return `rgba(200,200,255,${a.toFixed(3)})`;
  }
}
