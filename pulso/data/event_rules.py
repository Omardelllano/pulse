"""
EVENT_RULES: Keyword → emotion mapping for PULSO keyword simulator.
28 categories covering major event types in Mexico.
Matches Section 7.1 of the master briefing.

Matching rules:
- Keywords are compared after accent-stripping + lowercasing.
- Multi-word keywords checked as substrings.
- Scoring: (hit_count, longest_matched_kw_len, intensity) — all descending.
- Duplicate normalized forms are deduplicated before scoring.
"""

EVENT_RULES = [

    # ── Sports: national team joy ──────────────────────────────────────────────
    {
        "keywords": [
            "gol", "mundial", "selección", "seleccion", "futbol", "fútbol",
            "tri", "copa del mundo", "copa", "campeón", "campeon", "gana mexico",
            "gana méxico", "ganamos", "clasificó", "clasico", "olimpiadas",
            "medalla de oro", "medalla",
        ],
        "emotion": "joy",
        "intensity": 0.90,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Euforia deportiva nacional",
    },

    # ── Sports: club teams (Liga MX) ───────────────────────────────────────────
    {
        "keywords": [
            "chivas", "américa", "america", "cruz azul", "pumas", "tigres",
            "santos", "rayados", "liga mx", "liguilla", "clausura", "apertura",
            "clásico nacional", "clasico nacional", "superclásico", "superclasico",
        ],
        "emotion": "joy",
        "intensity": 0.82,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Pasión por el futbol de clubes",
    },

    # ── Sports: boxing & other sports ─────────────────────────────────────────
    {
        "keywords": [
            "canelo", "boxeo", "campeonato mundial", "oro olimpico", "plata olimpica",
            "bronce olimpico", "atletismo", "beisbol", "nba mexico", "formula 1",
            "gran premio", "autodromo",
        ],
        "emotion": "joy",
        "intensity": 0.80,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Logro deportivo nacional",
    },

    # ── Sports: defeat / elimination ───────────────────────────────────────────
    {
        "keywords": [
            "pierde mexico", "pierde méxico", "eliminado", "eliminados",
            "eliminada", "eliminadas", "elimino", "derrota de mexico",
            "derrota", "perdimos", "nos eliminaron", "quedamos fuera",
            "adios mundial", "adiós mundial", "fracaso deportivo",
            "no clasifica", "seleccion", "selección",
        ],
        "emotion": "sadness",
        "intensity": 0.82,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Decepción deportiva nacional",
    },

    # ── Economy: dollar / exchange rate ───────────────────────────────────────
    {
        "keywords": [
            "dólar", "dolar", "tipo de cambio", "devaluación", "devaluacion",
            "divisa", "peso mexicano", "remesas", "reservas internacionales",
        ],
        "emotion": "anger",
        "intensity": 0.85,
        "epicenter_states": ["CDMX", "NL", "JAL"],
        "wave_origin": "CDMX",
        "joy_states": ["BC", "SON", "CHIH", "TAM"],  # border states benefit from strong dollar
        "description_template": "Reacción al movimiento del tipo de cambio",
    },

    # ── Economy: inflation / cost of living ───────────────────────────────────
    {
        "keywords": [
            "inflación", "inflacion", "carestía", "carestia", "caro", "precios suben",
            "canasta básica", "canasta basica", "impuestos", "iva", "isr",
            "aumento de precios", "costo de vida", "poder adquisitivo",
        ],
        "emotion": "anger",
        "intensity": 0.80,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Presión inflacionaria afecta el bolsillo",
    },

    # ── Economy: recession / unemployment ─────────────────────────────────────
    {
        "keywords": [
            "recesión", "recesion", "crisis económica", "crisis economica",
            "desempleo", "desocupación", "desocupacion", "despido", "despidos masivos",
            "recorte de personal", "quiebra", "bancarrota", "cierre de empresa",
            "paro laboral", "empleo", "trabajo",
        ],
        "emotion": "sadness",
        "intensity": 0.78,
        "epicenter_states": ["CDMX", "NL", "JAL", "MEX"],
        "wave_origin": "CDMX",
        "description_template": "Impacto en el empleo y la economía",
    },

    # ── Economy: investment / growth ──────────────────────────────────────────
    {
        "keywords": [
            "inversión", "inversion", "crecimiento económico", "crecimiento",
            "nearshoring", "tesla", "bmw", "volkswagen", "fabrica nueva",
            "fábrica nueva", "planta nueva", "pib crece", "economía crece",
            "economia crece", "exportaciones crecen", "tratado comercial", "t-mec",
        ],
        "emotion": "hope",
        "intensity": 0.72,
        "epicenter_states": ["CDMX", "NL", "JAL", "QRO"],
        "wave_origin": "CDMX",
        "description_template": "Señales de crecimiento e inversión",
    },

    # ── Economy: wages / consumer spending ────────────────────────────────────
    {
        "keywords": [
            "salario mínimo", "salario minimo", "salario sube", "aumento salarial",
            "buen fin", "exportaciones", "aguinaldo", "reparto de utilidades", "ptu",
        ],
        "emotion": "hope",
        "intensity": 0.68,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Mejora en ingresos y consumo",
    },

    # ── Natural disasters: earthquake ─────────────────────────────────────────
    {
        "keywords": [
            "temblor", "sismo", "terremoto", "richter", "alerta sísmica",
            "alerta sismica", "epicentro", "réplica", "replica sísmica",
        ],
        "emotion": "fear",
        "intensity": 0.95,
        "epicenter_states": ["CDMX", "OAX", "GRO", "CHIS", "PUE", "MOR"],
        "wave_origin": "CDMX",
        "description_template": "Alerta sísmica activa",
    },

    # ── Natural disasters: volcano / tsunami ──────────────────────────────────
    {
        "keywords": [
            "popocatépetl", "popocatepetl", "volcán", "volcan", "erupción",
            "erupcion", "lava", "ceniza volcánica", "ceniza volcanica",
            "tsunami", "maremoto",
        ],
        "emotion": "fear",
        "intensity": 0.92,
        "epicenter_states": ["PUE", "MEX", "MOR", "CDMX", "OAX"],
        "wave_origin": "PUE",
        "description_template": "Alerta por actividad volcánica",
    },

    # ── Weather: hurricane / tropical storm ───────────────────────────────────
    {
        "keywords": [
            "huracán", "huracan", "tormenta tropical", "ciclón", "ciclon",
            "depresión tropical", "depresion tropical", "categoria 5", "categoria 4",
            "alerta de huracán", "alerta de huracan",
        ],
        "emotion": "fear",
        "intensity": 0.88,
        "epicenter_states": ["TAM", "VER", "TAB", "CAM", "QROO", "GRO", "SIN", "NAY"],
        "wave_origin": "VER",
        "description_template": "Emergencia por huracán",
    },

    # ── Weather: floods / severe rain ─────────────────────────────────────────
    {
        "keywords": [
            "inundación", "inundacion", "desbordamiento", "tromba", "granizo",
            "tornado", "lluvia torrencial", "lluvias intensas", "alerta roja",
            "zona de desastre",
        ],
        "emotion": "fear",
        "intensity": 0.82,
        "epicenter_states": ["TAB", "VER", "GRO", "OAX", "CHIS"],
        "wave_origin": "VER",
        "description_template": "Emergencia meteorológica severa",
    },

    # ── Drought / water crisis ────────────────────────────────────────────────
    {
        "keywords": [
            "sequía", "sequia", "presa", "escasez de agua", "día cero",
            "dia cero", "corte de agua", "desabasto de agua", "desabasto",
            "racionamiento", "acuífero", "cuenca",
        ],
        "emotion": "fear",
        "intensity": 0.78,
        "epicenter_states": ["NL", "CHIH", "SON", "DUR", "CDMX"],
        "wave_origin": "NL",
        "description_template": "Crisis hídrica",
    },

    # ── Crime: organized crime / narco ────────────────────────────────────────
    {
        "keywords": [
            "narco", "narcotráfico", "narcotrafico", "cártel", "cartel",
            "balacera", "ejecución", "ejecucion", "levantón", "levanton",
            "narcomenudeo", "plaza", "sicario", "plaza controlada",
        ],
        "emotion": "sadness",
        "intensity": 0.88,
        "epicenter_states": ["CHIH", "SIN", "TAM", "GRO", "MICH", "ZAC"],
        "wave_origin": "CHIH",
        "fear_states": ["CDMX", "JAL", "NL"],
        "description_template": "Crisis de seguridad por crimen organizado",
    },

    # ── Crime: violence / kidnapping / femicide ───────────────────────────────
    {
        "keywords": [
            "secuestro", "inseguridad", "feminicidio", "feminicidios",
            "desaparecida", "desaparecido", "desaparecidas", "desaparecidos",
            "extorsión", "extorsion", "homicidio", "asesinato", "violencia",
            "crimen", "delincuencia",
        ],
        "emotion": "sadness",
        "intensity": 0.85,
        "epicenter_states": ["CHIH", "SIN", "TAM", "GRO", "MICH", "ZAC"],
        "wave_origin": "CHIH",
        "fear_states": ["CDMX", "JAL", "NL"],
        "description_template": "Violencia e inseguridad afectan a la población",
    },

    # ── War / military conflict ───────────────────────────────────────────────
    {
        "keywords": [
            "bomba", "nuclear", "guerra", "ataque militar", "invasión",
            "invasion", "misil", "ejército atacó", "ejercito ataco",
            "terrorismo", "terrorista", "atentado", "conflicto armado",
        ],
        "emotion": "fear",
        "intensity": 0.98,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Amenaza de conflicto bélico",
    },

    # ── Politics: corruption / scandal ────────────────────────────────────────
    {
        "keywords": [
            "corrupción", "corrupcion", "fraude electoral", "robo al erario",
            "escándalo", "escandalo", "desvío de fondos", "desvio de fondos",
            "moches", "impunidad", "abuso de poder", "enriquecimiento ilícito",
            "enriquecimiento ilicito", "nepotismo", "soborno",
        ],
        "emotion": "anger",
        "intensity": 0.78,
        "epicenter_states": ["CDMX"],
        "wave_origin": "CDMX",
        "description_template": "Indignación por corrupción política",
    },

    # ── Politics: legislation / reform ────────────────────────────────────────
    {
        "keywords": [
            "constitución", "constitucion", "reforma constitucional",
            "reforma", "ley aprobada", "aprobaron", "senado aprobó",
            "senado aprobo", "diputados aprobaron", "decreto presidencial",
            "autoritarismo", "censura", "dictadura",
        ],
        "emotion": "anger",
        "intensity": 0.72,
        "epicenter_states": ["CDMX"],
        "wave_origin": "CDMX",
        "description_template": "Cambio legislativo o político",
    },

    # ── Elections ─────────────────────────────────────────────────────────────
    {
        "keywords": [
            "elecciones", "elección federal", "eleccion federal",
            "voto", "votar", "candidato presidencial", "candidata presidencial",
            "presidente electo", "gobernador electo", "campaña electoral",
            "ine", "tribunal electoral", "casilla", "urna",
        ],
        "emotion": "anger",
        "intensity": 0.70,
        "epicenter_states": ["CDMX", "NL", "JAL"],
        "wave_origin": "CDMX",
        "description_template": "Tensión electoral",
    },

    # ── Celebration / national holidays ───────────────────────────────────────
    {
        "keywords": [
            "navidad", "año nuevo", "ano nuevo", "día de muertos", "dia de muertos",
            "grito de independencia", "grito", "15 de septiembre", "16 de septiembre",
            "guadalupe", "12 de diciembre", "posada", "carnaval", "feria",
            "quinceañera", "boda", "fiesta nacional", "celebración", "celebracion",
            "festejo",
        ],
        "emotion": "joy",
        "intensity": 0.85,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Festividad y celebración nacional",
    },

    # ── Health crisis / epidemic ──────────────────────────────────────────────
    {
        "keywords": [
            "covid", "pandemia", "virus", "contagio", "vacuna", "epidemia",
            "dengue", "influenza", "gripe aviar", "emergencia sanitaria",
            "cuarentena", "brote", "ómicron", "omicron",
        ],
        "emotion": "fear",
        "intensity": 0.80,
        "epicenter_states": ["CDMX", "NL", "JAL", "BC"],
        "wave_origin": "CDMX",
        "description_template": "Alerta sanitaria",
    },

    # ── Energy / gasoline / electricity ───────────────────────────────────────
    {
        "keywords": [
            "gasolina", "gasolinazo", "combustible", "petróleo", "petroleo",
            "pemex", "luz eléctrica", "luz electrica", "cfe", "apagón",
            "apagon", "tarifa eléctrica", "tarifa electrica", "gas lp",
            "gas natural", "precio del gas",
        ],
        "emotion": "anger",
        "intensity": 0.82,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Impacto en precios de energía",
    },

    # ── Migration / border ────────────────────────────────────────────────────
    {
        "keywords": [
            "migrante", "migrantes", "migración", "migracion",
            "deportación", "deportacion", "deportados", "frontera",
            "muro fronterizo", "visa", "caravana migrante", "caravana",
            "refugiado", "refugiados", "asilo",
        ],
        "emotion": "sadness",
        "intensity": 0.72,
        "epicenter_states": ["CHIS", "TAM", "BC", "SON", "CHIH"],
        "wave_origin": "CHIS",
        "description_template": "Crisis migratoria en la frontera",
    },

    # ── Technology / internet outages ─────────────────────────────────────────
    {
        "keywords": [
            "se cayó internet", "se cayo internet", "whatsapp caído", "whatsapp caido",
            "whatsapp", "tiktok", "facebook caído", "facebook caido",
            "hackeo masivo", "hackeo", "ciberataque", "falla del sistema",
            "se cayó", "se cayo",
        ],
        "emotion": "anger",
        "intensity": 0.55,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Falla tecnológica masiva",
    },

    # ── Education ─────────────────────────────────────────────────────────────
    {
        "keywords": [
            "unam", "ipn", "politécnico", "politecnico", "beca", "becas",
            "regreso a clases", "ciclo escolar", "educación pública",
            "educacion publica", "maestros", "huelga de maestros",
            "cnte", "universidades", "bachillerato",
        ],
        "emotion": "hope",
        "intensity": 0.60,
        "epicenter_states": ["CDMX", "NL", "JAL"],
        "wave_origin": "CDMX",
        "description_template": "Noticias del sector educativo",
    },

    # ── Transportation / traffic / strikes ────────────────────────────────────
    {
        "keywords": [
            "tráfico", "trafico", "metro cdmx", "metro", "transporte público",
            "transporte publico", "bloqueo carretero", "bloqueo", "paro de transportistas",
            "huelga", "aeropuerto cerrado", "vuelo cancelado", "choque en",
            "accidente vial",
        ],
        "emotion": "anger",
        "intensity": 0.62,
        "epicenter_states": ["CDMX", "NL", "JAL"],
        "wave_origin": "CDMX",
        "description_template": "Caos en el transporte",
    },

    # ── National pride / achievement ──────────────────────────────────────────
    {
        "keywords": [
            "orgullo mexicano", "orgullo", "logro histórico", "logro historico",
            "premio nobel", "premio", "astronauta mexicano", "mexicano destaca",
            "mexicana destaca", "récord mundial", "record mundial",
            "descubrimiento científico", "descubrimiento cientifico",
            "innovación mexicana", "innovacion mexicana", "reconocimiento internacional",
            "descubrimiento", "innovación", "innovacion",
        ],
        "emotion": "hope",
        "intensity": 0.75,
        "epicenter_states": ["ALL"],
        "wave_origin": "CDMX",
        "description_template": "Orgullo nacional por logro destacado",
    },

    # ── Food / gastronomy ─────────────────────────────────────────────────────
    {
        "keywords": [
            "tacos", "comida mexicana", "gastronomía mexicana", "gastronomia mexicana",
            "mole", "pozole", "patrimonio gastronómico", "patrimonio gastronomico",
            "mezcal", "tequila", "estrella michelin", "michelin", "guía michelin",
            "mejor restaurante", "tortilla", "chile en nogada",
        ],
        "emotion": "joy",
        "intensity": 0.65,
        "epicenter_states": ["ALL"],
        "wave_origin": "OAX",
        "description_template": "Orgullo por la gastronomía mexicana",
    },

]

# Default rule when no keywords match (triggers LLM fallback in P2)
DEFAULT_RULE = {
    "emotion": "fear",
    "intensity": 0.50,
    "epicenter_states": ["CDMX"],
    "wave_origin": "CDMX",
    "description_template": "Evento no categorizado",
}
