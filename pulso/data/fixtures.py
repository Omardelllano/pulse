"""
Mock response fixture pools for MockProvider.
Each method has 5+ distinct response variations.
All descriptions are in Spanish, code/keys in English.
"""
from datetime import datetime

# Helper: build a full 32-state emotion list
# Used to quickly construct WorldState fixtures

_BASE_TIMESTAMP = "2024-01-15T12:00:00"

# Inline contagion values to avoid circular imports at module load time
_CONTAGION = {
    "anger":   {"anger": 0.60, "fear": 0.20, "sadness": 0.10, "joy": 0.05, "hope": 0.05},
    "joy":     {"joy": 0.60, "hope": 0.20, "anger": 0.05, "fear": 0.05, "sadness": 0.10},
    "fear":    {"fear": 0.55, "sadness": 0.20, "anger": 0.15, "joy": 0.03, "hope": 0.07},
    "hope":    {"hope": 0.55, "joy": 0.25, "fear": 0.05, "sadness": 0.05, "anger": 0.10},
    "sadness": {"sadness": 0.55, "fear": 0.20, "anger": 0.10, "joy": 0.05, "hope": 0.10},
}

# All 32 state codes
_ALL_STATE_CODES = [
    "AGS", "BC", "BCS", "CAM", "CHIS", "CHIH", "CDMX", "COAH", "COL", "DUR",
    "GTO", "GRO", "HGO", "JAL", "MEX", "MICH", "MOR", "NAY", "NL", "OAX",
    "PUE", "QRO", "QROO", "SLP", "SIN", "SON", "TAB", "TAM", "TLAX", "VER",
    "YUC", "ZAC",
]

_STATES_FEAR = [
    {"state_code": "CDMX", "state_name": "Ciudad de México", "emotion": "fear", "intensity": 0.70, "description": "La capital concentra la mayor incertidumbre del país.", "wave_order": 0, "latitude": 19.4326, "longitude": -99.1332, "population_weight": 1.0},
    {"state_code": "MEX", "state_name": "Estado de México", "emotion": "fear", "intensity": 0.65, "description": "El Estado de México refleja la tensión de la capital.", "wave_order": 1, "latitude": 19.4969, "longitude": -99.6953, "population_weight": 0.9},
    {"state_code": "JAL", "state_name": "Jalisco", "emotion": "fear", "intensity": 0.55, "description": "Jalisco siente el impacto económico con preocupación.", "wave_order": 2, "latitude": 20.6595, "longitude": -103.3494, "population_weight": 0.55},
    {"state_code": "NL", "state_name": "Nuevo León", "emotion": "fear", "intensity": 0.50, "description": "El sector industrial de Nuevo León teme consecuencias.", "wave_order": 2, "latitude": 25.5922, "longitude": -99.9962, "population_weight": 0.40},
    {"state_code": "PUE", "state_name": "Puebla", "emotion": "fear", "intensity": 0.55, "description": "Puebla enfrenta incertidumbre ante los cambios.", "wave_order": 2, "latitude": 19.0414, "longitude": -98.2063, "population_weight": 0.40},
    {"state_code": "VER", "state_name": "Veracruz", "emotion": "sadness", "intensity": 0.50, "description": "Veracruz lamenta las consecuencias para su economía.", "wave_order": 3, "latitude": 19.1738, "longitude": -96.1342, "population_weight": 0.40},
    {"state_code": "GTO", "state_name": "Guanajuato", "emotion": "anger", "intensity": 0.60, "description": "Guanajuato reacciona con indignación ante la situación.", "wave_order": 2, "latitude": 21.0190, "longitude": -101.2574, "population_weight": 0.40},
    {"state_code": "CHIH", "state_name": "Chihuahua", "emotion": "fear", "intensity": 0.60, "description": "Chihuahua, en la frontera, teme el impacto inmediato.", "wave_order": 1, "latitude": 28.6330, "longitude": -106.0691, "population_weight": 0.25},
    {"state_code": "BC", "state_name": "Baja California", "emotion": "fear", "intensity": 0.65, "description": "Baja California siente directamente la presión fronteriza.", "wave_order": 1, "latitude": 30.8406, "longitude": -115.2838, "population_weight": 0.25},
    {"state_code": "TAM", "state_name": "Tamaulipas", "emotion": "fear", "intensity": 0.65, "description": "Tamaulipas, estado fronterizo, siente el impacto directo.", "wave_order": 1, "latitude": 24.2669, "longitude": -98.8363, "population_weight": 0.25},
    {"state_code": "SIN", "state_name": "Sinaloa", "emotion": "fear", "intensity": 0.55, "description": "Sinaloa teme disrupciones en su sector agrícola.", "wave_order": 2, "latitude": 25.1721, "longitude": -107.4795, "population_weight": 0.20},
    {"state_code": "SON", "state_name": "Sonora", "emotion": "fear", "intensity": 0.55, "description": "Sonora, en la frontera norte, anticipa consecuencias graves.", "wave_order": 1, "latitude": 29.2972, "longitude": -110.3309, "population_weight": 0.20},
    {"state_code": "COAH", "state_name": "Coahuila", "emotion": "fear", "intensity": 0.55, "description": "Coahuila, estado industrial, teme el impacto económico.", "wave_order": 2, "latitude": 27.0587, "longitude": -101.7068, "population_weight": 0.22},
    {"state_code": "CHIS", "state_name": "Chiapas", "emotion": "sadness", "intensity": 0.55, "description": "Chiapas ya vulnerable siente más peso sobre sus comunidades.", "wave_order": 4, "latitude": 16.7569, "longitude": -93.1292, "population_weight": 0.30},
    {"state_code": "GRO", "state_name": "Guerrero", "emotion": "anger", "intensity": 0.65, "description": "Guerrero reacciona con ira ante una situación que lo perjudica.", "wave_order": 3, "latitude": 17.4392, "longitude": -99.5451, "population_weight": 0.25},
    {"state_code": "OAX", "state_name": "Oaxaca", "emotion": "sadness", "intensity": 0.50, "description": "Oaxaca siente tristeza ante la agudización de sus carencias.", "wave_order": 4, "latitude": 17.0732, "longitude": -96.7266, "population_weight": 0.28},
    {"state_code": "MICH", "state_name": "Michoacán", "emotion": "anger", "intensity": 0.60, "description": "Michoacán reacciona con enojo ante la falta de soluciones.", "wave_order": 3, "latitude": 19.5665, "longitude": -101.7068, "population_weight": 0.30},
    {"state_code": "TAB", "state_name": "Tabasco", "emotion": "sadness", "intensity": 0.45, "description": "Tabasco siente el peso de la situación con resignación.", "wave_order": 4, "latitude": 17.8409, "longitude": -92.6189, "population_weight": 0.15},
    {"state_code": "HGO", "state_name": "Hidalgo", "emotion": "fear", "intensity": 0.45, "description": "Hidalgo teme las consecuencias para sus trabajadores migrantes.", "wave_order": 3, "latitude": 20.0911, "longitude": -98.7624, "population_weight": 0.20},
    {"state_code": "QRO", "state_name": "Querétaro", "emotion": "fear", "intensity": 0.50, "description": "Querétaro, polo industrial, teme el freno a la inversión.", "wave_order": 2, "latitude": 20.5888, "longitude": -100.3899, "population_weight": 0.18},
    {"state_code": "SLP", "state_name": "San Luis Potosí", "emotion": "sadness", "intensity": 0.45, "description": "San Luis Potosí lamenta el impacto en sus exportaciones.", "wave_order": 3, "latitude": 22.1565, "longitude": -100.9855, "population_weight": 0.20},
    {"state_code": "ZAC", "state_name": "Zacatecas", "emotion": "sadness", "intensity": 0.45, "description": "Zacatecas siente el golpe con melancolía.", "wave_order": 4, "latitude": 22.7709, "longitude": -102.5832, "population_weight": 0.12},
    {"state_code": "AGS", "state_name": "Aguascalientes", "emotion": "hope", "intensity": 0.40, "description": "Aguascalientes mantiene cierta esperanza pese a la situación.", "wave_order": 3, "latitude": 22.0000, "longitude": -102.2960, "population_weight": 0.10},
    {"state_code": "NAY", "state_name": "Nayarit", "emotion": "fear", "intensity": 0.40, "description": "Nayarit teme efectos negativos en su turismo y agricultura.", "wave_order": 4, "latitude": 21.7514, "longitude": -104.8455, "population_weight": 0.08},
    {"state_code": "COL", "state_name": "Colima", "emotion": "fear", "intensity": 0.50, "description": "Colima, pequeño pero vulnerable, siente la presión.", "wave_order": 4, "latitude": 19.1223, "longitude": -103.7249, "population_weight": 0.06},
    {"state_code": "DUR", "state_name": "Durango", "emotion": "sadness", "intensity": 0.40, "description": "Durango observa la situación con preocupación tranquila.", "wave_order": 4, "latitude": 24.0277, "longitude": -104.6532, "population_weight": 0.12},
    {"state_code": "BCS", "state_name": "Baja California Sur", "emotion": "hope", "intensity": 0.35, "description": "BCS confía en que el turismo lo mantenga a flote.", "wave_order": 5, "latitude": 25.1694, "longitude": -111.7234, "population_weight": 0.08},
    {"state_code": "MOR", "state_name": "Morelos", "emotion": "fear", "intensity": 0.55, "description": "Morelos teme la propagación de tensiones desde la capital.", "wave_order": 2, "latitude": 18.6813, "longitude": -99.1013, "population_weight": 0.15},
    {"state_code": "CAM", "state_name": "Campeche", "emotion": "sadness", "intensity": 0.40, "description": "Campeche siente el golpe en su industria petrolera.", "wave_order": 4, "latitude": 19.8301, "longitude": -90.5349, "population_weight": 0.08},
    {"state_code": "YUC", "state_name": "Yucatán", "emotion": "hope", "intensity": 0.40, "description": "Yucatán apuesta por su diversificación económica.", "wave_order": 5, "latitude": 20.7099, "longitude": -89.0943, "population_weight": 0.15},
    {"state_code": "QROO", "state_name": "Quintana Roo", "emotion": "hope", "intensity": 0.45, "description": "Quintana Roo confía en su sector turístico.", "wave_order": 5, "latitude": 19.1817, "longitude": -88.4791, "population_weight": 0.12},
    {"state_code": "TLAX", "state_name": "Tlaxcala", "emotion": "sadness", "intensity": 0.45, "description": "Tlaxcala siente la situación como una carga más.", "wave_order": 4, "latitude": 19.3182, "longitude": -98.1979, "population_weight": 0.10},
]

_STATES_JOY = [
    {"state_code": "CDMX", "state_name": "Ciudad de México", "emotion": "joy", "intensity": 0.85, "description": "La capital celebra con euforia este logro histórico.", "wave_order": 0, "latitude": 19.4326, "longitude": -99.1332, "population_weight": 1.0},
    {"state_code": "MEX", "state_name": "Estado de México", "emotion": "joy", "intensity": 0.80, "description": "El Estado de México se une a la celebración nacional.", "wave_order": 1, "latitude": 19.4969, "longitude": -99.6953, "population_weight": 0.9},
    {"state_code": "JAL", "state_name": "Jalisco", "emotion": "joy", "intensity": 0.75, "description": "Jalisco celebra con orgullo este momento.", "wave_order": 1, "latitude": 20.6595, "longitude": -103.3494, "population_weight": 0.55},
    {"state_code": "NL", "state_name": "Nuevo León", "emotion": "hope", "intensity": 0.70, "description": "Nuevo León ve oportunidades en este acontecimiento.", "wave_order": 2, "latitude": 25.5922, "longitude": -99.9962, "population_weight": 0.40},
    {"state_code": "PUE", "state_name": "Puebla", "emotion": "joy", "intensity": 0.70, "description": "Puebla participa en la alegría colectiva.", "wave_order": 2, "latitude": 19.0414, "longitude": -98.2063, "population_weight": 0.40},
    {"state_code": "VER", "state_name": "Veracruz", "emotion": "joy", "intensity": 0.65, "description": "Veracruz celebra desde su tradición festiva.", "wave_order": 2, "latitude": 19.1738, "longitude": -96.1342, "population_weight": 0.40},
    {"state_code": "GTO", "state_name": "Guanajuato", "emotion": "hope", "intensity": 0.65, "description": "Guanajuato siente esperanza renovada ante este suceso.", "wave_order": 2, "latitude": 21.0190, "longitude": -101.2574, "population_weight": 0.40},
    {"state_code": "CHIH", "state_name": "Chihuahua", "emotion": "joy", "intensity": 0.60, "description": "Chihuahua se suma a la celebración nacional.", "wave_order": 3, "latitude": 28.6330, "longitude": -106.0691, "population_weight": 0.25},
    {"state_code": "BC", "state_name": "Baja California", "emotion": "hope", "intensity": 0.60, "description": "Baja California celebra con esperanza en el futuro.", "wave_order": 3, "latitude": 30.8406, "longitude": -115.2838, "population_weight": 0.25},
    {"state_code": "TAM", "state_name": "Tamaulipas", "emotion": "joy", "intensity": 0.55, "description": "Tamaulipas celebra las buenas noticias para la región.", "wave_order": 3, "latitude": 24.2669, "longitude": -98.8363, "population_weight": 0.25},
    {"state_code": "SIN", "state_name": "Sinaloa", "emotion": "joy", "intensity": 0.60, "description": "Sinaloa festeja con sus tradiciones y calidez.", "wave_order": 3, "latitude": 25.1721, "longitude": -107.4795, "population_weight": 0.20},
    {"state_code": "SON", "state_name": "Sonora", "emotion": "joy", "intensity": 0.55, "description": "Sonora recibe las buenas noticias con optimismo.", "wave_order": 3, "latitude": 29.2972, "longitude": -110.3309, "population_weight": 0.20},
    {"state_code": "COAH", "state_name": "Coahuila", "emotion": "hope", "intensity": 0.60, "description": "Coahuila ve en esto una oportunidad de crecimiento.", "wave_order": 2, "latitude": 27.0587, "longitude": -101.7068, "population_weight": 0.22},
    {"state_code": "CHIS", "state_name": "Chiapas", "emotion": "hope", "intensity": 0.60, "description": "Chiapas espera que este evento traiga mejoras a su gente.", "wave_order": 4, "latitude": 16.7569, "longitude": -93.1292, "population_weight": 0.30},
    {"state_code": "GRO", "state_name": "Guerrero", "emotion": "hope", "intensity": 0.55, "description": "Guerrero siente esperanza de que las cosas mejoren.", "wave_order": 4, "latitude": 17.4392, "longitude": -99.5451, "population_weight": 0.25},
    {"state_code": "OAX", "state_name": "Oaxaca", "emotion": "joy", "intensity": 0.65, "description": "Oaxaca celebra con su rica tradición cultural.", "wave_order": 3, "latitude": 17.0732, "longitude": -96.7266, "population_weight": 0.28},
    {"state_code": "MICH", "state_name": "Michoacán", "emotion": "joy", "intensity": 0.60, "description": "Michoacán celebra este momento con entusiasmo.", "wave_order": 3, "latitude": 19.5665, "longitude": -101.7068, "population_weight": 0.30},
    {"state_code": "TAB", "state_name": "Tabasco", "emotion": "joy", "intensity": 0.65, "description": "Tabasco celebra con orgullo este triunfo nacional.", "wave_order": 3, "latitude": 17.8409, "longitude": -92.6189, "population_weight": 0.15},
    {"state_code": "HGO", "state_name": "Hidalgo", "emotion": "hope", "intensity": 0.55, "description": "Hidalgo ve posibilidades de mejora para sus comunidades.", "wave_order": 4, "latitude": 20.0911, "longitude": -98.7624, "population_weight": 0.20},
    {"state_code": "QRO", "state_name": "Querétaro", "emotion": "joy", "intensity": 0.70, "description": "Querétaro, dinámico y moderno, celebra con optimismo.", "wave_order": 2, "latitude": 20.5888, "longitude": -100.3899, "population_weight": 0.18},
    {"state_code": "SLP", "state_name": "San Luis Potosí", "emotion": "joy", "intensity": 0.60, "description": "San Luis Potosí se une a la celebración colectiva.", "wave_order": 3, "latitude": 22.1565, "longitude": -100.9855, "population_weight": 0.20},
    {"state_code": "ZAC", "state_name": "Zacatecas", "emotion": "joy", "intensity": 0.55, "description": "Zacatecas celebra con sus costumbres y tradiciones.", "wave_order": 4, "latitude": 22.7709, "longitude": -102.5832, "population_weight": 0.12},
    {"state_code": "AGS", "state_name": "Aguascalientes", "emotion": "joy", "intensity": 0.65, "description": "Aguascalientes, fiel a su espíritu festivo, celebra.", "wave_order": 3, "latitude": 22.0000, "longitude": -102.2960, "population_weight": 0.10},
    {"state_code": "NAY", "state_name": "Nayarit", "emotion": "joy", "intensity": 0.60, "description": "Nayarit celebra en sus playas y comunidades.", "wave_order": 4, "latitude": 21.7514, "longitude": -104.8455, "population_weight": 0.08},
    {"state_code": "COL", "state_name": "Colima", "emotion": "joy", "intensity": 0.60, "description": "Colima celebra con la calidez característica del occidente.", "wave_order": 4, "latitude": 19.1223, "longitude": -103.7249, "population_weight": 0.06},
    {"state_code": "DUR", "state_name": "Durango", "emotion": "hope", "intensity": 0.55, "description": "Durango espera que este evento traiga prosperidad.", "wave_order": 4, "latitude": 24.0277, "longitude": -104.6532, "population_weight": 0.12},
    {"state_code": "BCS", "state_name": "Baja California Sur", "emotion": "joy", "intensity": 0.65, "description": "BCS celebra entre el mar y el desierto.", "wave_order": 4, "latitude": 25.1694, "longitude": -111.7234, "population_weight": 0.08},
    {"state_code": "MOR", "state_name": "Morelos", "emotion": "joy", "intensity": 0.70, "description": "Morelos se contagia de la alegría de la capital.", "wave_order": 2, "latitude": 18.6813, "longitude": -99.1013, "population_weight": 0.15},
    {"state_code": "CAM", "state_name": "Campeche", "emotion": "hope", "intensity": 0.55, "description": "Campeche celebra con esperanza en el desarrollo de su región.", "wave_order": 4, "latitude": 19.8301, "longitude": -90.5349, "population_weight": 0.08},
    {"state_code": "YUC", "state_name": "Yucatán", "emotion": "joy", "intensity": 0.70, "description": "Yucatán celebra desde su rica identidad cultural.", "wave_order": 3, "latitude": 20.7099, "longitude": -89.0943, "population_weight": 0.15},
    {"state_code": "QROO", "state_name": "Quintana Roo", "emotion": "joy", "intensity": 0.70, "description": "Quintana Roo, turístico y vibrante, celebra el momento.", "wave_order": 3, "latitude": 19.1817, "longitude": -88.4791, "population_weight": 0.12},
    {"state_code": "TLAX", "state_name": "Tlaxcala", "emotion": "joy", "intensity": 0.65, "description": "Tlaxcala celebra con su cultura milenaria.", "wave_order": 3, "latitude": 19.3182, "longitude": -98.1979, "population_weight": 0.10},
]


def _make_full_spread(dominant_emotion: str) -> dict:
    """Build a spread matrix for all 32 states from inline contagion values."""
    matrix = {}
    for code in _ALL_STATE_CODES:
        matrix[code] = dict(_CONTAGION[dominant_emotion])
    return matrix


# 5 base state variations
BASE_STATE_POOL = [
    {
        "timestamp": "2024-01-15T08:00:00",
        "event_text": "",
        "event_source": "base",
        "states": _STATES_FEAR,
        "spread_matrix": _make_full_spread("fear"),
        "metadata": {"variation": 0, "label": "base_fear_morning"},
    },
    {
        "timestamp": "2024-01-15T12:00:00",
        "event_text": "",
        "event_source": "base",
        "states": _STATES_JOY,
        "spread_matrix": _make_full_spread("joy"),
        "metadata": {"variation": 1, "label": "base_joy_midday"},
    },
    {
        "timestamp": "2024-01-15T16:00:00",
        "event_text": "",
        "event_source": "base",
        "states": [dict(s, emotion="sadness", intensity=round(s["intensity"] * 0.9, 2), description="La tarde trae reflexión y cierta melancolía al país.") for s in _STATES_FEAR],
        "spread_matrix": _make_full_spread("sadness"),
        "metadata": {"variation": 2, "label": "base_sadness_afternoon"},
    },
    {
        "timestamp": "2024-01-15T20:00:00",
        "event_text": "",
        "event_source": "base",
        "states": [dict(s, emotion="hope" if s["emotion"] == "joy" else s["emotion"], description="La noche trae esperanza renovada para el país.") for s in _STATES_JOY],
        "spread_matrix": _make_full_spread("hope"),
        "metadata": {"variation": 3, "label": "base_hope_evening"},
    },
    {
        "timestamp": "2024-01-16T08:00:00",
        "event_text": "",
        "event_source": "base",
        "states": [dict(s, emotion="anger", intensity=round(min(1.0, s["intensity"] * 1.1), 2), description="El nuevo día comienza con tensión en el ambiente político.") for s in _STATES_FEAR],
        "spread_matrix": _make_full_spread("anger"),
        "metadata": {"variation": 4, "label": "base_anger_morning"},
    },
]

# 5+ event simulation response variations
EVENT_RESPONSE_POOL = [
    {
        "event_key": "dolar_sube",
        "timestamp": "2024-01-15T14:00:00",
        "event_text": "El dólar sube a 22 pesos",
        "event_source": "user",
        "states": _STATES_FEAR,
        "spread_matrix": _make_full_spread("fear"),
        "metadata": {"variation": 0, "event_type": "economy"},
    },
    {
        "event_key": "seleccion_gana",
        "timestamp": "2024-01-15T22:00:00",
        "event_text": "México gana el Mundial de Fútbol",
        "event_source": "user",
        "states": _STATES_JOY,
        "spread_matrix": _make_full_spread("joy"),
        "metadata": {"variation": 1, "event_type": "sports"},
    },
    {
        "event_key": "sismo",
        "timestamp": "2024-01-15T10:00:00",
        "event_text": "Sismo de magnitud 7.2 sacude la Ciudad de México",
        "event_source": "user",
        "states": [dict(s, emotion="fear", intensity=min(1.0, round(s["intensity"] + 0.2, 2)), description="El temblor sacude los cimientos y los corazones del país.") for s in _STATES_FEAR],
        "spread_matrix": _make_full_spread("fear"),
        "metadata": {"variation": 2, "event_type": "disaster"},
    },
    {
        "event_key": "reforma_educativa",
        "timestamp": "2024-01-15T09:00:00",
        "event_text": "Gobierno anuncia reforma educativa histórica",
        "event_source": "user",
        "states": [
            dict(s, emotion="hope", intensity=0.6, description="La reforma genera esperanza en el futuro educativo del país.")
            if i % 2 == 0 else
            dict(s, emotion="anger", intensity=0.55, description="Algunos sectores rechazan la reforma con indignación.")
            for i, s in enumerate(_STATES_FEAR)
        ],
        "spread_matrix": _make_full_spread("hope"),
        "metadata": {"variation": 3, "event_type": "politics"},
    },
    {
        "event_key": "desabasto_agua",
        "timestamp": "2024-01-15T11:00:00",
        "event_text": "Crisis de agua en varias ciudades del norte",
        "event_source": "user",
        "states": [
            dict(s, emotion="anger" if s["state_code"] in ["NL", "CHIH", "SON", "COAH", "TAM", "BC"] else "sadness",
                 intensity=0.70 if s["state_code"] in ["NL", "CHIH", "SON", "COAH"] else 0.50,
                 description="La escasez de agua desata ira en los estados afectados.")
            for s in _STATES_FEAR
        ],
        "spread_matrix": _make_full_spread("anger"),
        "metadata": {"variation": 4, "event_type": "environment"},
    },
    {
        "event_key": "aumento_salario",
        "timestamp": "2024-01-15T13:00:00",
        "event_text": "Anuncian aumento histórico al salario mínimo",
        "event_source": "user",
        "states": [dict(s, emotion="joy", intensity=0.65, description="El aumento salarial genera alivio y optimismo en los trabajadores.") for s in _STATES_JOY],
        "spread_matrix": _make_full_spread("joy"),
        "metadata": {"variation": 5, "event_type": "economy"},
    },
]

# 5+ news sentiment variations
NEWS_SENTIMENT_POOL = [
    {"emotion": "fear", "affected_states": ["CDMX", "MEX", "JAL", "NL"], "intensity": 0.6, "decay_hours": 6.0},
    {"emotion": "anger", "affected_states": ["GTO", "MICH", "GRO", "OAX", "CHIS"], "intensity": 0.7, "decay_hours": 8.0},
    {"emotion": "joy", "affected_states": ["CDMX", "JAL", "NL", "QRO", "YUC", "QROO"], "intensity": 0.8, "decay_hours": 4.0},
    {"emotion": "sadness", "affected_states": ["VER", "TAB", "CAM", "OAX", "CHIS", "GRO"], "intensity": 0.5, "decay_hours": 10.0},
    {"emotion": "hope", "affected_states": ["NL", "QRO", "AGS", "BC", "SON"], "intensity": 0.65, "decay_hours": 5.0},
    {"emotion": "fear", "affected_states": ["BC", "SON", "CHIH", "COAH", "TAM"], "intensity": 0.75, "decay_hours": 7.0},
]

# 5 moderation result variations
MODERATION_POOL = [
    {"valid": True, "reason": None},
    {"valid": True, "reason": None},
    {"valid": True, "reason": None},
    {"valid": False, "reason": "Contenido no relacionado con México o eventos actuales."},
    {"valid": False, "reason": "Texto demasiado vago para generar una simulación útil."},
]

# 5 consistency check variations
CONSISTENCY_POOL = [
    {"status": "consistent", "adjustments": []},
    {"status": "adjusted", "adjustments": [{"state_code": "CDMX", "intensity_delta": -0.1}]},
    {"status": "adjusted", "adjustments": [{"state_code": "GRO", "intensity_delta": 0.05}, {"state_code": "CHIS", "intensity_delta": 0.05}]},
    {"status": "consistent", "adjustments": []},
    {"status": "adjusted", "adjustments": [{"state_code": "NL", "intensity_delta": -0.05}, {"state_code": "JAL", "intensity_delta": -0.05}]},
]
