"""Tests for document parsers."""

import pytest

from content_agent.core.parsing import (
    BaseParser,
    MarkdownParser,
    ParsingError,
    TextParser,
)


def test_text_parser_basic(tmp_path):
    """Test basic text parsing."""
    # Create test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("""Test Document

Section 1
This is section 1 content.

Section 2
This is section 2 content.
""")

    parser = TextParser()
    doc = parser.parse(test_file)

    assert doc.title == "Test Document"
    assert doc.source_type == "text"
    assert len(doc.sections) > 0


def test_text_parser_extract_text(tmp_path):
    """Test text extraction."""
    test_file = tmp_path / "test.txt"
    content = "Hello, world!\nThis is a test."
    test_file.write_text(content)

    parser = TextParser()
    text = parser.extract_text(test_file)

    assert text == content


def test_text_parser_nonexistent_file():
    """Test parsing nonexistent file."""
    parser = TextParser()

    with pytest.raises(ParsingError):
        parser.parse("/nonexistent/file.txt")


def test_markdown_parser_basic(tmp_path):
    """Test basic markdown parsing."""
    test_file = tmp_path / "test.md"
    test_file.write_text("""# Test Document

## Section 1
This is section 1 content.

## Section 2
This is section 2 content.
""")

    parser = MarkdownParser()
    doc = parser.parse(test_file)

    assert doc.title == "Test Document"
    assert doc.source_type == "markdown"
    # Should have 1 top-level section (Test Document) with 2 subsections
    assert len(doc.sections) == 1
    assert len(doc.sections[0].subsections) == 2


def test_markdown_parser_with_frontmatter(tmp_path):
    """Test markdown with YAML frontmatter."""
    test_file = tmp_path / "test.md"
    test_file.write_text("""---
title: My Document
author: Test Author
---

# Heading

Content here.
""")

    parser = MarkdownParser()
    doc = parser.parse(test_file)

    assert doc.title == "My Document"
    assert doc.metadata.get("author") == "Test Author"


def test_base_parser_section_hierarchy():
    """Test section hierarchy creation."""

    class TestParser(BaseParser):
        def parse(self, source):
            pass

        def extract_text(self, source):
            pass

    parser = TestParser()

    # Test flat sections
    flat = [
        (1, "Title 1", "Content 1"),
        (2, "Title 1.1", "Content 1.1"),
        (1, "Title 2", "Content 2"),
    ]

    hierarchy = parser._create_section_hierarchy(flat)

    assert len(hierarchy) == 2  # Two top-level sections
    assert hierarchy[0].title == "Title 1"
    assert len(hierarchy[0].subsections) == 1
    assert hierarchy[0].subsections[0].title == "Title 1.1"


def test_base_parser_generate_section_id():
    """Test section ID generation."""

    class TestParser(BaseParser):
        def parse(self, source):
            pass

        def extract_text(self, source):
            pass

    parser = TestParser()

    # Test normal title
    section_id = parser._generate_section_id("Introduction", 0)
    assert section_id == "introduction"

    # Test title with special characters
    section_id = parser._generate_section_id("Section 1.2: Overview", 1)
    assert "overview" in section_id

    # Test empty title
    section_id = parser._generate_section_id("", 5)
    assert section_id == "section_6"


def test_pdf_parser_reads_metadata(tmp_path):
    """PDF metadata comes from pypdf, the maintained successor of PyPDF2."""
    pytest.importorskip("pdfplumber")
    from pypdf import PdfWriter

    from content_agent.core.parsing.pdf_parser import PDFParser

    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    writer.add_metadata({"/Title": "Sample Policy", "/Author": "Security Team"})
    pdf_file = tmp_path / "policy.pdf"
    with open(pdf_file, "wb") as f:
        writer.write(f)

    metadata = PDFParser()._extract_metadata_from_pdf(pdf_file)

    assert metadata["title"] == "Sample Policy"
    assert metadata["author"] == "Security Team"
    assert metadata["page_count"] == 2
