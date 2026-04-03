/**
 * Simplified Mexico border outlines in normalized canvas coordinates (0–1).
 * Drawn before nodes as a very faint geographic reference layer.
 * Coordinates approximate Mexico's shape in our visual projection space.
 *
 * x=0 = west edge of map, x=1 = east edge
 * y=0 = north edge,        y=1 = south edge
 */

// Mainland Mexico border (clockwise from NW corner)
const MEXICO_OUTLINE_MAINLAND = [
  // ── US–Mexico border (top) ───────────────────────────────────
  [0.04, 0.03],  // Tijuana / NW
  [0.17, 0.02],  // Sonora / Arizona border
  [0.36, 0.02],  // Chihuahua / NM border
  [0.56, 0.04],  // Ciudad Juárez
  [0.68, 0.07],  // Ojinaga / Presidio
  [0.77, 0.12],  // Acuña / Del Rio area
  [0.84, 0.18],  // Nuevo Laredo / Laredo
  [0.89, 0.24],  // Reynosa / McAllen
  // ── Gulf of Mexico coast (east side, going south) ────────────
  [0.90, 0.30],  // Matamoros / Brownsville — Gulf begins
  [0.91, 0.38],  // Tampico area
  [0.88, 0.46],  // Veracruz area
  [0.82, 0.53],  // Coatzacoalcos
  [0.76, 0.60],  // Villahermosa area
  [0.78, 0.66],  // Campeche coast
  // ── Yucatán peninsula (NE bulge) ─────────────────────────────
  [0.87, 0.61],  // Northern Yucatán
  [0.94, 0.64],  // Cancún
  [0.93, 0.76],  // Chetumal / Tulum
  // ── Guatemala / Belize border (bottom-east) ──────────────────
  [0.82, 0.85],  // Chetumal south / Belize
  [0.72, 0.89],  // Guatemala border E
  [0.63, 0.90],  // Chiapas south
  // ── Pacific coast (going northwest) ──────────────────────────
  [0.55, 0.86],  // Huatulco / Oaxaca coast
  [0.46, 0.80],  // Guerrero coast
  [0.36, 0.74],  // Michoacán / Jalisco coast
  [0.28, 0.69],  // Manzanillo area
  [0.22, 0.57],  // Nayarit coast
  [0.17, 0.45],  // Mazatlán / Sinaloa
  [0.13, 0.34],  // Los Mochis area
  [0.10, 0.23],  // Sonora coast (mainland — east side of Gulf of Calif)
  // ── Gulf of California notch (back up to NW) ─────────────────
  [0.08, 0.13],  // Guaymas area
  [0.06, 0.08],  // Sonora NW coast
  [0.04, 0.03],  // Close — back to NW corner
];

// Baja California peninsula (separate polygon, west of Gulf of California)
const MEXICO_OUTLINE_BAJA = [
  [0.05, 0.03],  // Border — Tijuana
  [0.08, 0.03],  // Border junction
  [0.09, 0.08],  // BC mid-west coast going south
  [0.08, 0.16],  // BC lower
  [0.11, 0.26],  // BCS upper — La Paz latitude
  [0.15, 0.37],  // BCS mid
  [0.15, 0.43],  // Cabo San Lucas
  [0.13, 0.40],  // Pacific side going back north
  [0.10, 0.33],  // BCS Pacific coast
  [0.07, 0.22],  // BC Pacific lower
  [0.05, 0.12],  // BC Pacific mid
  [0.04, 0.06],  // BC Pacific upper
  [0.05, 0.03],  // Close — back to border
];
