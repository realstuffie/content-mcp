"""HTML document parser."""

import re
from pathlib import Path
from typing import Any

from content_agent.core.parsing.base_parser import BaseParser, ParsingError
from content_agent.models.control import ParsedDocument

try:
    import requests
    from bs4 import BeautifulSoup

    HTML_AVAILABLE = True
except ImportError:
    HTML_AVAILABLE = False


class HTMLParser(BaseParser):
    """Parser for HTML documents and web pages."""

    def __init__(self, timeout: int = 30):
        """Initialize HTML parser.

        Args:
            timeout: Request timeout in seconds for fetching URLs
        """
        super().__init__()
        self.timeout = timeout
        if not HTML_AVAILABLE:
            raise ParsingError(
                "HTML parsing dependencies not installed. "
                "Install with: pip install beautifulsoup4 requests"
            )

    def parse(self, source: str | Path) -> ParsedDocument:
        """Parse an HTML document or web page.

        Args:
            source: Path to HTML file or URL string

        Returns:
            ParsedDocument with extracted content

        Raises:
            ParsingError: If parsing fails
        """
        try:
            # Determine if source is URL or file path
            source_str = str(source)
            if source_str.startswith(("http://", "https://")):
                html_content = self._fetch_url(source_str)
                source_path = source_str
            else:
                path = Path(source) if isinstance(source, str) else source
                if not path.exists():
                    raise ParsingError(f"HTML file not found: {path}")
                html_content = path.read_text(encoding="utf-8")
                source_path = str(path)

            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Extract metadata
            metadata = self._extract_metadata_from_html(soup)

            # Extract title
            title = metadata.get("title", "")
            if not title:
                title_tag = soup.find("title")
                if title_tag:
                    title = title_tag.get_text().strip()
                else:
                    h1 = soup.find("h1")
                    if h1:
                        title = h1.get_text().strip()
                    else:
                        title = (
                            Path(source_path).stem
                            if not source_str.startswith("http")
                            else "Document"
                        )

            # Extract text and parse sections
            self.extract_text(source)
            sections = self._parse_sections_from_soup(soup)

            return ParsedDocument(
                title=title,
                sections=sections,
                requirements=[],  # Will be populated by AI extraction
                metadata=metadata,
                source_path=source_path,
                source_type="html",
            )

        except Exception as e:
            raise ParsingError(f"Failed to parse HTML: {e}") from e

    def extract_text(self, source: str | Path) -> str:
        """Extract raw text from HTML.

        Args:
            source: Path to HTML file or URL string

        Returns:
            Extracted text content

        Raises:
            ParsingError: If extraction fails
        """
        try:
            # Get HTML content
            source_str = str(source)
            if source_str.startswith(("http://", "https://")):
                html_content = self._fetch_url(source_str)
            else:
                path = Path(source) if isinstance(source, str) else source
                html_content = path.read_text(encoding="utf-8")

            # Parse and extract text
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = "\n".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            raise ParsingError(f"Failed to extract text from HTML: {e}") from e

    def _fetch_url(self, url: str) -> str:
        """Fetch HTML content from URL.

        Args:
            url: URL to fetch

        Returns:
            HTML content

        Raises:
            ParsingError: If request fails
        """
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return str(response.text)
        except requests.RequestException as e:
            raise ParsingError(f"Failed to fetch URL {url}: {e}") from e

    def _extract_metadata_from_html(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract metadata from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Dictionary of metadata
        """
        metadata: dict[str, Any] = {}

        # Extract meta tags
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property")
            content = meta.get("content")
            if name and content:
                metadata[str(name)] = content

        # Extract title
        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text().strip()

        return metadata

    def _parse_sections_from_soup(self, soup: BeautifulSoup) -> list:
        """Parse sections from HTML using heading tags.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of DocumentSection objects
        """
        flat_sections = []

        # Find all headings (h1-h6)
        headings = soup.find_all(re.compile(r"^h[1-6]$"))

        for heading in headings:
            # Get heading level
            level = int(heading.name[1])

            # Get heading text
            title = heading.get_text().strip()

            # Get content until next heading of same or higher level
            content_parts = []
            for sibling in heading.find_next_siblings():
                if sibling.name and re.match(r"^h[1-6]$", sibling.name):
                    sibling_level = int(sibling.name[1])
                    if sibling_level <= level:
                        break
                content_parts.append(sibling.get_text().strip())

            content = "\n".join(content_parts)

            flat_sections.append((level, title, content))

        # If no headings found, treat whole document as one section
        if not flat_sections:
            title_tag = soup.find("title")
            title = title_tag.get_text().strip() if title_tag else "Document"
            content = soup.get_text()
            flat_sections.append((1, title, content))

        return self._create_section_hierarchy(flat_sections)
