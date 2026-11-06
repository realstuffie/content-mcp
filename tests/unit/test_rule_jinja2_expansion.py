"""Tests for rule YAML loading with Jinja2 template expansion."""

from unittest.mock import MagicMock, patch


class TestLoadRuleYaml:
    """Test RuleDiscovery._load_rule_yaml()."""

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def _make_discovery(self, mock_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        return RuleDiscovery()

    def test_uses_ssg_open_and_expand(self, tmp_path):
        """_load_rule_yaml delegates to ssg.yaml.open_and_expand."""
        rule_file = tmp_path / "rule.yml"
        rule_file.write_text("title: test\n")

        discovery = self._make_discovery()

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.return_value = {"title": "expanded"}

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            result = discovery._load_rule_yaml(rule_file)

        mock_ssg_modules.yaml.open_and_expand.assert_called_once_with(
            str(rule_file), {"product": ""}
        )
        assert result == {"title": "expanded"}

    def test_passes_product_substitutions(self, tmp_path):
        """When product is provided, it is passed as a substitution."""
        rule_file = tmp_path / "rule.yml"
        rule_file.write_text("title: test\n")

        discovery = self._make_discovery()

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.return_value = {"title": "expanded"}

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            discovery._load_rule_yaml(rule_file, product="rhel10")

        mock_ssg_modules.yaml.open_and_expand.assert_called_once_with(
            str(rule_file), {"product": "rhel10"}
        )

    def test_falls_back_to_yaml_load_on_ssg_failure(self, tmp_path):
        """Falls back to raw yaml.load if ssg expansion fails."""
        rule_file = tmp_path / "rule.yml"
        rule_file.write_text("title: fallback\nseverity: high\n")

        discovery = self._make_discovery()

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.side_effect = RuntimeError("ssg broken")

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            result = discovery._load_rule_yaml(rule_file)

        assert result["title"] == "fallback"
        assert result["severity"] == "high"

    def test_non_templated_rule_loads_normally(self, tmp_path):
        """Rules without Jinja2 templates produce the same result as raw yaml.load."""
        rule_file = tmp_path / "rule.yml"
        rule_file.write_text("title: Plain Rule\nseverity: low\nplatform: machine\n")

        discovery = self._make_discovery()

        expected = {"title": "Plain Rule", "severity": "low", "platform": "machine"}
        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.return_value = expected

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            result = discovery._load_rule_yaml(rule_file)

        assert result == expected
        assert result["title"] == "Plain Rule"
        assert result["severity"] == "low"
        assert result["platform"] == "machine"


class TestGetRuleDetailsWithJinja2:
    """Test that get_rule_details works with Jinja2-templated rules."""

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_rule_with_jinja2_is_discoverable(self, mock_repo, tmp_path):
        """Rules with Jinja2 control structures must be loadable."""
        from content_agent.core.discovery.rules import RuleDiscovery

        rule_dir = tmp_path / "linux_os" / "guide" / "test_rule"
        rule_dir.mkdir(parents=True)
        rule_file = rule_dir / "rule.yml"
        rule_file.write_text(
            "title: Test Rule\nseverity: medium\n" "identifiers:\n  cce@rhel9: CCE-12345-6\n"
        )

        mock_repo.return_value.path = tmp_path
        discovery = RuleDiscovery()
        discovery._rule_cache = {"test_rule": rule_file}

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.return_value = {
            "title": "Test Rule",
            "severity": "medium",
            "identifiers": {"cce@rhel9": "CCE-12345-6"},
            "references": {},
        }

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            result = discovery.get_rule_details("test_rule")

        assert result is not None
        assert result.title == "Test Rule"
        assert result.severity == "medium"

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_rule_with_product_expansion(self, mock_repo, tmp_path):
        """Product-specific content is expanded when product is provided."""
        from content_agent.core.discovery.rules import RuleDiscovery

        rule_dir = tmp_path / "linux_os" / "guide" / "test_rule"
        rule_dir.mkdir(parents=True)
        rule_file = rule_dir / "rule.yml"
        rule_file.write_text("title: Test Rule\n")

        mock_repo.return_value.path = tmp_path
        discovery = RuleDiscovery()
        discovery._rule_cache = {"test_rule": rule_file}

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.return_value = {
            "title": "Test Rule",
            "severity": "medium",
            "identifiers": {},
            "references": {},
            "warnings": [{"general": "Automated remediation not available"}],
        }

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            result = discovery.get_rule_details("test_rule", product="rhel10")

        mock_ssg_modules.yaml.open_and_expand.assert_called_once_with(
            str(rule_file), {"product": "rhel10"}
        )
        assert result is not None

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_raises_when_both_expansion_and_yaml_fail(self, mock_repo, tmp_path):
        """When both ssg expansion and raw yaml.load fail, get_rule_details raises."""
        import pytest
        import yaml

        from content_agent.core.discovery.rules import RuleDiscovery

        rule_dir = tmp_path / "linux_os" / "guide" / "broken_rule"
        rule_dir.mkdir(parents=True)
        rule_file = rule_dir / "rule.yml"
        rule_file.write_text("{{% invalid yaml {{% everywhere\n")

        mock_repo.return_value.path = tmp_path
        discovery = RuleDiscovery()
        discovery._rule_cache = {"broken_rule": rule_file}

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.side_effect = RuntimeError("expansion failed")

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            with pytest.raises((yaml.scanner.ScannerError, ValueError)):
                discovery.get_rule_details("broken_rule")

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_search_accumulates_error_when_both_paths_fail(self, mock_repo, tmp_path):
        """When both paths fail, rule is excluded from items and error is accumulated."""
        from content_agent.core.discovery.rules import RuleDiscovery

        rule_dir = tmp_path / "linux_os" / "guide" / "broken_rule"
        rule_dir.mkdir(parents=True)
        rule_file = rule_dir / "rule.yml"
        rule_file.write_text("{{% invalid yaml {{% everywhere\n")

        mock_repo.return_value.path = tmp_path
        discovery = RuleDiscovery()
        discovery._rule_cache = {"broken_rule": rule_file}

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.side_effect = RuntimeError("expansion failed")

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            result = discovery.search_rules(query="broken_rule")

        assert result.items == []
        assert len(result.errors) == 1
        assert "broken_rule" in result.errors[0]


class TestSearchRulesWithJinja2:
    """Test that search_rules finds rules with Jinja2 control structures."""

    @patch("content_agent.core.discovery.rules.get_content_repository")
    def test_search_includes_jinja2_rules(self, mock_repo, tmp_path):
        """search_rules must include rules that have Jinja2 control structures."""
        from content_agent.core.discovery.rules import RuleDiscovery

        rule_dir = tmp_path / "linux_os" / "guide" / "accounts_password_pam_unix_enabled"
        rule_dir.mkdir(parents=True)
        rule_file = rule_dir / "rule.yml"
        rule_file.write_text("title: Verify pam_unix\n")

        mock_repo.return_value.path = tmp_path
        discovery = RuleDiscovery()
        discovery._rule_cache = {"accounts_password_pam_unix_enabled": rule_file}

        mock_ssg_modules = MagicMock()
        mock_ssg_modules.yaml.open_and_expand.return_value = {
            "title": "Verify pam_unix module is activated",
            "severity": "medium",
            "identifiers": {},
            "references": {},
        }

        with patch(
            "content_agent.core.discovery.rules.get_ssg_modules",
            return_value=mock_ssg_modules,
        ):
            results = discovery.search_rules(query="pam_unix_enabled")

        rule_ids = [r.rule_id for r in results.items]
        assert "accounts_password_pam_unix_enabled" in rule_ids
