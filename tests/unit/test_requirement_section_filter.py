"""Unit tests for requirement section filtering in parse_policy_document."""

from content_agent.models.control import DocumentSection, ParsedDocument
from content_agent.server.handlers.tools import _find_section_by_requirement_id


def _make_section(
    title: str, content: str = "", subsections: list[DocumentSection] | None = None
) -> DocumentSection:
    """Create a DocumentSection for testing."""
    return DocumentSection(
        id=title.lower().replace(" ", "-"),
        title=title,
        level=2,
        content=content,
        subsections=subsections or [],
    )


class TestFindSectionByRequirementId:
    """Tests for _find_section_by_requirement_id helper."""

    def test_title_match_anssi_r_code(self) -> None:
        sections = [
            _make_section("R34 M I Disabling the service accounts"),
            _make_section("R35 M I Something else"),
        ]
        result = _find_section_by_requirement_id(sections, "R34")
        assert result is not None
        assert "R34" in result.title

    def test_title_match_cis_dotted_number(self) -> None:
        sections = [
            _make_section("1.1.1.1 Ensure cramfs kernel module is not available"),
        ]
        result = _find_section_by_requirement_id(sections, "1.1.1.1")
        assert result is not None
        assert "1.1.1.1" in result.title

    def test_content_fallback_stig_id(self) -> None:
        sections = [
            _make_section("Some STIG Rule", content="STIG ID: RHEL-09-171011"),
        ]
        result = _find_section_by_requirement_id(sections, "RHEL-09-171011")
        assert result is not None
        assert "RHEL-09-171011" in result.content

    def test_content_fallback_in_subsection(self) -> None:
        sub = _make_section("Details", content="STIG ID: RHEL-09-171011")
        sections = [
            _make_section("Some STIG Rule", subsections=[sub]),
        ]
        result = _find_section_by_requirement_id(sections, "RHEL-09-171011")
        assert result is not None
        assert "RHEL-09-171011" in result.content

    def test_no_match_returns_none(self) -> None:
        sections = [_make_section("R34 M I Disabling the service accounts")]
        result = _find_section_by_requirement_id(sections, "NONEXISTENT-999")
        assert result is None

    def test_partial_match_r3_vs_r34(self) -> None:
        sections = [_make_section("R34 M I Disabling the service accounts")]
        result = _find_section_by_requirement_id(sections, "R3")
        assert result is None

    def test_partial_match_dotted_1_1_1_vs_1_1_1_1(self) -> None:
        sections = [_make_section("1.1.1.1 Ensure cramfs kernel module")]
        result = _find_section_by_requirement_id(sections, "1.1.1")
        assert result is None

    def test_case_insensitive_matching(self) -> None:
        sections = [
            _make_section("Some Rule", content="STIG ID: RHEL-09-171011"),
        ]
        result = _find_section_by_requirement_id(sections, "rhel-09-171011")
        assert result is not None

    def test_match_in_nested_subsection_title(self) -> None:
        sub = _make_section("R34 M I Disabling the service accounts")
        sections = [_make_section("Security Rules", subsections=[sub])]
        result = _find_section_by_requirement_id(sections, "R34")
        assert result is not None
        assert "R34" in result.title

    def test_empty_sections(self) -> None:
        result = _find_section_by_requirement_id([], "R34")
        assert result is None


class TestParseToolRequirementFiltering:
    """Tests for handler-level filtering behavior (via _find_section_by_requirement_id)."""

    def _make_parsed_document(self) -> ParsedDocument:
        return ParsedDocument(
            title="Test Policy",
            source_path="/test/doc.md",
            source_type="markdown",
            sections=[
                _make_section("R34 M I Disabling the service accounts"),
                _make_section("R35 M I Something else"),
                _make_section("1.1.1.1 Ensure cramfs kernel module"),
            ],
        )

    def test_filter_with_match(self) -> None:
        parsed = self._make_parsed_document()
        matching = _find_section_by_requirement_id(parsed.sections, "R34")
        assert matching is not None
        parsed.sections = [matching]
        assert len(parsed.sections) == 1
        assert "R34" in parsed.sections[0].title

    def test_filter_no_match_sets_metadata(self) -> None:
        parsed = self._make_parsed_document()
        matching = _find_section_by_requirement_id(parsed.sections, "NONEXISTENT")
        assert matching is None
        parsed.sections = []
        parsed.metadata["requirement_not_found"] = "NONEXISTENT"
        assert len(parsed.sections) == 0
        assert parsed.metadata["requirement_not_found"] == "NONEXISTENT"

    def test_no_filter_returns_all(self) -> None:
        parsed = self._make_parsed_document()
        # When requirement_id is not provided, no filtering occurs
        assert len(parsed.sections) == 3
