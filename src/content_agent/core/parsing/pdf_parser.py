"""PDF document parser."""

import re
from pathlib import Path
from typing import Any

from content_agent.core.parsing.base_parser import BaseParser, ParsingError
from content_agent.models.control import ParsedDocument

try:
    import pdfplumber
    from pypdf import PdfReader

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFParser(BaseParser):
    """Parser for PDF documents."""

    def __init__(self) -> None:
        """Initialize PDF parser."""
        super().__init__()
        if not PDF_AVAILABLE:
            raise ParsingError(
                "PDF parsing dependencies not installed. "
                "Install with: pip install pdfplumber pypdf"
            )

    def parse(self, source: str | Path) -> ParsedDocument:
        """Parse a PDF document.

        Args:
            source: Path to PDF file

        Returns:
            ParsedDocument with extracted content

        Raises:
            ParsingError: If parsing fails
        """
        path = Path(source) if isinstance(source, str) else source

        if not path.exists():
            raise ParsingError(f"PDF file not found: {path}")

        if not path.suffix.lower() == ".pdf":
            raise ParsingError(f"File is not a PDF: {path}")

        try:
            # Extract text and metadata
            text = self.extract_text(path)
            metadata = self._extract_metadata_from_pdf(path)

            # Extract title from metadata or first line
            title = metadata.get("title", "")
            if not title:
                first_lines = text.split("\n")[:5]
                for line in first_lines:
                    if line.strip():
                        title = line.strip()
                        break
                if not title:
                    title = path.stem

            # Parse sections from text
            sections = self._parse_sections(text)

            return ParsedDocument(
                title=title,
                sections=sections,
                requirements=[],  # Will be populated by AI extraction
                metadata=metadata,
                source_path=str(path),
                source_type="pdf",
            )

        except Exception as e:
            raise ParsingError(f"Failed to parse PDF: {e}") from e

    def extract_text(self, source: str | Path) -> str:
        """Extract raw text from PDF.

        Args:
            source: Path to PDF file

        Returns:
            Extracted text

        Raises:
            ParsingError: If extraction fails
        """
        path = Path(source) if isinstance(source, str) else source

        try:
            text_parts = []

            # Try pdfplumber first (better text extraction)
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)

            return "\n\n".join(text_parts)

        except Exception as e:
            raise ParsingError(f"Failed to extract text from PDF: {e}") from e

    def _extract_metadata_from_pdf(self, path: Path) -> dict[str, Any]:
        """Extract metadata from PDF file.

        Args:
            path: Path to PDF file

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, Any] = {}

        try:
            reader = PdfReader(path)

            if reader.metadata:
                pdf_meta = reader.metadata
                metadata["title"] = pdf_meta.get("/Title", "")
                metadata["author"] = pdf_meta.get("/Author", "")
                metadata["subject"] = pdf_meta.get("/Subject", "")
                metadata["creator"] = pdf_meta.get("/Creator", "")
                metadata["producer"] = pdf_meta.get("/Producer", "")

                # Parse dates
                if "/CreationDate" in pdf_meta:
                    metadata["creation_date"] = pdf_meta["/CreationDate"]
                if "/ModDate" in pdf_meta:
                    metadata["modification_date"] = pdf_meta["/ModDate"]

            metadata["page_count"] = len(reader.pages)

        except Exception:
            # If metadata extraction fails, return empty dict
            pass

        return metadata

    def _parse_sections(self, text: str) -> list:
        """Parse sections from PDF text.

        Args:
            text: Extracted PDF text

        Returns:
            List of DocumentSection objects
        """
        lines = text.split("\n")
        flat_sections = []
        current_section: tuple[int, str, list[str]] | None = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Detect headings (various patterns)
            heading_level = self._detect_heading_level(stripped)

            if heading_level is not None:
                # Save previous section
                if current_section:
                    level, title, content_lines = current_section
                    flat_sections.append((level, title, "\n".join(content_lines)))

                # Start new section
                current_section = (heading_level, stripped, [])
            elif current_section:
                # Add to current section content
                current_section[2].append(line)

        # Save last section
        if current_section:
            level, title, content_lines = current_section
            flat_sections.append((level, title, "\n".join(content_lines)))

        return self._create_section_hierarchy(flat_sections)

    def _detect_heading_level(self, line: str) -> int | None:
        """Detect if line is a heading and return its level.

        Args:
            line: Line of text

        Returns:
            Heading level (1-6) or None
        """
        # Pattern 1: All caps, short lines (likely headings)
        if len(line) < 100 and line.isupper() and len(line.split()) <= 10:
            return 1

        # Pattern 2: Numbered sections (e.g., "1. Introduction", "2.1 Overview")
        numbered_pattern = r"^(\d+\.)+\s+[A-Z]"
        if re.match(numbered_pattern, line):
            dots = line.split()[0].count(".")
            return min(dots + 1, 6)

        # Pattern 3: Section markers (e.g., "Section 1:", "Chapter 2:")
        section_pattern = r"^(Section|Chapter|Part|Appendix)\s+\d+"
        if re.match(section_pattern, line, re.IGNORECASE):
            return 1

        # Pattern 4: Title case, short, no period at end
        if (
            len(line) < 100
            and line[0].isupper()
            and not line.endswith(".")
            and len(line.split()) <= 15
        ):
            # Check if it looks like a title (most words capitalized)
            words = line.split()
            capitalized = sum(1 for w in words if w[0].isupper())
            if capitalized / len(words) > 0.5:
                return 2

        return None
