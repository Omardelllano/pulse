"""
Emotion contagion matrix for PULSO.
Defines how emotions spread from major nodes to satellite nodes.
Matches Section 5.3 of the master briefing exactly.
"""

CONTAGION_MATRIX = {
    "anger":   {"anger": 0.60, "fear": 0.20, "sadness": 0.10, "joy": 0.05, "hope": 0.05},
    "joy":     {"joy": 0.60, "hope": 0.20, "anger": 0.05, "fear": 0.05, "sadness": 0.10},
    "fear":    {"fear": 0.55, "sadness": 0.20, "anger": 0.15, "joy": 0.03, "hope": 0.07},
    "hope":    {"hope": 0.55, "joy": 0.25, "fear": 0.05, "sadness": 0.05, "anger": 0.10},
    "sadness": {"sadness": 0.55, "fear": 0.20, "anger": 0.10, "joy": 0.05, "hope": 0.10},
}
