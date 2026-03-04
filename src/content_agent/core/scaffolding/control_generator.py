"""Control file generation implementation."""

import logging
from pathlib import Path

import yaml

from content_agent.core.integration import get_content_repository
from content_agent.models.control import (
    ControlGenerationResult,
    ControlRequirement,
    ExtractedRequirement,
)

logger = logging.getLogger(__name__)


# Custom YAML representer for better multi-line string formatting
class folded_str(str):
    """String subclass that will be represented as folded scalar in YAML."""

    pass


def folded_str_representer(dumper, data):
    """Represent folded_str as folded scalar (>)."""
    if "\n" in data or len(data) > 80:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=">")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# Register the custom representer
yaml.add_representer(folded_str, folded_str_representer)


class ControlGenerator:
    """Generator for control file structures."""

    def __init__(self) -> None:
        """Initialize control generator."""
        self.content_repo = get_content_repository()

    def generate_control_structure(
        self,
        policy_id: str,
        policy_title: str,
        requirements: list[ExtractedRequirement],
        output_dir: Path | None = None,
        nested_by_section: bool = False,  # Deprecated, kept for compatibility
        source_document: str | None = None,
        description: str | None = None,
        version: str | None = None,
        levels: list[str] | None = None,
        product: str | None = None,
    ) -> ControlGenerationResult:
        """Generate control file structure with individual requirement files.

        Creates flat structure as required by ComplianceAsCode:
        - controls/<policy_id>/req1.yml
        - controls/<policy_id>/req2.yml
        - controls/<policy_id>.yml (parent with controls_dir reference)

        Args:
            policy_id: Policy identifier
            policy_title: Policy title
            requirements: List of extracted requirements
            output_dir: Optional output directory (defaults to controls/)
            nested_by_section: Deprecated, always uses flat structure
            source_document: Source document path or URL
            description: Optional policy description
            version: Optional version string (e.g., 'v3r1')
            levels: Optional list of compliance levels (e.g., ['high', 'medium', 'low'])
            product: Optional product ID; when set, defaults output to
                     products/<product>/controls/ instead of controls/

        Returns:
            ControlGenerationResult with file paths and status
        """
        logger.info(f"Generating control structure for {policy_id} (product={product})")

        try:
            # Determine output directory
            if output_dir is None:
                if product is not None:
                    output_dir = self.content_repo.path / "products" / product / "controls"
                else:
                    output_dir = self.content_repo.path / "controls"
            else:
                output_dir = Path(output_dir)

            policy_dir = output_dir / policy_id
            parent_file_path = output_dir / f"{policy_id}.yml"

            # Check if already exists
            if policy_dir.exists() or parent_file_path.exists():
                return ControlGenerationResult(
                    policy_id=policy_id,
                    parent_file_path=parent_file_path,
                    requirement_files=[],
                    total_requirements=0,
                    sections=[],
                    success=False,
                    errors=[
                        f"Control structure already exists: {policy_dir} or {parent_file_path}"
                    ],
                    warnings=[],
                )

            # Create flat directory structure
            policy_dir.mkdir(parents=True, exist_ok=True)

            # Convert ExtractedRequirement to ControlRequirement
            control_requirements = self._convert_to_control_requirements(requirements)

            # Generate individual requirement files (flat structure)
            requirement_files = []

            for idx, req in enumerate(control_requirements, 1):
                # Generate filename from requirement ID or index
                filename = self._generate_filename(req, idx)
                file_path = policy_dir / filename

                # Generate requirement file
                success = self.generate_requirement_file(req, file_path)
                if success:
                    # Store relative path from policy_dir (just filename for flat structure)
                    requirement_files.append(filename)

            # Generate parent control file
            parent_success = self.generate_parent_control_file(
                policy_id=policy_id,
                policy_title=policy_title,
                requirement_files=requirement_files,
                output_path=parent_file_path,
                source_document=source_document,
                description=description,
                version=version,
                levels=levels,
            )

            if not parent_success:
                return ControlGenerationResult(
                    policy_id=policy_id,
                    parent_file_path=parent_file_path,
                    requirement_files=[policy_dir / f for f in requirement_files],
                    total_requirements=len(control_requirements),
                    sections=[],
                    success=False,
                    errors=["Failed to generate parent control file"],
                    warnings=[],
                )

            logger.info(
                f"Created flat control structure with {len(requirement_files)} requirements"
            )

            return ControlGenerationResult(
                policy_id=policy_id,
                parent_file_path=parent_file_path,
                requirement_files=[policy_dir / f for f in requirement_files],
                total_requirements=len(control_requirements),
                sections=[],  # No sections in flat structure
                success=True,
                errors=[],
                warnings=[],
            )

        except Exception as e:
            logger.error(f"Failed to generate control structure: {e}")
            return ControlGenerationResult(
                policy_id=policy_id,
                parent_file_path=Path(),
                requirement_files=[],
                total_requirements=0,
                sections=[],
                success=False,
                errors=[str(e)],
                warnings=[],
            )

    def generate_requirement_file(self, requirement: ControlRequirement, file_path: Path) -> bool:
        """Generate individual requirement control file in ComplianceAsCode format.

        Args:
            requirement: Control requirement
            file_path: Path to write file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Build control item following ComplianceAsCode format
            control_item = {
                "id": requirement.id,
            }

            # Add levels if specified
            if requirement.levels:
                control_item["levels"] = requirement.levels

            # Use description as title (full requirement text)
            # Wrap in folded_str for better multi-line formatting
            control_item["title"] = folded_str(requirement.description)

            # Add rules if present
            if requirement.rules:
                control_item["rules"] = requirement.rules

            # Add status
            control_item["status"] = requirement.status

            # Add optional fields
            if requirement.related_rules:
                control_item["related_rules"] = requirement.related_rules

            if requirement.references:
                control_item["references"] = requirement.references

            if requirement.notes:
                # Use folded_str for notes too
                control_item["notes"] = folded_str(requirement.notes)

            # Wrap in controls list (ComplianceAsCode format)
            content = {"controls": [control_item]}

            # Write YAML file with proper formatting
            with open(file_path, "w") as f:
                yaml.dump(
                    content,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=4,
                    width=120,  # Wider line width for longer titles
                )

            logger.debug(f"Created requirement file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create requirement file {file_path}: {e}")
            return False

    def generate_parent_control_file(
        self,
        policy_id: str,
        policy_title: str,
        requirement_files: list[str],
        output_path: Path,
        description: str | None = None,
        source_document: str | None = None,
        version: str | None = None,
        levels: list[str] | None = None,
    ) -> bool:
        """Generate parent control file in ComplianceAsCode format.

        Generates a parent control file that references the controls directory
        containing individual requirement files.

        Args:
            policy_id: Policy identifier
            policy_title: Policy title
            requirement_files: List of requirement filenames (not used, kept for compatibility)
            output_path: Path to write parent file
            description: Optional policy description
            source_document: Optional source document path/URL
            version: Optional version string (e.g., 'v3r1')
            levels: Optional list of compliance levels (e.g., ['high', 'medium', 'low'])

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent control file content in ComplianceAsCode format
            content = {
                "policy": policy_title,
                "title": policy_title,
                "id": policy_id,
            }

            # Add optional version
            if version:
                content["version"] = version

            # Add source
            if source_document:
                content["source"] = source_document

            # Add controls_dir (references the directory with individual files)
            content["controls_dir"] = policy_id

            # Add levels
            if levels:
                content["levels"] = [{"id": level} for level in levels]
            else:
                # Default levels
                content["levels"] = [
                    {"id": "high"},
                    {"id": "medium"},
                    {"id": "low"},
                ]

            # Write YAML file
            with open(output_path, "w") as f:
                yaml.dump(
                    content,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=4,
                )

            logger.info(f"Created parent control file: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create parent control file {output_path}: {e}")
            return False

    def _convert_to_control_requirements(
        self, extracted: list[ExtractedRequirement]
    ) -> list[ControlRequirement]:
        """Convert ExtractedRequirement to ControlRequirement.

        Args:
            extracted: List of extracted requirements

        Returns:
            List of control requirements
        """
        requirements = []

        for idx, req in enumerate(extracted, 1):
            # Generate ID if not present
            req_id = req.potential_id or f"REQ-{idx:03d}"

            # Extract title from first line or use ID
            title_parts = req.text.split("\n", 1)
            title = title_parts[0][:100] if title_parts else req_id

            control_req = ControlRequirement(
                id=req_id,
                title=title,
                description=req.text,
                section=req.section_id,
                notes=req.context,  # Add context as notes if provided
            )

            requirements.append(control_req)

        return requirements

    def _group_by_section(
        self, requirements: list[ControlRequirement]
    ) -> dict[str, list[ControlRequirement]]:
        """Group requirements by section.

        Args:
            requirements: List of requirements

        Returns:
            Dictionary mapping section ID to requirements
        """
        sections: dict[str, list[ControlRequirement]] = {}

        for req in requirements:
            section_id = req.section or "default"
            # Clean section ID for filesystem
            section_id = self._clean_section_id(section_id)

            if section_id not in sections:
                sections[section_id] = []
            sections[section_id].append(req)

        return sections

    def _clean_section_id(self, section_id: str) -> str:
        """Clean section ID for use as directory name.

        Args:
            section_id: Section identifier

        Returns:
            Cleaned section ID
        """
        # Replace special characters with underscores
        clean = "".join(c if c.isalnum() or c in "-_" else "_" for c in section_id)
        # Remove consecutive underscores
        clean = "_".join(filter(None, clean.split("_")))
        # Limit length
        return clean[:50].lower()

    def _generate_filename(self, requirement: ControlRequirement, index: int) -> str:
        """Generate filename for requirement.

        Args:
            requirement: Control requirement
            index: Index in section

        Returns:
            Filename (e.g., "req_001.yml" or "ac_2_5.yml")
        """
        # Try to use requirement ID
        if requirement.id and requirement.id != f"REQ-{index:03d}":
            # Clean ID for filename
            clean_id = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in requirement.id.lower()
            )
            clean_id = "_".join(filter(None, clean_id.split("_")))
            return f"{clean_id}.yml"

        # Fall back to index-based name
        return f"req_{index:03d}.yml"
