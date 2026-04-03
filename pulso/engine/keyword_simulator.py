"""
KeywordSimulator: Generates WorldState from user text using keyword matching.
No LLM calls — uses predefined EVENT_RULES. Free and instant.
Matches Section 7.1-7.2 of the master briefing.
"""
import math
import unicodedata
from collections import Counter
from datetime import datetime

from pulso.data.event_rules import EVENT_RULES, DEFAULT_RULE
from pulso.data.mexico_states import MEXICO_STATES
from pulso.data.contagion import CONTAGION_MATRIX
from pulso.models.schemas import WorldState, StateEmotion, Emotion, EmotionSpread


# Geographic adjacency — states considered "neighbors" for wave_order
_NEIGHBORS: dict[str, list[str]] = {
    "AGS":  ["JAL", "ZAC", "SLP"],
    "BC":   ["SON", "BCS"],
    "BCS":  ["BC", "SON", "SIN"],
    "CAM":  ["TAB", "QROO", "YUC"],
    "CHIS": ["OAX", "TAB", "GRO"],
    "CHIH": ["SON", "SIN", "DUR", "COAH"],
    "CDMX": ["MEX", "MOR", "HGO"],
    "COAH": ["CHIH", "DUR", "ZAC", "SLP", "NL", "TAM"],
    "COL":  ["JAL", "MICH"],
    "DUR":  ["CHIH", "SIN", "NAY", "ZAC", "COAH"],
    "GTO":  ["JAL", "SLP", "QRO", "HGO", "MICH", "AGS", "ZAC"],
    "GRO":  ["MEX", "MOR", "PUE", "OAX", "MICH"],
    "HGO":  ["SLP", "VER", "PUE", "TLX", "MEX", "QRO"],
    "JAL":  ["NAY", "ZAC", "AGS", "GTO", "MICH", "COL"],
    "MEX":  ["CDMX", "HGO", "QRO", "GTO", "MICH", "GRO", "MOR", "PUE", "TLX"],
    "MICH": ["JAL", "GTO", "QRO", "MEX", "GRO", "COL"],
    "MOR":  ["MEX", "CDMX", "GRO", "PUE"],
    "NAY":  ["SIN", "DUR", "JAL"],
    "NL":   ["COAH", "TAM", "SLP", "ZAC"],
    "OAX":  ["PUE", "VER", "GRO", "CHIS"],
    "PUE":  ["TLX", "HGO", "VER", "OAX", "GRO", "MEX", "MOR"],
    "QRO":  ["GTO", "SLP", "HGO", "MEX", "MICH"],
    "QROO": ["YUC", "CAM"],
    "SLP":  ["ZAC", "JAL", "GTO", "QRO", "HGO", "VER", "TAM", "NL", "COAH"],
    "SIN":  ["SON", "CHIH", "DUR", "NAY", "BCS"],
    "SON":  ["BC", "BCS", "SIN", "CHIH"],
    "TAB":  ["VER", "CAM", "CHIS"],
    "TAM":  ["NL", "COAH", "SLP", "VER"],
    "TLX":  ["PUE", "HGO", "MEX"],
    "VER":  ["TAM", "SLP", "HGO", "PUE", "OAX", "CHIS", "TAB"],
    "YUC":  ["CAM", "QROO"],
    "ZAC":  ["CHIH", "DUR", "NAY", "JAL", "AGS", "SLP", "NL", "COAH", "GTO"],
}

_STATE_MAP = {s["state_code"]: s for s in MEXICO_STATES}
_ALL_CODES = [s["state_code"] for s in MEXICO_STATES]

# Default emotional baselines per state (from MEXICO_STATES data)
_DEFAULT_EMOTIONS: dict[str, str] = {
    s["state_code"]: s["default_emotion"] for s in MEXICO_STATES
}
_DEFAULT_INTENSITIES: dict[str, float] = {
    s["state_code"]: s["default_intensity"] for s in MEXICO_STATES
}

# ── Regional diversity constants ──────────────────────────────────────────────

# Economic/cultural profiles used to assign secondary emotions
_PROFILES: dict[str, set[str]] = {
    "border_usd":   {"BC", "SON", "CHIH", "TAM"},
    "oil":          {"TAB", "CAM", "VER", "TAM"},
    "vulnerable":   {"OAX", "CHIS", "GRO", "TLX", "ZAC"},
    "conservative": {"GTO", "AGS", "JAL", "QRO"},
    "agriculture":  {"SIN", "SON", "MICH", "VER", "TAB"},
    "tourism":      {"QROO", "BCS", "NAY", "OAX", "JAL"},
    "industrial":   {"NL", "COAH", "QRO", "AGS", "SLP", "GTO"},
}

# (primary_emotion, profile) → secondary_emotion
_PROFILE_SECONDARY: dict[tuple[str, str], str] = {
    # anger: who benefits or suffers differently
    ("anger",   "border_usd"):   "joy",      # peso falls → USD earners win
    ("anger",   "tourism"):      "fear",     # instability → tourism collapses
    ("anger",   "vulnerable"):   "sadness",  # poor absorb the worst shock
    ("anger",   "industrial"):   "fear",     # industry fears supply disruption
    ("anger",   "oil"):          "hope",     # oil sector sees opportunity
    # joy: who can't fully celebrate
    ("joy",     "conservative"): "hope",     # cautious optimism, not full euphoria
    ("joy",     "vulnerable"):   "sadness",  # prosperity hasn't reached them
    # fear: who turns fear into action or grief
    ("fear",    "border_usd"):   "anger",    # border communities push back
    ("fear",    "industrial"):   "anger",    # industry demands government action
    ("fear",    "tourism"):      "sadness",  # tourism sector mourns losses
    # hope: who doubts
    ("hope",    "conservative"): "fear",     # skeptical of change
    ("hope",    "vulnerable"):   "sadness",  # hope feels distant from reality
    ("hope",    "oil"):          "anger",    # fossil sector fears being left behind
    # sadness: who responds with outrage or resilience
    ("sadness", "industrial"):   "anger",    # demand accountability
    ("sadness", "tourism"):      "fear",     # economic contagion
    ("sadness", "border_usd"):   "anger",    # border workers get angry
    ("sadness", "conservative"): "hope",     # faith and resilience
}

# Fallback secondary emotions when no profile mapping exists
_SECONDARY_FALLBACK: dict[str, list[str]] = {
    "anger":   ["fear", "sadness"],
    "joy":     ["hope", "sadness"],
    "fear":    ["anger", "sadness"],
    "hope":    ["joy", "fear"],
    "sadness": ["anger", "fear"],
}

# Per-emotion contrarian profiles for nationwide (ALL-epicenter) events.
# "Contrarian" = states that react differently from the national wave.
# Vulnerable states celebrate and mourn along with everyone else (no contrarian for joy/sadness).
# Conservative states (GTO, AGS, JAL, QRO) are culturally cautious for any emotion.
_CONTRARIAN_PROFILES_BY_EMOTION: dict[str, tuple[str, ...]] = {
    "anger":   ("vulnerable", "conservative"),  # anger → vulnerable suffer most, conservative resist
    "joy":     ("conservative",),               # joy → conservative are cautiously hopeful, not ecstatic
    "fear":    ("conservative",),               # fear → conservative react with hope/denial
    "hope":    ("conservative",),               # hope → conservative are skeptical
    "sadness": ("conservative",),               # sadness → conservative show resilience/hope
}

# Maximum states that can share the same emotion (diversity gate)
_MAX_SAME_EMOTION = 20


# ── Diversity helpers ─────────────────────────────────────────────────────────

def _get_secondary_emotion(state_code: str, primary_emotion: str) -> str:
    """
    Return the appropriate secondary emotion for a state given the primary.
    Checks economic profiles first, then falls back to state's default baseline.
    """
    for profile, codes in _PROFILES.items():
        if state_code in codes:
            key = (primary_emotion, profile)
            if key in _PROFILE_SECONDARY:
                return _PROFILE_SECONDARY[key]
    # No profile mapping: use state's default only when it contrasts with primary.
    # If default == primary, return primary to signal "no meaningful alternative"
    # (caller will keep the original emotion).
    state_default = _DEFAULT_EMOTIONS.get(state_code, primary_emotion)
    return state_default if state_default != primary_emotion else primary_emotion


def apply_regional_diversity(
    state_emotions: list,
    primary_emotion: str,
    protected_codes: set,
    wave_orders: dict,
    all_epicenter: bool = False,
) -> list:
    """
    Reassign emotions for non-protected states based on economic profiles.

    For specific-epicenter events (all_epicenter=False):
        States with wave_order < 2 are protected (too close to epicenter).
        States with wave_order >= 2 get profile-based secondary emotions.

    For nationwide events (all_epicenter=True):
        Only "contrarian" profile states (vulnerable, conservative) get diversified.
        This keeps celebration events joy-dominant while adding realism.
    """
    result = []
    for se in state_emotions:
        code = se.state_code

        # Always protect explicitly overridden states and epicenter states
        if code in protected_codes:
            result.append(se)
            continue

        if all_epicenter:
            # Only diversify contrarian profiles for nationwide events (per-emotion)
            contrarian_profiles = _CONTRARIAN_PROFILES_BY_EMOTION.get(primary_emotion, ("conservative",))
            in_contrarian = any(
                code in _PROFILES.get(p, set())
                for p in contrarian_profiles
            )
            if not in_contrarian:
                result.append(se)
                continue
            # Use state's emotional baseline (muted, not full-intensity)
            new_intensity = round(
                max(0.20, min(0.50, _DEFAULT_INTENSITIES.get(code, 0.35) * 0.95)),
                3,
            )
        else:
            # Geographic events: only diversify distant states
            wave_ord = wave_orders.get(code, 5)
            if wave_ord < 2:
                result.append(se)
                continue
            # Farther = lower intensity, using baseline rather than propagated intensity
            if wave_ord >= 3:
                new_intensity = round(
                    max(0.20, min(0.45, _DEFAULT_INTENSITIES.get(code, 0.35) * 0.90)),
                    3,
                )
            else:
                # wave_order == 2: moderate reduction
                new_intensity = round(max(0.30, se.intensity * 0.75), 3)

        secondary = _get_secondary_emotion(code, primary_emotion)
        if secondary == primary_emotion:
            # No useful secondary — keep original
            result.append(se)
            continue

        result.append(se.model_copy(update={
            "emotion": Emotion(secondary),
            "intensity": new_intensity,
        }))

    return result


def ensure_diversity(state_emotions: list) -> list:
    """
    Post-processing gate: if any single emotion holds more than _MAX_SAME_EMOTION
    states, reassign the lowest-intensity offenders to secondary emotions.
    Applied after both keyword simulation and LLM results.
    """
    emotion_counts = Counter(s.emotion.value for s in state_emotions)
    dominated = [(emo, cnt) for emo, cnt in emotion_counts.items() if cnt > _MAX_SAME_EMOTION]
    if not dominated:
        return state_emotions

    result = list(state_emotions)
    for primary_emo, count in dominated:
        same_indices = sorted(
            [i for i, s in enumerate(result) if s.emotion.value == primary_emo],
            # Reassign lowest-intensity states first; within ties, most-distant first
            # (highest wave_order = farthest from epicenter = least impacted).
            key=lambda i: (result[i].intensity, -(result[i].wave_order or 0)),
        )
        to_reassign = same_indices[:count - _MAX_SAME_EMOTION]
        fallbacks = _SECONDARY_FALLBACK.get(primary_emo, ["fear", "sadness"])

        for rank, idx in enumerate(to_reassign):
            se = result[idx]
            new_emo = _get_secondary_emotion(se.state_code, primary_emo)
            if new_emo == primary_emo:
                new_emo = fallbacks[rank % len(fallbacks)]
            result[idx] = se.model_copy(update={
                "emotion": Emotion(new_emo),
                "intensity": round(max(0.25, se.intensity * 0.70), 3),
            })

    return result


# ── Wave-order computation ────────────────────────────────────────────────────

def _compute_wave_orders(origin: str) -> dict[str, int]:
    visited = {origin: 0}
    queue = [origin]
    while queue:
        current = queue.pop(0)
        for neighbor in _NEIGHBORS.get(current, []):
            if neighbor not in visited:
                visited[neighbor] = visited[current] + 1
                queue.append(neighbor)
    for code in _ALL_CODES:
        if code not in visited:
            visited[code] = 5
    return visited


def _strip_accents(text: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )


def _normalize(text: str) -> str:
    return _strip_accents(text.lower())


def _match_rule(text: str) -> tuple[dict, int]:
    """
    Match EVENT_RULES against normalized text.

    Scoring (all descending): hit_count → longest_matched_keyword_len → rule_intensity
    Deduplicates normalized keywords first so accented+bare variants aren't double-counted.
    Falls back to DEFAULT_RULE with hit_count=0.
    """
    norm = _normalize(text)
    best_rule = DEFAULT_RULE
    best_score: tuple[int, int, float] = (0, 0, 0.0)

    for rule in EVENT_RULES:
        seen: set[str] = set()
        matched_lens: list[int] = []
        for kw in rule["keywords"]:
            nkw = _normalize(kw)
            if nkw in seen:
                continue
            seen.add(nkw)
            if nkw in norm:
                matched_lens.append(len(nkw))

        hits = len(matched_lens)
        if hits == 0:
            continue

        score: tuple[int, int, float] = (hits, max(matched_lens), rule.get("intensity", 0.0))
        if score > best_score:
            best_score = score
            best_rule = rule

    return best_rule, best_score[0]


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


class KeywordSimulator:
    """Generates WorldState from user text using keyword matching. No LLM."""

    def simulate(self, event_text: str) -> WorldState:
        """
        Full keyword simulation pipeline:
        1. Normalize text
        2. Match against EVENT_RULES
        3. Build WorldState with epicenter/neighbor/distant intensities
        4. Apply regional diversity (profile-based secondary emotions)
        5. Validate diversity gate (ensure_diversity)
        6. Assign wave_order by geographic distance from wave_origin
        """
        rule, hit_count = _match_rule(event_text)

        emotion = rule["emotion"]
        base_intensity = rule["intensity"]
        wave_origin = rule.get("wave_origin", "CDMX")
        epicenter_states = rule.get("epicenter_states", ["CDMX"])
        description = rule.get("description_template", "Evento en México")

        joy_states = set(rule.get("joy_states", rule.get("joy_override_states", [])))
        fear_states = set(rule.get("fear_states", rule.get("fear_override_states", [])))
        hope_states = set(rule.get("hope_states", rule.get("hope_override_states", [])))
        sadness_states = set(rule.get("sadness_states", rule.get("sadness_override_states", [])))

        all_epicenter = epicenter_states == ["ALL"]
        wave_orders = _compute_wave_orders(wave_origin)

        def get_wave_order(code: str) -> int:
            return min(5, wave_orders.get(code, 5))

        state_emotions: list[StateEmotion] = []

        for s in MEXICO_STATES:
            code = s["state_code"]
            wave_ord = get_wave_order(code)

            if code in joy_states:
                emo = "joy"
                intensity = _clamp(base_intensity * 0.6)
            elif code in fear_states:
                emo = "fear"
                intensity = _clamp(base_intensity * 0.7)
            elif code in hope_states:
                emo = "hope"
                intensity = _clamp(base_intensity * 0.5)
            elif code in sadness_states:
                emo = "sadness"
                intensity = _clamp(base_intensity * 0.6)
            elif all_epicenter or code in epicenter_states:
                emo = emotion
                intensity = base_intensity
            else:
                emo = emotion
                if wave_ord <= 1:
                    intensity = _clamp(base_intensity * 0.70)
                elif wave_ord <= 2:
                    intensity = _clamp(base_intensity * 0.55)
                else:
                    intensity = _clamp(base_intensity * 0.40)

            contagion = CONTAGION_MATRIX.get(emo, CONTAGION_MATRIX["fear"])
            spread = EmotionSpread(
                anger=contagion.get("anger", 0.1),
                joy=contagion.get("joy", 0.1),
                fear=contagion.get("fear", 0.1),
                hope=contagion.get("hope", 0.1),
                sadness=contagion.get("sadness", 0.1),
            )

            state_emotions.append(StateEmotion(
                state_code=code,
                state_name=s["state_name"],
                emotion=Emotion(emo),
                intensity=round(intensity, 3),
                description=description,
                wave_order=wave_ord,
                latitude=s["latitude"],
                longitude=s["longitude"],
                population_weight=s["population_weight"],
            ))

        # ── Regional diversity ────────────────────────────────────────────────
        # Protected set: explicit override states + (for geographic events) epicenter states
        protected_codes: set[str] = set(epicenter_states) if not all_epicenter else set()
        protected_codes |= joy_states | fear_states | hope_states | sadness_states

        state_emotions = apply_regional_diversity(
            state_emotions, emotion, protected_codes, wave_orders, all_epicenter
        )
        state_emotions = ensure_diversity(state_emotions)

        # Build spread_matrix keyed by state_code (from final emotions)
        spread_matrix: dict[str, EmotionSpread] = {}
        for se in state_emotions:
            contagion = CONTAGION_MATRIX.get(se.emotion.value, CONTAGION_MATRIX["fear"])
            spread_matrix[se.state_code] = EmotionSpread(
                anger=contagion.get("anger", 0.1),
                joy=contagion.get("joy", 0.1),
                fear=contagion.get("fear", 0.1),
                hope=contagion.get("hope", 0.1),
                sadness=contagion.get("sadness", 0.1),
            )

        return WorldState(
            timestamp=datetime.utcnow(),
            event_text=event_text,
            event_source="keyword",
            states=state_emotions,
            spread_matrix=spread_matrix,
            metadata={
                "matched_rule": rule.get("description_template", "default"),
                "keyword_hits": hit_count,
                "wave_origin": wave_origin,
                "method": "keyword",
            },
        )
