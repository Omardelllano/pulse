"""
GeminiFreeProvider: Google Gemini Flash (free tier) via litellm.
All methods fall back to MockProvider on any LLM failure.
Matches Section 11 of the master briefing.
"""
import json
import logging
import re
import asyncio
import time
from datetime import datetime, date
from typing import Optional

from pulso.providers.base import BaseLLMProvider
from pulso.models.schemas import WorldState, StateEmotion, Emotion, EmotionSpread
from pulso.data.mexico_states import MEXICO_STATES
from pulso.data.contagion import CONTAGION_MATRIX
from pulso.config import settings
from pulso.engine.keyword_simulator import ensure_diversity

logger = logging.getLogger(__name__)

_STATE_CODES = [s["state_code"] for s in MEXICO_STATES]
_STATE_MAP = {s["state_code"]: s for s in MEXICO_STATES}
_EMOTIONS = {"anger", "joy", "fear", "hope", "sadness"}

# Gemini free tier: 15 RPM → enforce ≥5s between calls
_MIN_CALL_INTERVAL = 5.0

_GENERATE_BASE_PROMPT = """\
You are a sociopolitical analyst specialized in Mexico.
Based on the current general context of Mexico (economy, politics,
social climate, season), generate the emotional state for each of
Mexico's 32 states.
Today is {date}.

For each state determine:
- emotion: one of [anger, joy, fear, hope, sadness]
- intensity: 0.0 to 1.0
- wave_order: 0-5 (most populated/important states = 0)
- description: 1 sentence in Spanish explaining the current mood

Respond ONLY with a JSON array of 32 objects (no markdown, no code fences):
[{{"state_code":"CDMX","emotion":"fear","intensity":0.7,\
"wave_order":0,"description":"Incertidumbre por..."}}]

State codes: {state_codes}
"""

_SIMULATE_EVENT_PROMPT = """\
You are a sociological simulation engine for Mexico.
Event: "{event_text}"

Generate how all 32 Mexican states react emotionally.

CRITICAL — Mexico is diverse. Your response MUST:
- Include AT LEAST 3 different emotions across the 32 states
- Assign NO SINGLE emotion to more than 20 states
- Vary intensity significantly (range 0.25–0.95, not all similar)
- Reflect regional economic profiles:
  * Border states (BC, SON, CHIH, TAM): react to economic/security events differently
  * Industrial states (NL, QRO, AGS, GTO, SLP, COAH): respond to economic shocks
  * Vulnerable states (OAX, CHIS, GRO, TLX, ZAC): often sadness or fear regardless of event
  * Conservative states (GTO, AGS, JAL, QRO): cautious hope instead of full joy
  * Tourism states (QROO, BCS, JAL, OAX): fear for instability, joy for prosperity
  * Oil states (TAB, CAM, VER): react to energy and economic events uniquely

Example diversity for "dollar rises": \
CDMX=anger(0.90), BC=joy(0.70), OAX=sadness(0.60), NL=fear(0.55), GRO=sadness(0.65)

Epicenter states get highest intensity. Distant states get lower intensity.

Respond ONLY with a raw JSON object:
{{
  "states": [
    {{
      "state_code": "CDMX",
      "emotion": "anger",
      "intensity": 0.85,
      "description": "Descripción breve en español",
      "wave_order": 0
    }}
  ]
}}

emotion must be one of: anger, joy, fear, hope, sadness
Include all 32 state codes: {state_codes}
"""

_NEWS_BULK_PROMPT = """\
Analyze these {n} Mexican news headlines and return a JSON array of exactly {n} objects (same order).

Headlines:
{headlines_text}

For each headline return:
{{"emotion": "anger|joy|fear|hope|sadness", "affected_states": ["CDMX"], "intensity": 0.0-1.0, "decay_hours": 6.0}}

affected_states: state codes most affected (empty list = nationwide impact).
Valid state codes: {state_codes}

Respond ONLY with a raw JSON array. No explanation.
"""

_CONSISTENCY_PROMPT = """\
Review Mexico's current emotional state for realism.

Top 5 states by intensity: {state_summary}
Recent news: {news_summary}
Today: {date}

Are these emotions realistic given the news? If adjustments needed (max ±0.20 per state), list them.

Respond ONLY with a raw JSON object:
{{"consistent": true, "adjustments": [{{"state_code": "GRO", "intensity_delta": -0.1}}], "reason": "..."}}
If consistent, adjustments should be [].
"""


def _extract_json(text: str):
    """Pull JSON object or array from LLM response text."""
    # Code block first
    m = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
    if m:
        return json.loads(m.group(1))
    # Raw JSON object/array
    m = re.search(r'(\{[\s\S]+\}|\[[\s\S]+\])', text)
    if m:
        return json.loads(m.group(1))
    raise ValueError(f"No JSON in response: {text[:200]!r}")


class GeminiFreeProvider(BaseLLMProvider):
    """Google Gemini Flash (free tier) via litellm. Falls back to mock on failure."""

    def __init__(self, api_key: Optional[str] = None):
        self._api_key = api_key or settings.gemini_api_key
        self._last_call: float = 0.0
        self._mock: Optional[BaseLLMProvider] = None

    def _get_mock(self) -> BaseLLMProvider:
        if self._mock is None:
            from pulso.providers.mock import MockProvider
            self._mock = MockProvider()
        return self._mock

    async def _llm(self, prompt: str, temperature: float = 0.3) -> str:
        """Single LLM call with rate-limit guard."""
        import litellm

        elapsed = time.monotonic() - self._last_call
        if elapsed < _MIN_CALL_INTERVAL:
            await asyncio.sleep(_MIN_CALL_INTERVAL - elapsed)
        self._last_call = time.monotonic()

        kwargs = dict(
            model=settings.gemini_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        if self._api_key:
            kwargs["api_key"] = self._api_key

        response = await litellm.acompletion(**kwargs)
        return response.choices[0].message.content or ""

    def _parse_states(self, data: dict, event_text: str = "", source: str = "base") -> WorldState:
        """Build WorldState from parsed LLM JSON."""
        states_raw = data.get("states", [])
        if not states_raw:
            raise ValueError("LLM returned empty states list")

        state_emotions: list[StateEmotion] = []
        seen: set[str] = set()

        for item in states_raw:
            code = str(item.get("state_code", "")).upper()
            if code not in _STATE_MAP or code in seen:
                continue
            seen.add(code)
            static = _STATE_MAP[code]
            emo = item.get("emotion", "fear")
            if emo not in _EMOTIONS:
                emo = "fear"
            intensity = round(max(0.0, min(1.0, float(item.get("intensity", 0.5)))), 3)
            wave_order = max(0, min(5, int(item.get("wave_order", 2))))
            desc = str(item.get("description", ""))[:120] or "Sin descripción."

            state_emotions.append(StateEmotion(
                state_code=code,
                state_name=static["state_name"],
                emotion=Emotion(emo),
                intensity=intensity,
                description=desc,
                wave_order=wave_order,
                latitude=static["latitude"],
                longitude=static["longitude"],
                population_weight=static["population_weight"],
            ))

        # Fill any missing states with a neutral default
        for static in MEXICO_STATES:
            code = static["state_code"]
            if code not in seen:
                state_emotions.append(StateEmotion(
                    state_code=code,
                    state_name=static["state_name"],
                    emotion=Emotion("fear"),
                    intensity=0.4,
                    description="Sin datos disponibles.",
                    wave_order=3,
                    latitude=static["latitude"],
                    longitude=static["longitude"],
                    population_weight=static["population_weight"],
                ))

        # Enforce diversity gate on LLM results too
        state_emotions = ensure_diversity(state_emotions)

        spread_matrix = {}
        for se in state_emotions:
            c = CONTAGION_MATRIX.get(se.emotion.value, CONTAGION_MATRIX["fear"])
            spread_matrix[se.state_code] = EmotionSpread(**{k: c[k] for k in c})

        return WorldState(
            timestamp=datetime.utcnow(),
            event_text=event_text,
            event_source=source,
            states=state_emotions,
            spread_matrix=spread_matrix,
            metadata={"method": "gemini-free"},
        )

    # ── Public methods ────────────────────────────────────────────────────────

    async def generate_base_state(self) -> WorldState:
        try:
            prompt = _GENERATE_BASE_PROMPT.format(
                date=date.today().isoformat(),
                state_codes=", ".join(_STATE_CODES),
            )
            raw = await self._llm(prompt, temperature=0.4)
            data = _extract_json(raw)
            # Accept both array and {"states": [...]} formats
            if isinstance(data, list):
                data = {"states": data}
            return self._parse_states(data, source="base")
        except Exception as exc:
            logger.warning("[Gemini] generate_base_state failed (%s) — mock fallback", exc)
            return await self._get_mock().generate_base_state()

    async def simulate_event(self, event_text: str) -> WorldState:
        try:
            prompt = _SIMULATE_EVENT_PROMPT.format(
                event_text=event_text,
                state_codes=", ".join(_STATE_CODES),
            )
            raw = await self._llm(prompt, temperature=0.35)
            data = _extract_json(raw)
            return self._parse_states(data, event_text=event_text, source="user")
        except Exception as exc:
            logger.warning("[Gemini] simulate_event failed (%s) — mock fallback", exc)
            result = await self._get_mock().simulate_event(event_text)
            return result

    async def extract_news_sentiment(self, headline: str) -> dict:
        results = await self.extract_news_bulk([headline])
        return results[0] if results else {
            "emotion": "fear", "affected_states": [], "intensity": 0.3, "decay_hours": 6.0
        }

    async def extract_news_bulk(self, headlines: list[str]) -> list[dict]:
        if not headlines:
            return []
        try:
            headlines_text = "\n".join(f"{i+1}. {h}" for i, h in enumerate(headlines))
            prompt = _NEWS_BULK_PROMPT.format(
                n=len(headlines),
                headlines_text=headlines_text,
                state_codes=", ".join(_STATE_CODES),
            )
            raw = await self._llm(prompt, temperature=0.2)
            data = _extract_json(raw)
            if not isinstance(data, list):
                raise ValueError(f"Expected array, got {type(data).__name__}")

            results = []
            for item in data:
                emo = item.get("emotion", "fear")
                results.append({
                    "emotion": emo if emo in _EMOTIONS else "fear",
                    "affected_states": [c for c in item.get("affected_states", []) if c in _STATE_MAP],
                    "intensity": round(max(0.0, min(1.0, float(item.get("intensity", 0.4)))), 3),
                    "decay_hours": float(item.get("decay_hours", 6.0)),
                })
            # Pad/trim to match input count
            while len(results) < len(headlines):
                results.append({"emotion": "fear", "affected_states": [], "intensity": 0.3, "decay_hours": 6.0})
            return results[:len(headlines)]
        except Exception as exc:
            logger.warning("[Gemini] extract_news_bulk failed (%s) — mock fallback", exc)
            mock = self._get_mock()
            return [await mock.extract_news_sentiment(h) for h in headlines]

    async def moderate_input(self, text: str) -> dict:
        return await self._get_mock().moderate_input(text)

    async def check_consistency(self, current_state: WorldState, news: list) -> WorldState:
        try:
            top5 = sorted(current_state.states, key=lambda s: s.intensity, reverse=True)[:5]
            state_summary = "; ".join(
                f"{s.state_code}={s.emotion.value}({s.intensity:.2f})" for s in top5
            )
            news_summary = "; ".join(
                str(n.get("headline", str(n))) for n in (news or [])[:5]
            ) or "No recent news"

            prompt = _CONSISTENCY_PROMPT.format(
                state_summary=state_summary,
                news_summary=news_summary,
                date=date.today().isoformat(),
            )
            raw = await self._llm(prompt, temperature=0.2)
            data = _extract_json(raw)

            if data.get("consistent", True) or not data.get("adjustments"):
                return current_state

            adj_map = {a["state_code"]: float(a.get("intensity_delta", 0.0)) for a in data["adjustments"]}
            states = [
                s.model_copy(update={
                    "intensity": round(max(0.0, min(1.0,
                        s.intensity + max(-0.20, min(0.20, adj_map.get(s.state_code, 0.0)))
                    )), 3)
                })
                for s in current_state.states
            ]
            return current_state.model_copy(update={
                "states": states,
                "metadata": {**current_state.metadata, "consistency_checked": True},
            })
        except Exception as exc:
            logger.warning("[Gemini] check_consistency failed (%s) — no adjustment", exc)
            return current_state
