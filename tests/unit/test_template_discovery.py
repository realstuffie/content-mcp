"""Unit tests for template discovery with documentation."""

from content_agent.core.discovery.templates import TemplateDiscovery
from content_agent.models import TemplateSchema

SAMPLE_REFERENCE_MD = """\
### Available Templates

#### accounts_password
-   Checks if PAM enforces password quality requirements.

-   Parameters:

    -   **variable** - PAM `pam_pwquality` password quality requirement

    -   **operation** - OVAL operation, eg. `less than or equal`

-   Languages: Ansible, Bash, OVAL

#### sshd_lineinfile
-   Checks configuration options of the SSH daemon.

-   Parameters:

    -   **parameter** - SSH configuration parameter name

    -   **value** - Expected value for the parameter

-   Languages: Ansible, Bash, OVAL
"""


class TestGetTemplateDocumentation:
    """Tests for _get_template_documentation method."""

    def test_returns_section_when_template_exists(self, initialized_content_repo):
        """Documentation is returned when template has an entry in reference file."""
        repo_path = initialized_content_repo.path
        ref_dir = repo_path / "docs" / "templates"
        ref_dir.mkdir(parents=True, exist_ok=True)
        (ref_dir / "template_reference.md").write_text(SAMPLE_REFERENCE_MD)

        discovery = TemplateDiscovery()
        result = discovery._get_template_documentation("accounts_password")

        assert result is not None
        assert "Checks if PAM enforces password quality requirements" in result
        assert "**variable**" in result
        assert "Languages: Ansible, Bash, OVAL" in result
        # Should not include the next template's content
        assert "sshd_lineinfile" not in result

    def test_returns_none_when_template_not_in_reference(self, initialized_content_repo):
        """None is returned when template has no entry in reference file."""
        repo_path = initialized_content_repo.path
        ref_dir = repo_path / "docs" / "templates"
        ref_dir.mkdir(parents=True, exist_ok=True)
        (ref_dir / "template_reference.md").write_text(SAMPLE_REFERENCE_MD)

        discovery = TemplateDiscovery()
        result = discovery._get_template_documentation("nonexistent_template")

        assert result is None

    def test_returns_none_when_reference_file_missing(self, initialized_content_repo):
        """None is returned when template_reference.md does not exist."""
        discovery = TemplateDiscovery()
        result = discovery._get_template_documentation("accounts_password")

        assert result is None

    def test_extracts_last_section(self, initialized_content_repo):
        """Last template section (no following ####) is extracted correctly."""
        repo_path = initialized_content_repo.path
        ref_dir = repo_path / "docs" / "templates"
        ref_dir.mkdir(parents=True, exist_ok=True)
        (ref_dir / "template_reference.md").write_text(SAMPLE_REFERENCE_MD)

        discovery = TemplateDiscovery()
        result = discovery._get_template_documentation("sshd_lineinfile")

        assert result is not None
        assert "SSH daemon" in result
        assert "**parameter**" in result


class TestGetTemplateSchemaWithDocumentation:
    """Tests for get_template_schema including documentation field."""

    def test_schema_includes_documentation(self, initialized_content_repo):
        """get_template_schema populates documentation field."""
        repo_path = initialized_content_repo.path

        # Create template directory
        template_dir = repo_path / "shared" / "templates" / "sshd_lineinfile"
        template_dir.mkdir(parents=True, exist_ok=True)

        # Create reference file
        ref_dir = repo_path / "docs" / "templates"
        ref_dir.mkdir(parents=True, exist_ok=True)
        (ref_dir / "template_reference.md").write_text(SAMPLE_REFERENCE_MD)

        discovery = TemplateDiscovery()
        schema = discovery.get_template_schema("sshd_lineinfile")

        assert schema is not None
        assert schema.documentation is not None
        assert "SSH daemon" in schema.documentation

    def test_schema_documentation_none_when_not_in_reference(self, initialized_content_repo):
        """get_template_schema sets documentation to None when not in reference."""
        repo_path = initialized_content_repo.path

        # Create template directory but no reference file
        template_dir = repo_path / "shared" / "templates" / "my_template"
        template_dir.mkdir(parents=True, exist_ok=True)

        discovery = TemplateDiscovery()
        schema = discovery.get_template_schema("my_template")

        assert schema is not None
        assert schema.documentation is None


class TestTemplateSchemaSerializationWithDocumentation:
    """Tests for TemplateSchema serialization with documentation field."""

    def test_serialization_includes_documentation(self):
        """model_dump includes documentation when populated."""
        schema = TemplateSchema(
            name="test_template",
            description="A test template",
            parameters=[],
            documentation="Some documentation text",
        )

        dumped = schema.model_dump(mode="json")
        assert "documentation" in dumped
        assert dumped["documentation"] == "Some documentation text"

    def test_serialization_with_none_documentation(self):
        """model_dump includes documentation key even when None."""
        schema = TemplateSchema(
            name="test_template",
            description="A test template",
            parameters=[],
        )

        dumped = schema.model_dump(mode="json")
        assert "documentation" in dumped
        assert dumped["documentation"] is None


PACKAGE_REFERENCE_MD = """\
### Available Templates

#### package_installed
-   Checks if a given package is installed.

-   Parameters:

    -   **pkgname** - name of the RPM or DEB package, eg. `tmux`

    -   **evr** - Optional parameter. Minimum version in
        `epoch:version-release` format.

-   Languages: Ansible, Bash, OVAL

#### sshd_lineinfile
-   Checks configuration options of the SSH daemon.

-   Parameters:

    -   **parameter** - name of the SSH configuration option

    -   **value** - value of the option. This cannot be specified
        together with **xccdf_variable**.

    -   **missing_parameter_pass** - if set to `"true"`, a missing option
        passes (default value: `"false"`).

-   Languages: Ansible, Bash, OVAL

#### key_value_pair_in_file
Checks if a given key and value are configured in a file.

Further notes on how the check works.

-   Parameters:

    -   **path** - path to the file

### Other notes

# not a template heading
"""


def _setup_templates(repo_path, reference=PACKAGE_REFERENCE_MD, templates=()):
    ref_dir = repo_path / "docs" / "templates"
    ref_dir.mkdir(parents=True, exist_ok=True)
    (ref_dir / "template_reference.md").write_text(reference)
    for name in templates:
        template_dir = repo_path / "shared" / "templates" / name
        template_dir.mkdir(parents=True, exist_ok=True)
        (template_dir / "template.yml").write_text("supported_languages:\n  - bash\n  - oval\n")


def _write_rule(repo_path, rule_id, template_block):
    rule_dir = repo_path / "linux_os" / "guide" / rule_id
    rule_dir.mkdir(parents=True, exist_ok=True)
    (rule_dir / "rule.yml").write_text(
        f"documentation_complete: true\n\ntitle: {rule_id}\n\nseverity: medium\n\n{template_block}"
    )


class TestTemplateParameters:
    """Parameters come from template_reference.md and from the rules using a template."""

    def test_documented_parameters_with_rule_usage(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["package_installed"])
        _write_rule(
            repo_path,
            "package_tmux_installed",
            "template:\n    name: package_installed\n    vars:\n        pkgname: tmux\n",
        )
        _write_rule(
            repo_path,
            "package_audit_installed",
            "template:\n    name: package_installed\n    vars:\n        pkgname: audit\n"
            "        pkgname@ubuntu2204: auditd\n        evr@ubuntu2204: 0:3.0-1\n",
        )

        schema = TemplateDiscovery().get_template_schema("package_installed")

        assert schema is not None
        assert schema.description == "Checks if a given package is installed."
        assert schema.supported_languages == ["bash", "oval"]
        assert schema.used_by_rules == 2
        assert [p.name for p in schema.parameters] == ["pkgname", "evr"]
        pkgname, evr = schema.parameters
        assert pkgname.required is True
        assert pkgname.type == "string"
        assert pkgname.used_by_rules == 2
        assert pkgname.description == "name of the RPM or DEB package, eg. `tmux`"
        assert evr.required is False
        assert evr.used_by_rules == 1
        assert "epoch:version-release" in (evr.description or "")
        # The example is a real rule, without product overrides
        assert schema.example_rule == "package_tmux_installed"
        assert schema.example_usage == {"pkgname": "tmux"}

    def test_parameter_some_rules_omit_is_not_required(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["sshd_lineinfile"])
        _write_rule(
            repo_path,
            "sshd_disable_root_login",
            "template:\n    name: sshd_lineinfile\n    vars:\n"
            "        parameter: PermitRootLogin\n        value: 'no'\n",
        )
        _write_rule(
            repo_path,
            "sshd_set_idle_timeout",
            "template:\n    name: sshd_lineinfile\n    vars:\n"
            "        parameter: ClientAliveInterval\n        xccdf_variable: var_timeout\n",
        )

        schema = TemplateDiscovery().get_template_schema("sshd_lineinfile")

        assert schema is not None
        by_name = {p.name: p for p in schema.parameters}
        assert by_name["parameter"].required is True
        # Not called optional in the reference, but one rule leaves it out
        assert by_name["value"].required is False
        missing = by_name["missing_parameter_pass"]
        assert missing.required is False
        assert missing.default == "false"
        assert missing.type == "unknown"
        undocumented = by_name["xccdf_variable"]
        assert undocumented.required is False
        assert undocumented.used_by_rules == 1
        assert "Not in template_reference.md" in (undocumented.description or "")

    def test_undocumented_template_parameters_from_rules(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["mount_option_home"])
        for rule_id, extra in [("mount_option_home_nosuid", ""), ("mount_option_home_noexec", "")]:
            _write_rule(
                repo_path,
                rule_id,
                "template:\n    name: mount_option_home\n    vars:\n"
                f"        mountoption: {rule_id.rsplit('_', 1)[1]}\n{extra}",
            )
        _write_rule(
            repo_path,
            "mount_option_home_nodev",
            "template:\n    name: mount_option_home\n    vars:\n"
            "        mountoption: nodev\n        no_remediation: true\n",
        )

        schema = TemplateDiscovery().get_template_schema("mount_option_home")

        assert schema is not None
        assert schema.documentation is None
        by_name = {p.name: p for p in schema.parameters}
        assert by_name["mountoption"].required is True
        assert by_name["mountoption"].used_by_rules == 3
        assert by_name["no_remediation"].required is False
        assert by_name["no_remediation"].type == "boolean"

    def test_rules_with_jinja_in_template_block(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["package_installed"])
        _write_rule(
            repo_path,
            "package_aide_installed",
            "template:\n    name: package_installed\n    vars:\n"
            "{{% if product == 'ubuntu2204' %}}\n        pkgname: aide-common\n"
            "{{% else %}}\n        pkgname: aide\n{{% endif %}}\n"
            "        evr: {{{ aide_version }}}\n",
        )
        _write_rule(
            repo_path,
            "package_tmux_installed",
            "template:\n    name: package_installed\n    vars:\n        pkgname: tmux\n",
        )

        schema = TemplateDiscovery().get_template_schema("package_installed")

        assert schema is not None
        assert schema.used_by_rules == 2
        assert {p.name: p.used_by_rules for p in schema.parameters} == {"pkgname": 2, "evr": 1}
        assert schema.example_rule == "package_tmux_installed"

    def test_description_from_opening_paragraph(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["key_value_pair_in_file"])

        schema = TemplateDiscovery().get_template_schema("key_value_pair_in_file")

        assert schema is not None
        assert schema.description == "Checks if a given key and value are configured in a file."
        assert [p.name for p in schema.parameters] == ["path"]
        # The section ends at the next heading
        assert "Other notes" not in (schema.documentation or "")

    def test_list_templates_has_descriptions(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["package_installed", "undocumented_template"])

        summaries = {s.name: s for s in TemplateDiscovery().list_templates()}

        assert summaries["package_installed"].description == (
            "Checks if a given package is installed."
        )
        assert summaries["undocumented_template"].description is None

    def test_no_invented_parameters(self, initialized_content_repo):
        # The old fallback returned a made-up "parameter" for templates it couldn't read
        repo_path = initialized_content_repo.path
        (repo_path / "shared" / "templates" / "bare_template").mkdir(parents=True)

        schema = TemplateDiscovery().get_template_schema("bare_template")

        assert schema is not None
        assert schema.parameters == []
        assert schema.supported_languages == []
        assert schema.example_usage is None

    def test_rule_changes_refresh_the_cache(self, initialized_content_repo):
        repo_path = initialized_content_repo.path
        _setup_templates(repo_path, templates=["package_installed"])
        _write_rule(
            repo_path,
            "package_tmux_installed",
            "template:\n    name: package_installed\n    vars:\n        pkgname: tmux\n",
        )
        discovery = TemplateDiscovery()
        first = discovery.get_template_schema("package_installed")
        _write_rule(
            repo_path,
            "package_aide_installed",
            "template:\n    name: package_installed\n    vars:\n        pkgname: aide\n",
        )

        second = discovery.get_template_schema("package_installed")

        assert first is not None and first.used_by_rules == 1
        assert second is not None and second.used_by_rules == 2
