"""
Mock news headlines used as fallback when all RSS sources fail
or when running in mock/development mode.
"""
from datetime import datetime, timezone, timedelta


def _mins_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=n)).isoformat()


MOCK_HEADLINES: list[dict] = [
    {
        "headline": "Dólar alcanza nuevo máximo histórico frente al peso mexicano",
        "source": "El Universal",
        "url": "",
        "timestamp": _mins_ago(8),
        "sentiment": {"emotion": "anger", "intensity": 0.82, "affected_states": ["CDMX", "NL", "JAL"]},
    },
    {
        "headline": "Sismo de magnitud 5.2 sacude la Ciudad de México; no se reportan daños graves",
        "source": "Milenio",
        "url": "",
        "timestamp": _mins_ago(22),
        "sentiment": {"emotion": "fear", "intensity": 0.75, "affected_states": ["CDMX", "MEX", "MOR"]},
    },
    {
        "headline": "México clasifica a cuartos de final de la Copa América tras golazo en el último minuto",
        "source": "Récord",
        "url": "",
        "timestamp": _mins_ago(45),
        "sentiment": {"emotion": "joy", "intensity": 0.92, "affected_states": []},
    },
    {
        "headline": "Huracán categoría 4 se intensifica en el Pacífico; alertas en Guerrero y Jalisco",
        "source": "Proceso",
        "url": "",
        "timestamp": _mins_ago(67),
        "sentiment": {"emotion": "fear", "intensity": 0.88, "affected_states": ["GRO", "JAL", "COL"]},
    },
    {
        "headline": "Gobierno anuncia aumento del salario mínimo para el próximo año",
        "source": "Animal Político",
        "url": "",
        "timestamp": _mins_ago(90),
        "sentiment": {"emotion": "hope", "intensity": 0.70, "affected_states": []},
    },
    {
        "headline": "Balacera en Culiacán deja varios civiles heridos; Guardia Nacional desplegada",
        "source": "Reforma",
        "url": "",
        "timestamp": _mins_ago(115),
        "sentiment": {"emotion": "sadness", "intensity": 0.85, "affected_states": ["SIN", "CHIH"]},
    },
    {
        "headline": "Sequía histórica en Nuevo León: presas al 12% de capacidad",
        "source": "Milenio",
        "url": "",
        "timestamp": _mins_ago(142),
        "sentiment": {"emotion": "fear", "intensity": 0.78, "affected_states": ["NL", "COAH", "TAM"]},
    },
    {
        "headline": "Empresas de nearshoring anuncian inversión de 15 mil mdp en Querétaro y Monterrey",
        "source": "El Economista",
        "url": "",
        "timestamp": _mins_ago(180),
        "sentiment": {"emotion": "hope", "intensity": 0.72, "affected_states": ["QRO", "NL"]},
    },
    {
        "headline": "Gasolinazo: precios de combustibles suben por segundo mes consecutivo",
        "source": "El Universal",
        "url": "",
        "timestamp": _mins_ago(210),
        "sentiment": {"emotion": "anger", "intensity": 0.80, "affected_states": []},
    },
    {
        "headline": "Día de Muertos en Oaxaca: UNESCO reconoce celebración como patrimonio de la humanidad",
        "source": "Proceso",
        "url": "",
        "timestamp": _mins_ago(260),
        "sentiment": {"emotion": "joy", "intensity": 0.75, "affected_states": ["OAX"]},
    },
]
