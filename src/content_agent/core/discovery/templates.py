"""Template discovery implementation."""

import logging
from pathlib import Path

from content_agent.core.integration import get_content_repository
from content_agent.models import TemplateParameter, TemplateSchema, TemplateSummary

logger = logging.getLogger(__name__)


class TemplateDiscovery:
    """Template discovery and schema extraction."""

    def __init__(self) -> None:
        """Initialize template discovery."""
        self.content_repo = get_content_repository()

    def list_templates(self) -> list[TemplateSummary]:
        """List all available templates.

        Returns:
            List of TemplateSummary objects
        """
        logger.debug("Listing all templates")
        templates = []

        templates_dir = self.content_repo.path / "shared" / "templates"
        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return []

        for template_dir in templates_dir.iterdir():
            if not template_dir.is_dir():
                continue

            template_name = template_dir.name
            summary = TemplateSummary(
                name=template_name,
                description=self._extract_description(template_dir),
                language="jinja2",
                category=self._guess_category(template_name),
            )
            templates.append(summary)

        templates.sort(key=lambda t: t.name)
        logger.info(f"Found {len(templates)} templates")
        return templates

    def get_template_schema(self, template_name: str) -> TemplateSchema | None:
        """Get schema for a template.

        Args:
            template_name: Template name

        Returns:
            TemplateSchema or None if not found
        """
        logger.debug(f"Getting schema for template: {template_name}")

        templates_dir = self.content_repo.path / "shared" / "templates"
        template_dir = templates_dir / template_name

        if not template_dir.exists():
            logger.warning(f"Template not found: {template_name}")
            return None

        # Look for template.yml or csv file for schema
        config_file = template_dir / "template.yml"
        csv_file = template_dir / f"{template_name}.csv"

        parameters = []

        # Try to extract parameters from config
        if config_file.exists():
            parameters = self._extract_parameters_from_config(config_file)
        elif csv_file.exists():
            parameters = self._extract_parameters_from_csv(csv_file)
        else:
            # Fallback: basic parameter detection
            logger.warning(f"No configuration found for {template_name}, using basic detection")
            parameters = self._detect_basic_parameters(template_dir)

        description = self._extract_description(template_dir)

        schema = TemplateSchema(
            name=template_name,
            description=description,
            parameters=parameters,
            example_usage=self._get_example_usage(template_dir),
            documentation=self._get_template_documentation(template_name),
        )

        logger.debug(f"Loaded schema for template {template_name}")
        return schema

    def _extract_description(self, template_dir: Path) -> str | None:
        """Extract template description.

        Args:
            template_dir: Template directory

        Returns:
            Description or None
        """
        # Look for README or docstring in template files
        readme = template_dir / "README.md"
        if readme.exists():
            try:
                content = readme.read_text()
                # Get first paragraph
                lines = content.strip().split("\n\n")
                if lines:
                    return lines[0].replace("\n", " ").strip()
            except Exception as e:
                logger.warning(f"Failed to read template README {readme}: {e}")

        return None

    def _guess_category(self, template_name: str) -> str | None:
        """Guess template category from name.

        Args:
            template_name: Template name

        Returns:
            Category or None
        """
        # Simple category guessing based on name patterns
        if "sshd" in template_name or "ssh_" in template_name:
            return "ssh"
        elif "audit" in template_name:
            return "audit"
        elif "kernel" in template_name:
            return "kernel"
        elif "service" in template_name:
            return "services"
        elif "package" in template_name:
            return "packages"
        elif "file" in template_name or "permissions" in template_name:
            return "files"

        return None

    def _extract_parameters_from_config(self, config_file: Path) -> list[TemplateParameter]:
        """Extract parameters from template config file.

        Args:
            config_file: Path to template.yml

        Returns:
            List of TemplateParameter
        """
        # For MVP, return basic structure
        # Full implementation would parse template.yml format
        return []

    def _extract_parameters_from_csv(self, csv_file: Path) -> list[TemplateParameter]:
        """Extract parameters from CSV file.

        Args:
            csv_file: Path to CSV file

        Returns:
            List of TemplateParameter
        """
        import csv

        parameters = []

        try:
            with open(csv_file) as f:
                reader = csv.DictReader(f)
                # CSV format varies by template, use first row as example
                # Most templates have columns like: rule_id, param1, param2, ...
                if reader.fieldnames:
                    for field in reader.fieldnames:
                        if field == "rule_id":
                            continue
                        parameters.append(
                            TemplateParameter(
                                name=field,
                                type="string",
                                required=True,
                                description=f"Template parameter: {field}",
                            )
                        )
        except Exception as e:
            logger.warning(f"Failed to extract parameters from CSV: {e}")

        return parameters

    def _detect_basic_parameters(self, template_dir: Path) -> list[TemplateParameter]:
        """Detect basic parameters from template directory.

        Args:
            template_dir: Template directory

        Returns:
            List of TemplateParameter
        """
        # Basic fallback - most templates have some common parameters
        return [
            TemplateParameter(
                name="parameter",
                type="string",
                required=False,
                description="Template-specific parameter",
            )
        ]

    def _get_template_documentation(self, template_name: str) -> str | None:
        """Extract template documentation from template_reference.md.

        Finds the section headed by `#### <template_name>` and returns all content
        until the next `####` heading or end of file.

        Args:
            template_name: Template name to look up

        Returns:
            Documentation text or None if not found
        """
        ref_file = self.content_repo.path / "docs" / "templates" / "template_reference.md"
        if not ref_file.exists():
            logger.debug(f"Template reference file not found: {ref_file}")
            return None

        try:
            content = ref_file.read_text()
        except Exception as e:
            logger.warning(f"Failed to read template reference file: {e}")
            return None

        heading = f"#### {template_name}"
        lines = content.split("\n")
        start_idx = None

        for i, line in enumerate(lines):
            if line.strip() == heading:
                start_idx = i + 1
                break

        if start_idx is None:
            return None

        # Collect lines until next #### heading or end of file
        section_lines = []
        for i in range(start_idx, len(lines)):
            if lines[i].strip().startswith("####"):
                break
            section_lines.append(lines[i])

        # Strip leading/trailing blank lines
        text = "\n".join(section_lines).strip()
        return text if text else None

    def _get_example_usage(self, template_dir: Path) -> dict | None:
        """Get example usage for template.

        Args:
            template_dir: Template directory

        Returns:
            Example parameters dict or None
        """
        # Look for CSV file with examples
        csv_files = list(template_dir.glob("*.csv"))
        if csv_files:
            import csv

            try:
                with open(csv_files[0]) as f:
                    reader = csv.DictReader(f)
                    # Get first data row as example
                    for row in reader:
                        # Remove rule_id from example
                        example = {k: v for k, v in row.items() if k != "rule_id"}
                        return example if example else None
            except Exception as e:
                logger.warning(f"Failed to read template CSV example {csv_files[0]}: {e}")

        return None


def list_templates() -> list[TemplateSummary]:
    """List all available templates.

    Returns:
        List of TemplateSummary objects
    """
    discovery = TemplateDiscovery()
    return discovery.list_templates()


def get_template_schema(template_name: str) -> TemplateSchema | None:
    """Get schema for a template.

    Args:
        template_name: Template name

    Returns:
        TemplateSchema or None if not found
    """
    discovery = TemplateDiscovery()
    return discovery.get_template_schema(template_name)
