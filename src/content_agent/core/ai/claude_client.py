"""Claude API client for AI operations."""

import inspect
import json
from typing import Any

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


def _accepts_temperature(create: Any) -> bool:
    """Return whether messages.create() takes a temperature argument.

    anthropic SDK 2.x removed temperature from messages.create(), and passing it
    raises TypeError. Earlier versions accept it.
    """
    try:
        return "temperature" in inspect.signature(create).parameters
    except (TypeError, ValueError):
        return True


class ClaudeAPIError(Exception):
    """Exception raised for Claude API errors."""

    pass


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-5-5",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ):
        """Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens per request
            temperature: Temperature for generation (0.0 = deterministic)

        Raises:
            ClaudeAPIError: If anthropic package not installed
        """
        if not ANTHROPIC_AVAILABLE:
            raise ClaudeAPIError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )

        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def create_message(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:
        """Create a message and get response from Claude.

        Args:
            system_prompt: System prompt defining behavior
            user_prompt: User prompt with task
            temperature: Override default temperature. Ignored with anthropic
                SDK 2.x, which has no temperature parameter.

        Returns:
            Response text from Claude

        Raises:
            ClaudeAPIError: If API request fails
        """
        try:
            request: dict[str, Any] = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            if _accepts_temperature(self.client.messages.create):
                request["temperature"] = (
                    temperature if temperature is not None else self.temperature
                )
            response = self.client.messages.create(**request)

            # Extract text from response
            content = response.content
            if isinstance(content, list) and len(content) > 0:
                text = getattr(content[0], "text", None)
                if isinstance(text, str):
                    return text
            return str(content)

        except Exception as e:
            raise ClaudeAPIError(f"Claude API request failed: {e}") from e

    def extract_json_response(self, response: str) -> dict[str, Any]:
        """Extract JSON from Claude response.

        Args:
            response: Response text from Claude

        Returns:
            Parsed JSON dictionary

        Raises:
            ClaudeAPIError: If JSON extraction fails
        """
        try:
            # Try to find JSON in response (might be wrapped in markdown code block)
            json_match = response
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                json_match = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                json_match = response[start:end].strip()

            return json.loads(json_match)  # type: ignore[no-any-return]

        except json.JSONDecodeError as e:
            raise ClaudeAPIError(f"Failed to parse JSON response: {e}") from e
