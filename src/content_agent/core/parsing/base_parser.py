"""Base parser class for document parsing."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from content_agent.models.control import DocumentSection, ParsedDocument


class ParsingError(Exception):
    """Exception raised during document parsing."""

    pass


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    def __init__(self) -> None:
        """Initialize the parser."""
        self.metadata: dict[str, Any] = {}

    @abstractmethod
    def parse(self, source: str | Path) -> ParsedDocument:
        """Parse a document and return structured data.

        Args:
            source: Path to file or URL string to parse

        Returns:
            ParsedDocument with extracted sections and content

        Raises:
            ParsingError: If parsing fails
        """
        pass

    @abstractmethod
    def extract_text(self, source: str | Path) -> str:
        """Extract raw text from document.

        Args:
            source: Path to file or URL string

        Returns:
            Raw text content

        Raises:
            ParsingError: If extraction fails
        """
        pass

    def _create_section_hierarchy(
        self, flat_sections: list[tuple[int, str, str]]
    ) -> list[DocumentSection]:
        """Convert flat list of sections to hierarchical structure.

        Args:
            flat_sections: List of (level, title, content) tuples

        Returns:
            List of top-level DocumentSection objects with nested subsections
        """
        if not flat_sections:
            return []

        sections: list[DocumentSection] = []
        stack: list[DocumentSection] = []

        for idx, (level, title, content) in enumerate(flat_sections):
            section_id = self._generate_section_id(title, idx)
            section = DocumentSection(
                id=section_id,
                title=title,
                level=level,
                content=content,
                subsections=[],
                parent_id=None,
            )

            # Remove sections from stack that are not ancestors
            while stack and stack[-1].level >= level:
                stack.pop()

            if stack:
                # Add as subsection to parent
                parent = stack[-1]
                section.parent_id = parent.id
                parent.subsections.append(section)
            else:
                # Add as top-level section
                sections.append(section)

            stack.append(section)

        return sections

    def _generate_section_id(self, title: str, index: int) -> str:
        """Generate a section ID from title.

        Args:
            title: Section title
            index: Section index

        Returns:
            Section ID (e.g., "introduction" or "section_1")
        """
        # Remove special characters and convert to lowercase
        clean_title = "".join(c if c.isalnum() else "_" for c in title.lower())
        clean_title = clean_title.strip("_")

        # Limit length and remove consecutive underscores
        clean_title = "_".join(filter(None, clean_title.split("_")))[:50]

        if clean_title:
            return clean_title

        return f"section_{index + 1}"

    def _detect_heading_level(self, line: str) -> int | None:
        """Detect if line is a heading and return its level.

        Args:
            line: Line of text to check

        Returns:
            Heading level (1-6) or None if not a heading
        """
        # Override in subclasses for format-specific heading detection
        return None

    def _extract_metadata(self, content: str) -> dict[str, Any]:
        """Extract metadata from document content.

        Args:
            content: Document content

        Returns:
            Dictionary of metadata
        """
        # Override in subclasses for format-specific metadata extraction
        return {}
