/**
 * EdgeGenerator: Builds two tiers of connections.
 *
 * Tier 1 (tier:1) — Major node to major node.
 *   Drawn as visible emotion-colored lines; particles flow along them.
 *
 * Tier 2 (tier:2) — Satellite to satellite, same cluster only.
 *   Very subtle white texture. Max 3 connections per satellite.
 *   NO cross-cluster satellite connections.
 */
class EdgeGenerator {
  constructor() {
    this.edges = [];
  }

  /**
   * Generate both tiers of edges.
   * @param {Array} nodes - All nodes (major + satellite)
   * @returns {Array} Array of { key, a, b, strength, tier } edge objects
   */
  generate(nodes) {
    this.edges = [];

    // ── Tier 1: major-to-major ──────────────────────────────────────
    const majors = nodes.filter(n => n.isMajor);
    const MAX_DIST  = 0.22;
    const MAX_EDGES = 3;
    const seen = new Set();

    for (let i = 0; i < majors.length; i++) {
      const a = majors[i];

      const ranked = [];
      for (let j = 0; j < majors.length; j++) {
        if (i === j) continue;
        const b = majors[j];
        const dx = a.x - b.x, dy = a.y - b.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < MAX_DIST) ranked.push({ b, dist });
      }
      ranked.sort((x, y) => x.dist - y.dist);

      let added = 0;
      for (const { b, dist } of ranked) {
        if (added >= MAX_EDGES) break;
        const key = [a.id, b.id].sort().join('||');
        if (seen.has(key)) continue;
        seen.add(key);
        this.edges.push({ key, a, b, strength: 1 - dist / MAX_DIST, tier: 1 });
        added++;
      }
    }

    // ── Tier 2: satellite within same cluster (max 3 per satellite) ─
    const satsByState = {};
    for (const node of nodes) {
      if (!node.isMajor) {
        if (!satsByState[node.stateCode]) satsByState[node.stateCode] = [];
        satsByState[node.stateCode].push(node);
      }
    }

    const satEdgeSeen  = new Set();
    const satConnCount = {};   // id → number of tier-2 connections

    for (const sats of Object.values(satsByState)) {
      for (let i = 0; i < sats.length; i++) {
        const a = sats[i];
        if ((satConnCount[a.id] || 0) >= 3) continue;

        // Sort cluster-mates by distance
        const ranked = [];
        for (let j = 0; j < sats.length; j++) {
          if (i === j) continue;
          const b = sats[j];
          if ((satConnCount[b.id] || 0) >= 3) continue;
          const dx = a.x - b.x, dy = a.y - b.y;
          ranked.push({ b, dist: Math.sqrt(dx * dx + dy * dy) });
        }
        ranked.sort((x, y) => x.dist - y.dist);

        let added = 0;
        for (const { b } of ranked) {
          if (added >= 3) break;
          if ((satConnCount[a.id] || 0) >= 3) break;
          if ((satConnCount[b.id] || 0) >= 3) continue;
          const key = [a.id, b.id].sort().join('||');
          if (satEdgeSeen.has(key)) continue;
          satEdgeSeen.add(key);
          this.edges.push({ key, a, b, strength: 0.5, tier: 2 });
          satConnCount[a.id] = (satConnCount[a.id] || 0) + 1;
          satConnCount[b.id] = (satConnCount[b.id] || 0) + 1;
          added++;
        }
      }
    }

    return this.edges;
  }
}
