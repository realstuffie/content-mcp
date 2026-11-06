"""Tests for ClaudeClient requests across anthropic SDK versions."""

from types import SimpleNamespace

import pytest

from content_agent.core.ai.claude_client import ClaudeClient


def _response(text):
    return SimpleNamespace(content=[SimpleNamespace(text=text)])


class MessagesWithoutTemperature:
    """messages.create() as in anthropic SDK 2.x."""

    def __init__(self):
        self.requests = []

    def create(self, *, model, max_tokens, messages, system=None):
        self.requests.append(
            {"model": model, "max_tokens": max_tokens, "messages": messages, "system": system}
        )
        return _response("ok")


class MessagesWithTemperature:
    """messages.create() as in anthropic SDK 1.x and earlier."""

    def __init__(self):
        self.requests = []

    def create(self, *, model, max_tokens, messages, system=None, temperature=None):
        self.requests.append({"temperature": temperature})
        return _response("ok")


@pytest.fixture
def client():
    pytest.importorskip("anthropic")
    return ClaudeClient(api_key="test-key", model="test-model", temperature=0.2)


def test_temperature_not_sent_when_sdk_has_no_parameter(client):
    messages = MessagesWithoutTemperature()
    client.client = SimpleNamespace(messages=messages)

    assert client.create_message("system", "user") == "ok"
    assert messages.requests == [
        {
            "model": "test-model",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": "user"}],
            "system": "system",
        }
    ]


def test_temperature_sent_when_sdk_accepts_it(client):
    messages = MessagesWithTemperature()
    client.client = SimpleNamespace(messages=messages)

    client.create_message("system", "user")
    client.create_message("system", "user", temperature=0.7)

    assert messages.requests == [{"temperature": 0.2}, {"temperature": 0.7}]
