// Emotion contagion matrix — frontend visual distribution for satellite nodes.
// Values tuned for cluster COLOR DOMINANCE: 70% primary so each cluster reads
// as one dominant hue from a distance. Backend contagion.py uses original values.
//
// Distribution: primary 0.70, secondary 0.15, tertiary 0.08, others 0.035 each.
const CONTAGION_MATRIX = {
  anger:   { anger: 0.70, fear: 0.15, sadness: 0.08, joy: 0.035, hope: 0.035 },
  joy:     { joy:   0.70, hope: 0.15, sadness: 0.08, anger: 0.035, fear: 0.035 },
  fear:    { fear:  0.70, sadness: 0.15, anger: 0.08, hope: 0.035, joy: 0.035 },
  hope:    { hope:  0.70, joy:  0.15, anger: 0.08, fear: 0.035, sadness: 0.035 },
  sadness: { sadness: 0.70, fear: 0.15, anger: 0.08, joy: 0.035, hope: 0.035 },
};
