"""Tests for parsing the selections of profile files."""

from unittest.mock import MagicMock, patch

PROFILE = """documentation_complete: true

title: 'Example'

description: |-
    An example profile.

selections:
    ### Variables
    - var_rekey_limit_size=1G
    # SSH
    - sshd_set_idle_timeout  # inline comment
{{% if product == "rhel9" %}}
    - rhel9_only_rule
{{% else %}}
    - other_product_rule
{{% endif %}}
    - '!quoted_unselection'
    - "quoted_rule"
    - cis_rhel9:all:l2_server
"""


@patch("content_agent.core.discovery.profiles.get_content_repository", MagicMock())
def _parse(content):
    from content_agent.core.discovery.profiles import ProfileDiscovery

    return ProfileDiscovery()._parse_profile(content)


class TestProfileSelectionParsing:
    def test_comments_and_jinja_blocks_keep_the_section_open(self):
        assert _parse(PROFILE)["selections"] == [
            "var_rekey_limit_size=1G",
            "sshd_set_idle_timeout",
            "rhel9_only_rule",
            "other_product_rule",
            "!quoted_unselection",
            "quoted_rule",
            "cis_rhel9:all:l2_server",
        ]

    def test_section_ends_at_next_top_level_key(self):
        content = "selections:\n    - rule_a\nextends: base\n"
        data = _parse(content)
        assert data["selections"] == ["rule_a"]
        assert data["extends"] == "base"


class TestFilterRulesParsing:
    def test_single_line(self):
        data = _parse("filter_rules: '\"kubevirt\" not in id_'\nselections:\n    - rule_a\n")
        assert data["filter_rules"] == '"kubevirt" not in id_'
        assert data["selections"] == ["rule_a"]

    def test_continued_on_indented_lines(self):
        content = (
            'filter_rules: \'"ocp4-node" not in platform and "ocp4-master-node"\n'
            "    not in platform'\n"
            "selections:\n"
            "    - cis_ocp_200:all\n"
        )
        data = _parse(content)
        assert (
            data["filter_rules"]
            == '"ocp4-node" not in platform and "ocp4-master-node" not in platform'
        )
        assert data["selections"] == ["cis_ocp_200:all"]

    def test_absent(self):
        assert _parse("selections:\n    - rule_a\n")["filter_rules"] is None
