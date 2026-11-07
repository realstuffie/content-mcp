"""Unit tests for rule validators."""

from content_agent.core.scaffolding.validators import RuleValidator, validate_rule_yaml


class TestRuleValidator:
    """Test RuleValidator class."""

    def test_valid_rule_yaml(self):
        """Test validation of valid rule YAML."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: This is a test rule
rationale: This is why we need this rule
severity: medium
references:
  nist:
    - AC-2(5)
    - SC-10
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_missing_required_fields(self):
        """Test validation with missing required fields."""
        yaml_content = """
title: Test Rule
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        assert result.valid is False
        assert len(result.errors) > 0

        # Check that missing fields are reported. documentation_complete is optional,
        # as in the content build.
        error_fields = [e.field for e in result.errors]
        assert "documentation_complete" not in error_fields
        assert "description" in error_fields

    def test_invalid_severity(self):
        """Test validation with invalid severity."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
severity: critical
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        assert result.valid is False
        severity_errors = [e for e in result.errors if e.field == "severity"]
        assert len(severity_errors) == 1
        assert "critical" in severity_errors[0].error

    def test_valid_severities(self):
        """Test all valid severity values."""
        valid_severities = ["low", "medium", "high", "unknown"]

        for severity in valid_severities:
            yaml_content = f"""
documentation_complete: true
title: Test Rule
description: Test description
severity: {severity}
"""
            validator = RuleValidator()
            result = validator.validate_yaml(yaml_content)

            # No severity errors
            severity_errors = [e for e in result.errors if e.field == "severity"]
            assert len(severity_errors) == 0

    def test_nist_reference_validation(self):
        """Test NIST reference format validation."""
        # Valid NIST references
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
references:
  nist:
    - AC-2(5)
    - SC-10
    - AU-12
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content, check_references=True)

        # Should have no errors for valid NIST refs
        nist_errors = [e for e in result.errors if "nist" in e.field.lower()]
        assert len(nist_errors) == 0

    def test_invalid_nist_reference_format(self):
        """Test invalid NIST reference format."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
references:
  nist:
    - AC-2.5
    - invalid-ref
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content, check_references=True)

        # Should have warnings for invalid NIST refs
        nist_warnings = [w for w in result.warnings if "nist" in w.field.lower()]
        assert len(nist_warnings) > 0

    def test_cce_validation(self):
        """Test CCE identifier validation."""
        # Valid CCE
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
identifiers:
  cce: CCE-12345-6
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        # No warnings for valid CCE
        cce_warnings = [w for w in result.warnings if "cce" in w.field.lower()]
        assert len(cce_warnings) == 0

    def test_invalid_cce_format(self):
        """Test invalid CCE format."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
identifiers:
  cce: INVALID-CCE
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        # Should have warning for invalid CCE
        cce_warnings = [w for w in result.warnings if "cce" in w.field.lower()]
        assert len(cce_warnings) > 0

    def test_recommended_fields_warning(self):
        """Test warnings for missing recommended fields."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        # Should have warnings for missing recommended fields
        assert len(result.warnings) > 0
        warning_fields = [w.field for w in result.warnings]
        assert "rationale" in warning_fields or "severity" in warning_fields

    def test_empty_field_value(self):
        """Test validation with empty field values."""
        yaml_content = """
documentation_complete: true
title:
description: Test description
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        assert result.valid is False
        title_errors = [e for e in result.errors if e.field == "title"]
        assert len(title_errors) == 1
        assert "empty" in title_errors[0].error.lower()

    def test_platform_and_platforms_warning(self):
        """Test warning for both platform and platforms."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
platform: machine
platforms:
  - machine
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        # Should have warning about both fields
        platform_warnings = [w for w in result.warnings if "platform" in w.field.lower()]
        assert len(platform_warnings) > 0

    def test_empty_list_warning(self):
        """Test warning for empty lists."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
products: []
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        # Should have warning about empty products list
        products_warnings = [w for w in result.warnings if w.field == "products"]
        assert len(products_warnings) > 0

    def test_invalid_yaml_syntax(self):
        """Test validation with invalid YAML syntax."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: [unclosed list
"""
        validator = RuleValidator()
        result = validator.validate_yaml(yaml_content)

        assert result.valid is False
        assert len(result.errors) > 0
        # Should have YAML parsing error
        yaml_errors = [e for e in result.errors if "yaml" in e.field.lower()]
        assert len(yaml_errors) > 0


class TestValidateRuleYamlFunction:
    """Test the validate_rule_yaml convenience function."""

    def test_function_call(self):
        """Test calling the validate_rule_yaml function."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
severity: high
"""
        result = validate_rule_yaml(yaml_content)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_check_references_parameter(self):
        """Test check_references parameter."""
        yaml_content = """
documentation_complete: true
title: Test Rule
description: Test description
references:
  nist:
    - invalid-format
"""
        # With reference checking
        result1 = validate_rule_yaml(yaml_content, check_references=True)
        nist_warnings1 = [w for w in result1.warnings if "nist" in w.field.lower()]

        # Without reference checking
        result2 = validate_rule_yaml(yaml_content, check_references=False)
        nist_warnings2 = [w for w in result2.warnings if "nist" in w.field.lower()]

        # Should have fewer warnings without reference checking
        assert len(nist_warnings1) > len(nist_warnings2)


class TestDocumentationComplete:
    """documentation_complete is checked the way the content build reads it."""

    RULE = "title: Test Rule\ndescription: A test rule\nrationale: Why\nseverity: medium\n"

    def _messages(self, line: str) -> tuple[bool, list[str]]:
        result = RuleValidator().validate_yaml(line + self.RULE)
        doc = [w.error for w in result.warnings if w.field == "documentation_complete"]
        return result.valid, doc

    def test_missing_is_complete(self):
        assert self._messages("") == (True, [])

    def test_true(self):
        assert self._messages("documentation_complete: true\n") == (True, [])

    def test_true_with_comment(self):
        line = "documentation_complete: true # switch to true when ready\n"
        assert self._messages(line) == (True, [])

    def test_false_leaves_the_rule_out(self):
        valid, messages = self._messages("documentation_complete: false\n")
        assert valid is True
        assert len(messages) == 1
        assert "leaves this rule out" in messages[0]

    def test_quoted_false_leaves_the_rule_out(self):
        valid, messages = self._messages("documentation_complete: 'false'\n")
        assert valid is True
        assert len(messages) == 1 and "leaves this rule out" in messages[0]

    def test_other_false_spellings_count_as_complete(self):
        for value in ("False", "no", "off"):
            valid, messages = self._messages(f"documentation_complete: {value}\n")
            assert valid is True
            assert len(messages) == 1 and "counts as complete" in messages[0], value

    def test_other_true_spellings(self):
        valid, messages = self._messages("documentation_complete: yes\n")
        assert valid is True
        assert messages == ["'yes' works, but rules write true"]
