"""Markdown document parser."""

import re
from pathlib import Path
from typing import Any

from content_agent.core.parsing.base_parser import BaseParser, ParsingError
from content_agent.models.control import ParsedDocument


class MarkdownParser(BaseParser):
    """Parser for Markdown documents."""

    def __init__(self) -> None:
        """Initialize Markdown parser."""
        super().__init__()

    def parse(self, source: str | Path) -> ParsedDocument:
        """Parse a Markdown document.

        Args:
            source: Path to Markdown file

        Returns:
            ParsedDocument with extracted content

        Raises:
            ParsingError: If parsing fails
        """
        path = Path(source) if isinstance(source, str) else source

        if not path.exists():
            raise ParsingError(f"Markdown file not found: {path}")

        try:
            # Read file content
            text = path.read_text(encoding="utf-8")

            # Extract metadata from frontmatter
            metadata = self._extract_metadata(text)

            # Extract title
            title = metadata.get("title", "")
            if not title:
                # Try to get from first heading
                for line in text.split("\n"):
                    if line.startswith("#"):
                        title = line.lstrip("#").strip()
                        break
                if not title:
                    title = path.stem

            # Parse sections
            sections = self._parse_sections(text)

            return ParsedDocument(
                title=title,
                sections=sections,
                requirements=[],  # Will be populated by AI extraction
                metadata=metadata,
                source_path=str(path),
                source_type="markdown",
            )

        except Exception as e:
            raise ParsingError(f"Failed to parse Markdown: {e}") from e

    def extract_text(self, source: str | Path) -> str:
        """Extract raw text from Markdown.

        Args:
            source: Path to Markdown file

        Returns:
            Raw text content

        Raises:
            ParsingError: If extraction fails
        """
        path = Path(source) if isinstance(source, str) else source

        try:
            return path.read_text(encoding="utf-8")
        except Exception as e:
            raise ParsingError(f"Failed to extract text from Markdown: {e}") from e

    def _extract_metadata(self, content: str) -> dict[str, Any]:
        """Extract metadata from Markdown frontmatter.

        Args:
            content: Markdown content

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, Any] = {}

        # Check for YAML frontmatter
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if match:
            frontmatter = match.group(1)
            # Simple YAML parsing (key: value)
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    metadata[key.strip()] = value.strip()

        return metadata

    def _parse_sections(self, text: str) -> list:
        """Parse sections from Markdown text.

        Args:
            text: Markdown content

        Returns:
            List of DocumentSection objects
        """
        # Remove frontmatter if present
        text = re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, flags=re.DOTALL)

        lines = text.split("\n")
        flat_sections = []
        current_section: tuple[int, str, list[str]] | None = None

        for line in lines:
            heading_level = self._detect_heading_level(line)

            if heading_level is not None:
                # Save previous section
                if current_section:
                    level, title, content_lines = current_section
                    flat_sections.append((level, title, "\n".join(content_lines)))

                # Extract heading text
                heading_text = line.lstrip("#").strip()

                # Start new section
                current_section = (heading_level, heading_text, [])
            elif current_section:
                # Add to current section content
                current_section[2].append(line)

        # Save last section
        if current_section:
            level, title, content_lines = current_section
            flat_sections.append((level, title, "\n".join(content_lines)))

        return self._create_section_hierarchy(flat_sections)

    def _detect_heading_level(self, line: str) -> int | None:
        """Detect if line is a Markdown heading and return its level.

        Args:
            line: Line of text

        Returns:
            Heading level (1-6) or None
        """
        # ATX-style headings (# Heading)
        if line.startswith("#"):
            level = 0
            for char in line:
                if char == "#":
                    level += 1
                else:
                    break
            if level <= 6 and line[level:].strip():
                return level

        return None
