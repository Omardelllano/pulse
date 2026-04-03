// PULSO Frontend Configuration
const CONFIG = {
  // Data source: "mock" loads from fixtures.js (zero API calls)
  //              "api"  calls the backend REST API
  DATA_SOURCE: "api",

  // Backend API base URL (only used when DATA_SOURCE = "api")
  // Empty string = relative path → always same-origin, no CORS preflight
  API_URL: "",

  // Canvas rendering settings
  CANVAS: {
    BACKGROUND_COLOR: "#050510",   // Very dark blue-black (NOT pure black)
    NODE_MIN_RADIUS: 2.5,
    NODE_MAX_RADIUS: 6,
    MAJOR_NODE_RADIUS: 11,
    GLOW_LAYERS: 4,
    EDGE_ALPHA: 0.03,              // Near-invisible connection lines
    PARTICLE_POOL_SIZE: 300,
    TARGET_FPS: 60,
  },

  // Emotion colors — exact values per spec
  // core:  solid node fill (rgb string)
  // glow:  radial gradient / particle color (rgb string)
  // color: hex alias for CSS (filter buttons, tooltips)
  // label: Spanish display name
  // c:     [r,g,b] core color array for fast inline rgba() in renderer
  // g:     [r,g,b] glow color array for fast inline rgba() in renderer
  EMOTIONS: {
    anger:   { core: 'rgb(226,75,74)',    glow: 'rgb(255,130,120)', color: '#e24b4a', label: 'Enojo',     c: [226,75,74],    g: [255,130,120] },
    joy:     { core: 'rgb(239,175,50)',   glow: 'rgb(255,225,130)', color: '#efaf32', label: 'Alegría',   c: [239,175,50],   g: [255,225,130] },
    fear:    { core: 'rgb(140,130,235)',  glow: 'rgb(195,185,255)', color: '#8c82eb', label: 'Miedo',     c: [140,130,235],  g: [195,185,255] },
    hope:    { core: 'rgb(40,180,130)',   glow: 'rgb(110,235,185)', color: '#28b482', label: 'Esperanza', c: [40,180,130],   g: [110,235,185] },
    sadness: { core: 'rgb(70,150,230)',   glow: 'rgb(145,200,255)', color: '#4696e6', label: 'Tristeza',  c: [70,150,230],   g: [145,200,255] },
  },
};
