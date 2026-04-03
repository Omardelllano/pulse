/**
 * NodeGenerator — Converts WorldState (32 states) into 1400+ canvas nodes.
 *
 * Key design decisions:
 *  - Spread radius is generous (0.04 + pop*0.07) so clusters fill geographic territory
 *  - Satellite emotions follow the contagion matrix deterministically (dominant colour visible)
 *  - Every node carries alive/drift/idx data for animation in the renderer
 */
class NodeGenerator {
  constructor() {
    this.nodes = [];
  }

  generate(worldState, stateConfigs, contagion) {
    this.nodes = [];
    let globalIdx = 0;

    const cfgMap = {};
    for (const cfg of stateConfigs) cfgMap[cfg.code] = cfg;

    // Pre-compute neighbor density for each state (used to prevent center blob)
    const densityMap = {};
    for (const cfg of stateConfigs) {
      let neighbors = 0;
      for (const other of stateConfigs) {
        if (other.code === cfg.code) continue;
        const dx = cfg.x - other.x, dy = cfg.y - other.y;
        if (Math.sqrt(dx * dx + dy * dy) < 0.1) neighbors++;
      }
      densityMap[cfg.code] = neighbors;
    }

    for (const se of worldState.states) {
      const cfg = cfgMap[se.state_code];
      if (!cfg) continue;

      const baseDelay = (se.wave_order || 0) * 48; // 0.8 s per wave_order at 60 fps

      // ── Major node (state capital / centre) ─────────────────────
      this.nodes.push({
        id:          `major_${se.state_code}`,
        stateCode:   se.state_code,
        stateName:   se.state_name,
        emotion:     se.emotion,
        intensity:   se.intensity,
        description: se.description,
        waveOrder:   se.wave_order || 0,
        isMajor:     true,
        x:           cfg.x,   y:    cfg.y,
        originX:     cfg.x,   originY: cfg.y,
        radius:      CONFIG.CANVAS.MAJOR_NODE_RADIUS * (0.65 + cfg.pop * 0.45),
        alpha:       1.0,
        population_weight: se.population_weight || cfg.pop,
        alive:       0,   aliveDelay: baseDelay,
        idx:         globalIdx++,
      });

      // ── Satellite nodes ──────────────────────────────────────────
      // More satellites + bigger spread to fill Mexico's geography
      const count = Math.max(22, Math.round(cfg.satelliteBase * (1.2 + se.intensity * 0.55)));

      // Deterministic contagion distribution → dominant colour always visible
      const probs = contagion[se.emotion] || contagion['fear'];
      const slots = this._buildSlots(probs, count);

      // Spread radius: fill state territory; reduce 30% in dense center to prevent blob
      const densityFactor = densityMap[se.state_code] > 3 ? 0.70 : 1.0;
      const spreadR = (0.042 + cfg.pop * 0.068) * densityFactor;

      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const dist  = Math.sqrt(Math.random()) * spreadR; // uniform disk

        const ox = Math.max(0.01, Math.min(0.99, cfg.x + Math.cos(angle) * dist));
        const oy = Math.max(0.01, Math.min(0.99, cfg.y + Math.sin(angle) * dist));

        // Minority emotion satellites are dimmer — keeps dominant color readable
        const baseIntensity = Math.max(0.18, Math.min(1, se.intensity * (0.5 + Math.random() * 0.6)));
        const satIntensity  = slots[i] === se.emotion
          ? baseIntensity
          : Math.max(0.05, baseIntensity * 0.5);

        this.nodes.push({
          id:          `sat_${se.state_code}_${i}`,
          stateCode:   se.state_code,
          stateName:   se.state_name,
          emotion:     slots[i],
          intensity:   satIntensity,
          description: se.description,
          waveOrder:   se.wave_order || 0,
          isMajor:     false,
          x: ox, y: oy, originX: ox, originY: oy,
          radius:  CONFIG.CANVAS.NODE_MIN_RADIUS +
                   Math.random() * (CONFIG.CANVAS.NODE_MAX_RADIUS - CONFIG.CANVAS.NODE_MIN_RADIUS),
          alpha:   0.55 + Math.random() * 0.45,
          population_weight: cfg.pop,
          // Drift
          driftSpeed: 0.22 + Math.random() * 0.50,
          driftPhase: Math.random() * Math.PI * 2,
          // Wave
          alive:      0,
          aliveDelay: baseDelay + Math.random() * 18,
          idx:        globalIdx++,
        });
      }
    }

    return this.nodes;
  }

  /** Fisher-Yates-shuffled array of emotion labels matching contagion probs. */
  _buildSlots(probs, count) {
    const slots = [];
    for (const [em, p] of Object.entries(probs)) {
      const n = Math.round(p * count);
      for (let j = 0; j < n; j++) slots.push(em);
    }
    const dominant = Object.entries(probs).sort((a, b) => b[1] - a[1])[0][0];
    while (slots.length < count) slots.push(dominant);
    while (slots.length > count) slots.pop();
    for (let i = slots.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      const t = slots[i]; slots[i] = slots[j]; slots[j] = t;
    }
    return slots;
  }

  getCount() { return this.nodes.length; }
}
