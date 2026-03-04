"""Claude API client for AI operations."""

import json
from typing import Any

try:
    from anthropic import Anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class ClaudeAPIError(Exception):
    """Exception raised for Claude API errors."""

    pass


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet-20241022",
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
            temperature: Override default temperature

        Returns:
            Response text from Claude

        Raises:
            ClaudeAPIError: If API request fails
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature if temperature is not None else self.temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            # Extract text from response
            content = response.content
            if isinstance(content, list) and len(content) > 0:
                return content[0].text  # type: ignore[union-attr]
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
