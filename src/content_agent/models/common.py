"""Common data types shared across the content-agent models."""

from dataclasses import dataclass, field
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class DiscoveryResult(Generic[T]):
    """Result wrapper for list discovery methods.

    Carries both successfully parsed items and error messages for items
    that failed to parse.
    """

    items: list[T] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
