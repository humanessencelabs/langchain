"""Model provider abstraction for Essence Pulse.

All AI reasoning inside the pipeline goes through a :class:`ModelProvider`.
This keeps the identity, permission, and memory layers independent of any
specific AI vendor.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelProvider(ABC):
    """Abstract base class for AI model adapters.

    Subclasses wrap a concrete AI provider (OpenAI, Anthropic, Gemini,
    local GGUF, etc.) and expose a uniform interface.

    Implement :meth:`complete` and, optionally, :meth:`stream`.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider identifier (e.g. ``"openai"``).

        Returns:
            Provider name string.
        """

    @abstractmethod
    def complete(self, prompt: str, *, context: dict[str, Any] | None = None) -> str:
        """Generate a completion for *prompt*.

        The ``context`` dictionary carries structured metadata (event
        metadata, identity hints, etc.) that adapters *may* incorporate
        into system prompts.  Adapters must never forward raw untrusted
        payload content as instructions.

        Args:
            prompt: The instruction or question to complete.
            context: Optional structured metadata.

        Returns:
            The model's text response.
        """

    def stream(
        self, prompt: str, *, context: dict[str, Any] | None = None
    ) -> list[str]:
        """Stream completion tokens.  Default: returns a single-item list.

        Override in subclasses that support genuine streaming.

        Args:
            prompt: The instruction or question to complete.
            context: Optional structured metadata.

        Returns:
            List of string chunks.
        """
        return [self.complete(prompt, context=context)]
