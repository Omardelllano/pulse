/**
 * WaveAnimator: Reveals nodes in wave_order sequence (0 first, 5 last).
 * Used when a new WorldState arrives from a simulation event.
 */
class WaveAnimator {
  constructor() {
    this.active    = false;
    this.startTime = 0;
    this.waveDelay = 480; // ms between each wave_order step
  }

  /** Start wave propagation animation. */
  start() {
    this.active    = true;
    this.startTime = performance.now();
  }

  /** Stop and reset. */
  stop() {
    this.active = false;
  }

  /**
   * Current maximum visible wave_order (0–5).
   * Returns 5 (all visible) when not animating.
   */
  getCurrentWaveOrder() {
    if (!this.active) return 5;
    const elapsed = performance.now() - this.startTime;
    const order   = Math.floor(elapsed / this.waveDelay);
    if (order >= 5) { this.active = false; return 5; }
    return order;
  }

  /** True if node should be drawn given current wave progress. */
  isNodeVisible(node) {
    if (!this.active) return true;
    return node.waveOrder <= this.getCurrentWaveOrder();
  }
}
