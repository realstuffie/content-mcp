"""Tests for similar requirements functionality."""

from unittest.mock import patch

import pytest

from content_agent.models.control import (
    ControlFile,
    ControlRequirement,
)


def _make_requirement(
    req_id: str,
    title: str = "Test",
    description: str = "Test description",
    rules: list[str] | None = None,
) -> ControlRequirement:
    return ControlRequirement(
        id=req_id,
        title=title,
        description=description,
        rules=rules or [],
    )


def _make_control_file(
    control_id: str,
    controls: list[ControlRequirement] | None = None,
) -> ControlFile:
    return ControlFile(
        id=control_id,
        title=f"Test {control_id}",
        controls=controls or [],
    )


class TestTokenize:
    """Test ControlDiscovery._tokenize()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_lowercasing(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        tokens = discovery._tokenize("Password Authentication Required")
        assert "password" in tokens
        assert "authentication" in tokens
        assert "required" in tokens

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_punctuation_removal(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        tokens = discovery._tokenize("password-based, authentication!")
        assert "password" in tokens
        assert "based" in tokens
        assert "authentication" in tokens

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_stopword_filtering(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        tokens = discovery._tokenize("The system shall ensure information is protected")
        assert "the" not in tokens
        assert "shall" not in tokens
        assert "ensure" not in tokens
        assert "system" not in tokens
        assert "information" not in tokens
        assert "protected" in tokens

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_short_token_filtering(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        tokens = discovery._tokenize("OS is an IT system")
        assert "os" not in tokens
        assert "is" not in tokens
        assert "an" not in tokens
        assert "it" not in tokens

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_empty_text(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        tokens = discovery._tokenize("")
        assert tokens == set()


class TestJaccardSimilarity:
    """Test ControlDiscovery._jaccard_similarity()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_identical_sets(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        result = discovery._jaccard_similarity({"a", "b", "c"}, {"a", "b", "c"})
        assert result == 1.0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_disjoint_sets(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        result = discovery._jaccard_similarity({"a", "b"}, {"c", "d"})
        assert result == 0.0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_partial_overlap(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        result = discovery._jaccard_similarity({"a", "b", "c"}, {"b", "c", "d"})
        # intersection = {b, c} = 2, union = {a, b, c, d} = 4
        assert result == pytest.approx(0.5)

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_empty_sets(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()
        assert discovery._jaccard_similarity(set(), {"a"}) == 0.0
        assert discovery._jaccard_similarity({"a"}, set()) == 0.0
        assert discovery._jaccard_similarity(set(), set()) == 0.0


class TestFindSimilarRequirements:
    """Test ControlDiscovery.find_similar_requirements()."""

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_finds_similar(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement(
            "R1",
            title="Password complexity requirements",
            description="Enforce password complexity including length and character types",
            rules=["accounts_password_minlen"],
        )
        req2 = _make_requirement(
            "R2",
            title="Audit logging configuration",
            description="Configure audit logging for security events",
        )
        cf = _make_control_file("nist", controls=[req1, req2])

        with patch.object(discovery, "list_controls", return_value=["nist"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                results = discovery.find_similar_requirements(
                    "password complexity length requirements"
                )

        # Should find the password requirement but not the audit one
        assert len(results) >= 1
        assert results[0].requirement_id == "R1"
        assert results[0].similarity_score > 0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_exclude_control_id(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement("R1", title="Password policy", description="Password rules")
        cf1 = _make_control_file("cis", controls=[req1])
        cf2 = _make_control_file("nist", controls=[req1])

        with patch.object(discovery, "list_controls", return_value=["cis", "nist"]):
            with patch.object(
                discovery,
                "get_control_details",
                side_effect=lambda cid, **kw: {"cis": cf1, "nist": cf2}.get(cid),
            ):
                results = discovery.find_similar_requirements(
                    "password policy rules",
                    exclude_control_id="cis",
                )

        for r in results:
            assert r.control_id != "cis"

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_min_similarity_filtering(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req1 = _make_requirement("R1", title="SSH configuration", description="Configure SSH")
        cf = _make_control_file("test", controls=[req1])

        with patch.object(discovery, "list_controls", return_value=["test"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                results = discovery.find_similar_requirements(
                    "SSH configuration settings",
                    min_similarity=0.99,  # Very high threshold
                )

        # Should filter out most results
        assert len(results) == 0 or all(r.similarity_score >= 0.99 for r in results)

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_max_results_cap(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        # Create many requirements with similar text
        reqs = [
            _make_requirement(
                f"R{i}",
                title=f"Password complexity requirement variant {i}",
                description="Enforce password length and character requirements",
            )
            for i in range(30)
        ]
        cf = _make_control_file("test", controls=reqs)

        with patch.object(discovery, "list_controls", return_value=["test"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                results = discovery.find_similar_requirements(
                    "password complexity length character requirements",
                    max_results=5,
                )

        assert len(results) <= 5

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_no_matches(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req = _make_requirement(
            "R1",
            title="Audit logging",
            description="Configure audit logging for security events",
        )
        cf = _make_control_file("test", controls=[req])

        with patch.object(discovery, "list_controls", return_value=["test"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                results = discovery.find_similar_requirements(
                    "zzzzxyxyxyxy completely unrelated text",
                )

        assert len(results) == 0

    @patch("content_agent.core.discovery.controls.get_content_repository")
    def test_matching_terms_populated(self, mock_repo):
        from content_agent.core.discovery.controls import ControlDiscovery

        discovery = ControlDiscovery()

        req = _make_requirement(
            "R1",
            title="Password authentication",
            description="Enforce password authentication requirements",
        )
        cf = _make_control_file("test", controls=[req])

        with patch.object(discovery, "list_controls", return_value=["test"]):
            with patch.object(discovery, "get_control_details", return_value=cf):
                results = discovery.find_similar_requirements(
                    "password authentication enforcement",
                    min_similarity=0.0,
                )

        if results:
            assert len(results[0].matching_terms) > 0
            assert "password" in results[0].matching_terms
