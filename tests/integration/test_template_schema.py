"""Integration tests for template schemas against a real content repository."""

from tests.conftest import requires_content_repo


@requires_content_repo
class TestTemplateSchemaWithRealContent:
    def test_package_installed(self, real_content_repo):
        from content_agent.core.discovery.templates import TemplateDiscovery

        schema = TemplateDiscovery().get_template_schema("package_installed")

        assert schema is not None
        by_name = {p.name: p for p in schema.parameters}
        assert by_name["pkgname"].required is True
        assert by_name["evr"].required is False
        assert "oval" in schema.supported_languages
        assert schema.used_by_rules > 50
        assert schema.example_usage is not None
        assert "pkgname" in schema.example_usage

    def test_parameters_some_rules_omit_are_optional(self, real_content_repo):
        from content_agent.core.discovery.templates import TemplateDiscovery

        schema = TemplateDiscovery().get_template_schema("sshd_lineinfile")

        assert schema is not None
        by_name = {p.name: p for p in schema.parameters}
        assert by_name["parameter"].required is True
        # Rules set either value or xccdf_variable
        assert by_name["value"].required is False
        assert by_name["xccdf_variable"].required is False

    def test_template_without_documented_parameters(self, real_content_repo):
        from content_agent.core.discovery.templates import TemplateDiscovery

        # The reference has a section for this template but no parameter list
        schema = TemplateDiscovery().get_template_schema("systemd_dropin_configuration")

        assert schema is not None
        assert schema.documentation is not None
        names = {p.name for p in schema.parameters}
        assert {"param", "value"} <= names

    def test_every_templated_rule_is_read(self, real_content_repo):
        from content_agent.core.discovery.templates import _rule_files, template_uses

        templated = [
            f for f in _rule_files(real_content_repo.path) if "\ntemplate:" in f.read_text()
        ]
        uses = template_uses(real_content_repo.path)

        assert sum(len(rules) for rules in uses.values()) == len(templated)

    def test_list_templates_describes_documented_templates(self, real_content_repo):
        from content_agent.core.discovery.templates import TemplateDiscovery

        summaries = TemplateDiscovery().list_templates()

        assert len([s for s in summaries if s.description]) > 40
