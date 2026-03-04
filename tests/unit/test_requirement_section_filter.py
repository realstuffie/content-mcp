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

    def test_flat_heading_cis_collects_body_sections(self) -> None:
        """CIS flat-heading: requirement + body parts all at same level."""
        sections = [
            _make_section("5.3.2.5 Ensure pam_unix module is enabled"),
            _make_section("**Profile Applicability:**", content="- Level 1 Server"),
            _make_section("**Description:**", content="The pam_unix.so module..."),
            _make_section("**Rationale:**", content="Unix authentication is required..."),
            _make_section("**Audit:**", content="Run the following command..."),
            _make_section("**Remediation:**", content="Edit /etc/pam.d/..."),
            _make_section("5.3.3.1 Ensure pam_faillock module is enabled"),
        ]
        result = _find_section_by_requirement_id(sections, "5.3.2.5")
        assert result is not None
        assert "5.3.2.5" in result.title
        assert "pam_unix.so module" in result.content
        assert "Unix authentication" in result.content
        assert "Run the following command" in result.content
        assert "Edit /etc/pam.d/" in result.content

    def test_flat_heading_stops_at_next_requirement(self) -> None:
        """Sibling collection stops when hitting the next requirement ID."""
        sections = [
            _make_section("5.3.2.5 Ensure pam_unix module is enabled"),
            _make_section("**Description:**", content="pam_unix description"),
            _make_section("5.3.3.1 Ensure pam_faillock module is enabled"),
            _make_section("**Description:**", content="pam_faillock description"),
        ]
        result = _find_section_by_requirement_id(sections, "5.3.2.5")
        assert result is not None
        assert "pam_unix description" in result.content
        assert "pam_faillock" not in result.content

    def test_anssi_r_code_recognized_as_boundary(self) -> None:
        """R-code IDs are recognized as requirement boundaries."""
        sections = [
            _make_section("R1 Apply system updates"),
            _make_section("**Description:**", content="Keep system up to date"),
            _make_section("R2 Harden kernel"),
        ]
        result = _find_section_by_requirement_id(sections, "R1")
        assert result is not None
        assert "Keep system up to date" in result.content
        assert "Harden kernel" not in result.content

    def test_body_headings_not_mistaken_for_requirement_ids(self) -> None:
        """Headings like Description, Rationale are not requirement IDs."""
        sections = [
            _make_section("1.2.3 Some requirement"),
            _make_section("**Description:**", content="desc text"),
            _make_section("**Rationale:**", content="rationale text"),
            _make_section("**Audit:**", content="audit text"),
        ]
        result = _find_section_by_requirement_id(sections, "1.2.3")
        assert result is not None
        # All body sections should be collected
        assert "desc text" in result.content
        assert "rationale text" in result.content
        assert "audit text" in result.content

    def test_original_section_not_mutated(self) -> None:
        """Sibling collection creates a new DocumentSection, not mutating original."""
        original = _make_section("1.2.3 Some requirement")
        sections = [
            original,
            _make_section("**Description:**", content="desc text"),
        ]
        result = _find_section_by_requirement_id(sections, "1.2.3")
        assert result is not None
        assert "desc text" in result.content
        # Original should remain unchanged
        assert original.content == ""
        assert result is not original

    def test_hierarchical_document_no_regression(self) -> None:
        """Well-structured docs with proper hierarchy still work."""
        sub1 = _make_section("Description", content="desc text")
        sub2 = _make_section("Rationale", content="rationale text")
        parent = _make_section("1.2.3 Some requirement", content="intro", subsections=[sub1, sub2])
        sections = [parent, _make_section("1.2.4 Another requirement")]
        result = _find_section_by_requirement_id(sections, "1.2.3")
        assert result is not None
        assert result.title == "1.2.3 Some requirement"
        assert result.content == "intro"
        assert len(result.subsections) == 2

    def test_req_id_pattern_matches_through_bold_markers(self) -> None:
        """_REQ_ID_PATTERN must match IDs preceded by markdown bold markers."""
        from content_agent.server.handlers.tools import _REQ_ID_PATTERN

        assert _REQ_ID_PATTERN.search(
            '<span id="page-601-0"></span>**5.3.3 Configure PAM Arguments**'
        )
        assert _REQ_ID_PATTERN.search("*5.3.2.5 Ensure pam_unix*")
        # Existing cases must still work
        assert _REQ_ID_PATTERN.search("5.3.2.5 Ensure pam_unix")
        assert _REQ_ID_PATTERN.search("R34 Disabling service accounts")

    def test_flat_heading_cis_with_span_and_bold_markers(self) -> None:
        """CIS markdown has <span> and ** in headings — pattern must still detect boundaries."""
        sections = [
            _make_section(
                '<span id="page-598-0"></span>*5.3.2.5 Ensure pam_unix module is enabled'
                " (Automated)*"
            ),
            _make_section("**Profile Applicability:**", content="- Level 1 Server"),
            _make_section("**Description:**", content="The pam_unix.so module..."),
            _make_section("**Remediation:**", content="Edit /etc/pam.d/..."),
            _make_section('<span id="page-601-0"></span>**5.3.3 Configure PAM Arguments**'),
            _make_section("**Description:**", content="PAM arguments description"),
        ]
        result = _find_section_by_requirement_id(sections, "5.3.2.5")
        assert result is not None
        assert "5.3.2.5" in result.title
        assert "pam_unix.so module" in result.content
        assert "Edit /etc/pam.d/" in result.content
        # Must NOT include content from the next requirement (5.3.3)
        assert "PAM arguments description" not in result.content


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
