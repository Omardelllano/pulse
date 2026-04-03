"""
InputGuard: Three-layer content filter for user input.
Layer 1: Regex blocklist (instant, zero cost)
Layer 2: Heuristic checks (instant, zero cost)
Layer 3: LLM moderation (only if layers 1-2 pass, costs 1 call)
"""
import re
from typing import Optional
from pulso.providers.base import BaseLLMProvider


class InputGuard:
    """
    Three-layer content filter for user-submitted event text.
    Validates input before it reaches the LLM simulation engine.
    """

    # Layer 1: Blocked patterns (English + Spanish)
    BLOCKED_PATTERNS = [
        r'\b(sex|porn|nude|xxx|nsfw|porno|desnud)\b',
        r'\b(kill|murder|bomb|attack|matar|violar|asesinar)\b',
        r'(.)\1{5,}',
        r'^[^a-záéíóúñ\s]{10,}$',
    ]

    # Layer 2: Heuristic thresholds
    MIN_WORDS = 2
    MAX_WORDS = 50
    MAX_CHARS = 200
    MIN_UNIQUE_WORDS = 2
    MUST_CONTAIN_LETTER = True

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.BLOCKED_PATTERNS
        ]

    def _check_layer1(self, text: str) -> tuple[bool, str]:
        """Regex blocklist check."""
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return False, "Contenido no permitido detectado."
        return True, ""

    def _check_layer2(self, text: str) -> tuple[bool, str]:
        """Heuristic validation."""
        if len(text) > self.MAX_CHARS:
            return False, f"El texto no puede tener más de {self.MAX_CHARS} caracteres."
        words = text.strip().split()
        if len(words) < self.MIN_WORDS:
            return False, f"El texto debe tener al menos {self.MIN_WORDS} palabras."
        if len(words) > self.MAX_WORDS:
            return False, f"El texto no puede tener más de {self.MAX_WORDS} palabras."
        unique_words = set(w.lower() for w in words)
        if len(unique_words) < self.MIN_UNIQUE_WORDS:
            return False, "El texto no tiene suficiente variedad de palabras."
        if self.MUST_CONTAIN_LETTER and not re.search(r'[a-záéíóúñ]', text, re.IGNORECASE):
            return False, "El texto debe contener palabras reales."
        return True, ""

    async def validate(self, text: str) -> tuple[bool, str]:
        """
        Full validation pipeline.
        Returns (is_valid, reason_if_invalid).
        """
        valid, reason = self._check_layer1(text)
        if not valid:
            return False, reason

        valid, reason = self._check_layer2(text)
        if not valid:
            return False, reason

        # Layer 3: LLM moderation (only if provider available)
        if self.provider:
            result = await self.provider.moderate_input(text)
            if not result.get("valid", True):
                return False, result.get("reason", "Contenido no válido.")

        return True, ""
