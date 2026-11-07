"""Integration tests for validating real rules that contain Jinja2."""

import pytest

from tests.conftest import requires_content_repo


@requires_content_repo
class TestRuleValidationWithRealContent:
    @pytest.mark.parametrize("rule_id", ["sshd_disable_root_login", "timer_logrotate_enabled"])
    def test_real_rule_with_jinja_is_valid(self, real_content_repo, rule_id):
        from content_agent.core.discovery.rules import RuleDiscovery
        from content_agent.core.scaffolding.validators import validate_rule_yaml

        rule_path = RuleDiscovery().content_repo.path
        rule_file = next(rule_path.glob(f"linux_os/**/{rule_id}/rule.yml"))

        result = validate_rule_yaml(rule_file.read_text())

        assert result.valid, result.errors

    def test_every_rule_the_build_reads_is_valid(self, real_content_repo):
        # The OpenShift rules without documentation_complete used to fail
        from content_agent.core.discovery.rule_paths import rule_files
        from content_agent.core.scaffolding.validators import RuleValidator

        validator = RuleValidator()
        invalid = {}
        for rule_file in rule_files(real_content_repo.path):
            result = validator.validate_yaml(rule_file.read_text())
            if not result.valid:
                invalid[rule_file.parent.name] = [e.error for e in result.errors]

        assert invalid == {}
