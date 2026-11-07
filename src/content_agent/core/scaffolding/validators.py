"""Rule validation implementation."""

import logging
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml

from content_agent.models import ValidationError, ValidationResult

logger = logging.getLogger(__name__)


def _expand_rule_jinja(yaml_content: str) -> Any | None:
    """Expand ComplianceAsCode Jinja2 in rule YAML the way rule discovery does.

    Returns None when the content can't be expanded, for example when no content
    repository is initialized.
    """
    try:
        from content_agent.core.discovery.rules import RuleDiscovery

        discovery = RuleDiscovery()
    except Exception as e:
        logger.debug(f"Rule discovery unavailable for Jinja2 expansion: {e}")
        return None

    with tempfile.TemporaryDirectory() as tmp_dir:
        rule_path = Path(tmp_dir) / "rule.yml"
        rule_path.write_text(yaml_content)
        try:
            return discovery._load_rule_yaml(rule_path)
        except Exception as e:
            logger.debug(f"Jinja2 expansion of rule YAML failed: {e}")
            return None


def _restore_fields_lost_in_expansion(data: Any, yaml_content: str, fields: set[str]) -> Any:
    """Put back required fields that Jinja2 expansion emptied.

    A field whose value is only a macro, such as {{{ describe_timer_enable(...) }}},
    can expand to nothing without a product. A field the raw content defines
    counts as present.
    """
    if not isinstance(data, dict):
        return data
    restored = dict(data)
    for field in fields:
        if restored.get(field):
            continue
        if re.search(rf"^{re.escape(field)}:", yaml_content, re.MULTILINE):
            restored[field] = "(set by Jinja2)"
    return restored


# ComplianceAsCode's YAML loader keeps booleans as text, and the build skips a rule
# only when documentation_complete is exactly "false"
_DOCUMENTATION_COMPLETE = re.compile(
    r"^documentation_complete:[ \t]*(?P<value>[^#\n]*?)[ \t]*(?:#.*)?$", re.MULTILINE
)
_YAML_TRUE = {"y", "yes", "on", "true"}
_YAML_FALSE = {"n", "no", "off", "false"}


def _check_documentation_complete(yaml_content: str) -> list[ValidationError]:
    """Warn when documentation_complete won't do what its author likely means.

    The field is optional, and a rule without it is complete. With the exact text
    `false`, the content build leaves the rule out unless it is a Debug build. Any
    other value, including `False` or `no`, counts as complete.
    """
    match = _DOCUMENTATION_COMPLETE.search(yaml_content)
    if match is None:
        return []
    # Quoted or not, the build compares the scalar's text
    value = match["value"].strip("'\"")
    if value == "true":
        return []
    if value == "false":
        return [
            ValidationError(
                field="documentation_complete",
                error="documentation_complete is false, so the content build leaves this "
                "rule out, except in Debug builds",
                suggestion="Set it to true, or remove it, when the rule is ready",
            )
        ]
    if value.lower() in _YAML_FALSE:
        error = (
            f"The content build treats only the text false as incomplete; "
            f"'{match['value']}' counts as complete"
        )
        suggestion = "Write false to leave the rule out of the build"
    elif value.lower() in _YAML_TRUE:
        error = f"'{match['value']}' works, but rules write true"
        suggestion = "Write true"
    else:
        error = f"documentation_complete is '{match['value']}'; the build counts it as complete"
        suggestion = "Use true or false"
    return [ValidationError(field="documentation_complete", error=error, suggestion=suggestion)]


class RuleValidator:
    """Validator for rule.yml files."""

    # Valid severity values
    VALID_SEVERITIES = {"low", "medium", "high", "unknown"}

    # Required top-level fields. documentation_complete is optional: the content
    # build treats a rule without it as complete.
    REQUIRED_FIELDS = {"title", "description"}

    # Optional but recommended fields
    RECOMMENDED_FIELDS = {"rationale", "severity", "references"}

    def __init__(self) -> None:
        """Initialize rule validator."""
        pass

    def validate_yaml(
        self,
        yaml_content: str,
        check_references: bool = True,
        auto_fix: bool = False,
    ) -> ValidationResult:
        """Validate rule YAML content.

        Content that plain YAML can parse is validated as is, with any Jinja2 macros
        ({{{ }}}) treated as literal strings. When Jinja2 makes the content invalid YAML,
        as in many existing ComplianceAsCode rules, it is expanded the way rule
        discovery does without a product, and the expanded rule is validated.

        Args:
            yaml_content: YAML content to validate
            check_references: Whether to check reference format
            auto_fix: Whether to attempt auto-fixing issues

        Returns:
            ValidationResult
        """
        errors: list[ValidationError] = []
        warnings: list[ValidationError] = []
        fixes_applied: list[str] = []

        try:
            # Parse YAML, expanding Jinja2 when it makes the content invalid YAML
            try:
                data = yaml.safe_load(yaml_content)
            except yaml.YAMLError:
                expanded = _expand_rule_jinja(yaml_content) if "{{" in yaml_content else None
                if expanded is None:
                    raise
                data = _restore_fields_lost_in_expansion(
                    expanded, yaml_content, self.REQUIRED_FIELDS
                )
                warnings.append(
                    ValidationError(
                        field="yaml",
                        error="Validated after expanding Jinja2 without a product",
                        suggestion="Product-specific content was not checked",
                    )
                )

            if not isinstance(data, dict):
                errors.append(
                    ValidationError(
                        field="root",
                        error="Rule YAML must be a dictionary/object",
                        suggestion="Ensure the file contains valid YAML with key-value pairs",
                    )
                )
                return ValidationResult(
                    valid=False, errors=errors, warnings=warnings, fixes_applied=fixes_applied
                )

            # Check required fields
            errors.extend(self._check_required_fields(data))

            # Check recommended fields
            warnings.extend(self._check_recommended_fields(data))

            # Validate severity
            if "severity" in data:
                severity_errors = self._validate_severity(data["severity"])
                errors.extend(severity_errors)

            # Validate references
            if check_references and "references" in data:
                ref_warnings = self._validate_references(data["references"])
                warnings.extend(ref_warnings)

            # Validate identifiers
            if "identifiers" in data:
                id_warnings = self._validate_identifiers(data["identifiers"])
                warnings.extend(id_warnings)

            # Check for common mistakes
            warnings.extend(self._check_common_mistakes(data))
            warnings.extend(_check_documentation_complete(yaml_content))

        except yaml.YAMLError as e:
            errors.append(
                ValidationError(
                    field="yaml",
                    error=f"YAML parsing error: {e}",
                    suggestion="Fix YAML syntax errors",
                )
            )
        except Exception as e:
            errors.append(
                ValidationError(
                    field="validation",
                    error=f"Validation error: {e}",
                )
            )

        valid = len(errors) == 0
        return ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            fixes_applied=fixes_applied,
        )

    def _check_required_fields(self, data: dict) -> list[ValidationError]:
        """Check for required fields.

        Args:
            data: Parsed YAML data

        Returns:
            List of validation errors
        """
        errors = []

        for field in self.REQUIRED_FIELDS:
            if field not in data:
                errors.append(
                    ValidationError(
                        field=field,
                        error=f"Required field '{field}' is missing",
                        suggestion=f"Add '{field}' field to the rule",
                    )
                )
            elif not data[field]:
                errors.append(
                    ValidationError(
                        field=field,
                        error=f"Required field '{field}' is empty",
                        suggestion=f"Provide a value for '{field}'",
                    )
                )

        return errors

    def _check_recommended_fields(self, data: dict) -> list[ValidationError]:
        """Check for recommended fields.

        Args:
            data: Parsed YAML data

        Returns:
            List of validation warnings
        """
        warnings = []

        for field in self.RECOMMENDED_FIELDS:
            if field not in data:
                warnings.append(
                    ValidationError(
                        field=field,
                        error=f"Recommended field '{field}' is missing",
                        suggestion=f"Consider adding '{field}' field",
                    )
                )

        return warnings

    def _validate_severity(self, severity: str) -> list[ValidationError]:
        """Validate severity value.

        Args:
            severity: Severity value

        Returns:
            List of validation errors
        """
        errors = []

        if severity not in self.VALID_SEVERITIES:
            errors.append(
                ValidationError(
                    field="severity",
                    error=f"Invalid severity value '{severity}'",
                    suggestion=f"Use one of: {', '.join(sorted(self.VALID_SEVERITIES))}",
                )
            )

        return errors

    def _validate_references(self, references: dict) -> list[ValidationError]:
        """Validate reference format.

        Args:
            references: References dict

        Returns:
            List of validation warnings
        """
        warnings = []

        # Check NIST format
        if "nist" in references:
            nist_refs = references["nist"]
            if isinstance(nist_refs, list):
                for ref in nist_refs:
                    if not self._is_valid_nist_reference(ref):
                        warnings.append(
                            ValidationError(
                                field="references.nist",
                                error=f"NIST reference '{ref}' may have incorrect format",
                                suggestion="Use format like 'AC-2(5)' or 'SC-10'",
                            )
                        )

        return warnings

    def _is_valid_nist_reference(self, ref: str) -> bool:
        """Check if NIST reference is valid format.

        Args:
            ref: Reference string

        Returns:
            True if valid format
        """
        # NIST format: XX-## or XX-##(##)
        pattern = r"^[A-Z]{2}-\d+(\(\d+\))?$"
        return bool(re.match(pattern, ref))

    def _validate_identifiers(self, identifiers: dict) -> list[ValidationError]:
        """Validate identifier format.

        Args:
            identifiers: Identifiers dict

        Returns:
            List of validation warnings
        """
        warnings = []

        # Check CCE format
        if "cce" in identifiers:
            cce = identifiers["cce"]
            if isinstance(cce, list) and cce:
                cce = cce[0]
            if isinstance(cce, str) and not self._is_valid_cce(cce):
                warnings.append(
                    ValidationError(
                        field="identifiers.cce",
                        error=f"CCE identifier '{cce}' may have incorrect format",
                        suggestion="Use format like 'CCE-12345-6'",
                    )
                )

        return warnings

    def _is_valid_cce(self, cce: str) -> bool:
        """Check if CCE is valid format.

        Args:
            cce: CCE string

        Returns:
            True if valid format
        """
        # CCE format: CCE-#####-#
        pattern = r"^CCE-\d{5}-\d$"
        return bool(re.match(pattern, cce))

    def _check_common_mistakes(self, data: dict) -> list[ValidationError]:
        """Check for common mistakes.

        Args:
            data: Parsed YAML data

        Returns:
            List of validation warnings
        """
        warnings = []

        # Check for platform vs platforms
        if "platform" in data and "platforms" in data:
            warnings.append(
                ValidationError(
                    field="platform/platforms",
                    error="Both 'platform' and 'platforms' are defined",
                    suggestion="Use only 'platform' field",
                )
            )

        # Check for empty lists
        for field in ["products", "platforms"]:
            if field in data and isinstance(data[field], list) and not data[field]:
                warnings.append(
                    ValidationError(
                        field=field,
                        error=f"Field '{field}' is an empty list",
                        suggestion=f"Either remove '{field}' or add values",
                    )
                )

        return warnings


def validate_rule_yaml(
    yaml_content: str,
    check_references: bool = True,
    auto_fix: bool = False,
) -> ValidationResult:
    """Validate rule YAML content.

    Args:
        yaml_content: YAML content to validate
        check_references: Whether to check reference format
        auto_fix: Whether to attempt auto-fixing issues

    Returns:
        ValidationResult
    """
    validator = RuleValidator()
    return validator.validate_yaml(yaml_content, check_references, auto_fix)
