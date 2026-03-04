"""Control file generation implementation."""

import logging
from pathlib import Path
from typing import Literal

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
        format: Literal["inline", "directory"],
        output_dir: Path | None = None,
        source_document: str | None = None,
        description: str | None = None,
        version: str | None = None,
        levels: list[str] | None = None,
        product: str | None = None,
    ) -> ControlGenerationResult:
        """Generate control file structure from extracted requirements.

        Args:
            policy_id: Policy identifier
            policy_title: Policy title
            requirements: List of extracted requirements
            format: Output format - "inline" for a single monolithic file,
                    "directory" for a parent file with individual requirement files
            output_dir: Optional output directory (defaults to controls/)
            source_document: Source document path or URL
            description: Optional policy description
            version: Optional version string (e.g., 'v3r1')
            levels: Optional list of compliance levels (e.g., ['high', 'medium', 'low'])
            product: Optional product ID; when set, defaults output to
                     products/<product>/controls/ instead of controls/

        Returns:
            ControlGenerationResult with file paths and status
        """
        logger.info(f"Generating control structure for {policy_id} (format={format})")

        try:
            # Determine output directory
            if output_dir is None:
                if product is not None:
                    output_dir = self.content_repo.path / "products" / product / "controls"
                else:
                    output_dir = self.content_repo.path / "controls"
            else:
                output_dir = Path(output_dir)

            control_requirements = self._convert_to_control_requirements(requirements)

            if format == "inline":
                return self._generate_inline_file(
                    policy_id=policy_id,
                    policy_title=policy_title,
                    control_requirements=control_requirements,
                    output_dir=output_dir,
                    source_document=source_document,
                    version=version,
                    levels=levels,
                )
            else:
                return self._generate_directory_structure(
                    policy_id=policy_id,
                    policy_title=policy_title,
                    control_requirements=control_requirements,
                    output_dir=output_dir,
                    source_document=source_document,
                    description=description,
                    version=version,
                    levels=levels,
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

    def _generate_directory_structure(
        self,
        policy_id: str,
        policy_title: str,
        control_requirements: list[ControlRequirement],
        output_dir: Path,
        source_document: str | None = None,
        description: str | None = None,
        version: str | None = None,
        levels: list[str] | None = None,
    ) -> ControlGenerationResult:
        """Generate directory-based control file structure.

        Creates:
        - <output_dir>/<policy_id>.yml (parent with controls_dir reference)
        - <output_dir>/<policy_id>/<req>.yml (individual requirement files)
        """
        policy_dir = output_dir / policy_id
        parent_file_path = output_dir / f"{policy_id}.yml"

        if policy_dir.exists() or parent_file_path.exists():
            return ControlGenerationResult(
                policy_id=policy_id,
                parent_file_path=parent_file_path,
                requirement_files=[],
                total_requirements=0,
                sections=[],
                success=False,
                errors=[f"Control structure already exists: {policy_dir} or {parent_file_path}"],
                warnings=[],
            )

        policy_dir.mkdir(parents=True, exist_ok=True)

        requirement_files = []
        for idx, req in enumerate(control_requirements, 1):
            filename = self._generate_filename(req, idx)
            file_path = policy_dir / filename

            success = self.generate_requirement_file(req, file_path)
            if success:
                requirement_files.append(filename)

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
            f"Created directory control structure with {len(requirement_files)} requirements"
        )

        return ControlGenerationResult(
            policy_id=policy_id,
            parent_file_path=parent_file_path,
            requirement_files=[policy_dir / f for f in requirement_files],
            total_requirements=len(control_requirements),
            sections=[],
            success=True,
            errors=[],
            warnings=[],
        )

    def _generate_inline_file(
        self,
        policy_id: str,
        policy_title: str,
        control_requirements: list[ControlRequirement],
        output_dir: Path,
        source_document: str | None = None,
        version: str | None = None,
        levels: list[str] | None = None,
    ) -> ControlGenerationResult:
        """Generate a single monolithic control file with all requirements inline.

        Creates: <output_dir>/<policy_id>.yml with metadata and controls list.
        """
        file_path = output_dir / f"{policy_id}.yml"

        if file_path.exists():
            return ControlGenerationResult(
                policy_id=policy_id,
                parent_file_path=file_path,
                requirement_files=[],
                total_requirements=0,
                sections=[],
                success=False,
                errors=[f"Control file already exists: {file_path}"],
                warnings=[],
            )

        output_dir.mkdir(parents=True, exist_ok=True)

        content: dict = {
            "policy": policy_title,
            "title": policy_title,
            "id": policy_id,
        }

        if version:
            content["version"] = version

        if source_document:
            content["source"] = source_document

        if levels:
            content["levels"] = [{"id": level} for level in levels]
        else:
            content["levels"] = [
                {"id": "high"},
                {"id": "medium"},
                {"id": "low"},
            ]

        content["controls"] = [self._build_control_item(req) for req in control_requirements]

        with open(file_path, "w") as f:
            yaml.dump(
                content,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                indent=4,
                width=120,
            )

        logger.info(f"Created inline control file with {len(control_requirements)} requirements")

        return ControlGenerationResult(
            policy_id=policy_id,
            parent_file_path=file_path,
            requirement_files=[],
            total_requirements=len(control_requirements),
            sections=[],
            success=True,
            errors=[],
            warnings=[],
        )

    def _build_control_item(self, requirement: ControlRequirement) -> dict:
        """Build a control item dict from a requirement.

        Args:
            requirement: Control requirement

        Returns:
            Dictionary representing a single control item in ComplianceAsCode format
        """
        control_item: dict = {
            "id": requirement.id,
        }

        if requirement.levels:
            control_item["levels"] = requirement.levels

        control_item["title"] = folded_str(requirement.description)

        if requirement.rules:
            control_item["rules"] = requirement.rules

        control_item["status"] = requirement.status

        if requirement.related_rules:
            control_item["related_rules"] = requirement.related_rules

        if requirement.references:
            control_item["references"] = requirement.references

        if requirement.notes:
            control_item["notes"] = folded_str(requirement.notes)

        return control_item

    def generate_requirement_file(self, requirement: ControlRequirement, file_path: Path) -> bool:
        """Generate individual requirement control file in ComplianceAsCode format.

        Args:
            requirement: Control requirement
            file_path: Path to write file

        Returns:
            True if successful, False otherwise
        """
        try:
            control_item = self._build_control_item(requirement)
            content = {"controls": [control_item]}

            with open(file_path, "w") as f:
                yaml.dump(
                    content,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    indent=4,
                    width=120,
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
