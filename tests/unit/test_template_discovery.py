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
