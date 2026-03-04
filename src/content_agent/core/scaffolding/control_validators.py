"""Control file validation implementation."""

import logging
from pathlib import Path

import yaml

from content_agent.core.discovery.rules import RuleDiscovery
from content_agent.models.control import ControlFile, ControlValidationResult

logger = logging.getLogger(__name__)


class ControlValidator:
    """Validator for control files."""

    def __init__(self) -> None:
        """Initialize control validator."""
        self.rule_discovery = RuleDiscovery()

    def validate_control_file(self, file_path: Path) -> ControlValidationResult:
        """Validate control file YAML syntax and structure.

        Args:
            file_path: Path to control file

        Returns:
            ControlValidationResult with validation status
        """
        errors = []
        warnings = []

        try:
            # Check file exists
            if not file_path.exists():
                return ControlValidationResult(
                    valid=False,
                    errors=[f"Control file not found: {file_path}"],
                    warnings=[],
                    file_path=file_path,
                )

            # Parse YAML
            try:
                with open(file_path) as f:
                    control_data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                return ControlValidationResult(
                    valid=False,
                    errors=[f"Invalid YAML syntax: {e}"],
                    warnings=[],
                    file_path=file_path,
                )

            # Validate structure
            structure_result = self.validate_control_structure(control_data)
            errors.extend(structure_result.errors)
            warnings.extend(structure_result.warnings)

            # If structure is valid, check rule references
            if structure_result.valid:
                try:
                    control = ControlFile(**control_data)
                    rule_result = self.validate_rule_references(control)
                    errors.extend(rule_result.errors)
                    warnings.extend(rule_result.warnings)
                except Exception as e:
                    errors.append(f"Failed to parse control file: {e}")

            return ControlValidationResult(
                valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                file_path=file_path,
            )

        except Exception as e:
            logger.error(f"Validation error for {file_path}: {e}")
            return ControlValidationResult(
                valid=False,
                errors=[f"Validation failed: {e}"],
                warnings=[],
                file_path=file_path,
            )

    def validate_control_structure(self, control_data: dict) -> ControlValidationResult:
        """Validate control file schema.

        Args:
            control_data: Parsed control YAML data

        Returns:
            ControlValidationResult
        """
        errors = []
        warnings = []

        # Required fields
        required_fields = ["id", "title"]
        for field in required_fields:
            if field not in control_data:
                errors.append(f"Missing required field: {field}")

        # Validate ID format
        if "id" in control_data:
            control_id = control_data["id"]
            if not isinstance(control_id, str) or not control_id:
                errors.append("Control ID must be a non-empty string")

        # Validate title
        if "title" in control_data:
            title = control_data["title"]
            if not isinstance(title, str) or not title:
                errors.append("Control title must be a non-empty string")

        # Validate description if present
        if "description" in control_data:
            desc = control_data["description"]
            if not isinstance(desc, str):
                errors.append("Description must be a string")

        # Validate controls list if present
        if "controls" in control_data:
            controls = control_data["controls"]
            if not isinstance(controls, list):
                errors.append("Controls must be a list")
            else:
                for idx, ctrl in enumerate(controls):
                    if not isinstance(ctrl, dict):
                        errors.append(f"Control at index {idx} must be a dictionary")
                        continue

                    # Validate individual control requirement
                    if "id" not in ctrl:
                        errors.append(f"Control at index {idx} missing 'id' field")
                    if "description" not in ctrl:
                        warnings.append(
                            f"Control {ctrl.get('id', idx)} missing 'description' field"
                        )

        # Validate includes if present
        if "includes" in control_data:
            includes = control_data["includes"]
            if not isinstance(includes, list):
                errors.append("Includes must be a list")
            else:
                for include in includes:
                    if not isinstance(include, str):
                        errors.append(f"Include path must be a string: {include}")

        # Validate levels if present
        if "levels" in control_data:
            levels = control_data["levels"]
            if not isinstance(levels, list):
                errors.append("Levels must be a list")
            else:
                for idx, level in enumerate(levels):
                    if not isinstance(level, dict):
                        errors.append(f"Level at index {idx} must be a dictionary")
                        continue
                    if "id" not in level:
                        errors.append(f"Level at index {idx} missing 'id' field")

        return ControlValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_rule_references(
        self,
        control: ControlFile,
        available_rules: list[str] | None = None,
    ) -> ControlValidationResult:
        """Check that all referenced rules exist.

        Args:
            control: Control file to validate
            available_rules: Optional list of available rule IDs

        Returns:
            ControlValidationResult
        """
        errors = []
        warnings = []

        # Get available rules if not provided
        if available_rules is None:
            try:
                rule_results = self.rule_discovery.search_rules(limit=10000)
                available_rules = [r.rule_id for r in rule_results.items]
            except Exception as e:
                warnings.append(f"Could not load available rules: {e}")
                available_rules = []

        # Check all rule references in controls
        for control_req in control.controls:
            # Check rules
            for rule_id in control_req.rules:
                if rule_id not in available_rules:
                    errors.append(
                        f"Rule '{rule_id}' referenced in control '{control_req.id}' does not exist"
                    )

            # Check related_rules (warnings only)
            for rule_id in control_req.related_rules:
                if rule_id not in available_rules:
                    warnings.append(
                        f"Related rule '{rule_id}' in control '{control_req.id}' does not exist"
                    )

        return ControlValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def validate_control_directory(self, control_dir: Path) -> ControlValidationResult:
        """Validate all control files in a directory.

        Args:
            control_dir: Directory containing control files

        Returns:
            ControlValidationResult
        """
        errors = []
        warnings = []

        if not control_dir.exists():
            return ControlValidationResult(
                valid=False,
                errors=[f"Control directory not found: {control_dir}"],
                warnings=[],
            )

        # Find all YAML files
        yaml_files = list(control_dir.glob("**/*.yml")) + list(control_dir.glob("**/*.yaml"))

        if not yaml_files:
            warnings.append(f"No control files found in {control_dir}")

        # Validate each file
        for yaml_file in yaml_files:
            result = self.validate_control_file(yaml_file)
            if not result.valid:
                errors.append(f"Validation failed for {yaml_file}:")
                errors.extend(f"  - {e}" for e in result.errors)
            if result.warnings:
                warnings.append(f"Warnings for {yaml_file}:")
                warnings.extend(f"  - {w}" for w in result.warnings)

        return ControlValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
