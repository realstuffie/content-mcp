"""Tests for validating rule YAML that needs Jinja2 expansion."""

from unittest.mock import patch

from content_agent.core.scaffolding.validators import validate_rule_yaml

RULE_WITH_JINJA = """documentation_complete: true

title: 'Enable logrotate Timer'

description: |-
    {{{ describe_timer_enable(timer="logrotate") }}}

severity: medium

{{% if 'rhel' in product %}}
platform: package[logrotate]
{{% endif %}}
"""


class FakeDiscovery:
    """Returns what ssg's loader gives without a product: documentation_complete is
    removed and the macro-only description expands to nothing."""

    def _load_rule_yaml(self, path):
        assert path.read_text() == RULE_WITH_JINJA
        return {"title": "Enable logrotate Timer", "description": "", "severity": "medium"}


def test_jinja_rule_is_expanded_and_validated():
    with patch("content_agent.core.discovery.rules.RuleDiscovery", return_value=FakeDiscovery()):
        result = validate_rule_yaml(RULE_WITH_JINJA, check_references=False)

    assert result.valid is True
    assert result.errors == []
    assert [w.error for w in result.warnings if w.field == "yaml"] == [
        "Validated after expanding Jinja2 without a product"
    ]


def test_yaml_error_kept_when_expansion_is_unavailable():
    with patch(
        "content_agent.core.discovery.rules.RuleDiscovery",
        side_effect=RuntimeError("Content repository not initialized"),
    ):
        result = validate_rule_yaml(RULE_WITH_JINJA)

    assert result.valid is False
    assert result.errors[0].field == "yaml"


def test_plain_yaml_is_not_expanded():
    with patch("content_agent.core.discovery.rules.RuleDiscovery") as discovery:
        result = validate_rule_yaml(
            "documentation_complete: true\ntitle: T\ndescription: '{{{ full_name }}} rule'\n"
        )

    discovery.assert_not_called()
    assert result.valid is True
