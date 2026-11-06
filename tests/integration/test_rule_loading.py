"""Integration tests for loading rules whose rule.yml needs product variables."""

import pytest

from tests.conftest import requires_content_repo

# Each of these failed to load before: the Jinja2 in their rule.yml needs a product
# name or product variables such as full_name.
RULES_NEEDING_PRODUCT_VARIABLES = [
    "service_tftp_disabled",
    "file_permissions_etc_issue",
    "file_permissions_sshd_private_key",
    "systemd_journal_upload_url",
]


@requires_content_repo
class TestRuleLoadingWithRealContent:
    @pytest.mark.parametrize("rule_id", RULES_NEEDING_PRODUCT_VARIABLES)
    def test_rule_loads_without_product(self, real_content_repo, rule_id):
        from content_agent.core.discovery.rules import RuleDiscovery

        rule = RuleDiscovery().get_rule_details(rule_id, include_rendered=False)
        assert rule is not None
        assert rule.title

    @pytest.mark.parametrize("rule_id", RULES_NEEDING_PRODUCT_VARIABLES)
    def test_rule_loads_with_product(self, real_content_repo, rule_id):
        from content_agent.core.discovery.rules import RuleDiscovery

        rule = RuleDiscovery().get_rule_details(
            rule_id, product="ubuntu2204", include_rendered=False
        )
        assert rule is not None
        assert rule.title

    def test_product_variables_are_expanded(self, real_content_repo):
        from content_agent.core.discovery.rules import RuleDiscovery

        rule = RuleDiscovery().get_rule_details(
            "systemd_journal_upload_url", product="ubuntu2204", include_rendered=False
        )
        assert rule is not None
        assert rule.description.startswith("Ubuntu 22.04 must offload")
