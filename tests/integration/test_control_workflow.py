"""Integration tests for control file generation workflow using real policy document."""

import tempfile
from pathlib import Path

import pytest

from content_agent.core.parsing import PDFParser
from content_agent.core.scaffolding.control_generator import ControlGenerator
from content_agent.core.scaffolding.control_validators import ControlValidator
from content_agent.models.control import ExtractedRequirement

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"
ITSAR_PDF = FIXTURES_DIR / "ITSAR701012411.pdf"


@pytest.mark.skipif(not ITSAR_PDF.exists(), reason="ITSAR PDF fixture not found")
class TestITSARWorkflow:
    """Integration tests using ITSAR policy document."""

    def test_parse_itsar_pdf(self):
        """Test parsing the ITSAR PDF document."""
        parser = PDFParser()
        doc = parser.parse(ITSAR_PDF)

        # Verify basic document parsing
        assert doc.title == "Indian Telecom Security Assurance Requirements (ITSAR)"
        assert doc.source_type == "pdf"
        assert len(doc.sections) > 0
        assert doc.metadata["page_count"] == 51

        # Verify metadata extraction
        assert doc.metadata["author"] == "ra10"
        assert "Microsoft" in doc.metadata["creator"]

    def test_extract_text_from_itsar(self):
        """Test text extraction from ITSAR PDF."""
        parser = PDFParser()
        text = parser.extract_text(ITSAR_PDF)

        # Verify text was extracted
        assert len(text) > 1000
        assert "ITSAR" in text
        assert "operating system" in text.lower()

        # Verify we can find requirement keywords
        assert "shall" in text.lower() or "must" in text.lower()

    def test_section_detection(self):
        """Test that sections are properly detected."""
        parser = PDFParser()
        doc = parser.parse(ITSAR_PDF)

        # Should have multiple top-level sections
        assert len(doc.sections) >= 10

        # Check for expected section patterns
        section_titles = [s.title for s in doc.sections]

        # Should contain numbered sections (e.g., "2.10.7. No automatic launch...")
        numbered_sections = [s for s in section_titles if any(c.isdigit() for c in s[:10])]
        assert len(numbered_sections) > 0

    def test_create_sample_requirements(self):
        """Test creating requirements from ITSAR content."""
        # Manually create some sample requirements based on ITSAR structure
        requirements = [
            ExtractedRequirement(
                text="The operating system shall implement ASLR (Address Space Layout Randomization) and KASLR (Kernel Address Space Layout Randomization) to protect against memory-based attacks.",
                section_id="security_features",
                section_title="2.11 Security Features",
                potential_id="ITSAR-2.11.1",
            ),
            ExtractedRequirement(
                text="The operating system must implement IMA (Integrity Measurement Architecture) to ensure system integrity.",
                section_id="security_features",
                section_title="2.11 Security Features",
                potential_id="ITSAR-2.11.2",
            ),
            ExtractedRequirement(
                text="No Root Password Recovery shall be allowed in the operating system.",
                section_id="system_integrity",
                section_title="2.12 System Integrity",
                potential_id="ITSAR-2.12.1",
            ),
        ]

        # Verify requirement structure
        assert len(requirements) == 3
        for req in requirements:
            assert req.text
            assert req.section_id
            assert req.potential_id

    def test_generate_control_files_from_requirements(self):
        """Test generating control files from sample requirements."""
        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Sample requirements
            requirements = [
                ExtractedRequirement(
                    text="The operating system shall implement ASLR and KASLR.",
                    section_id="security_features",
                    section_title="Security Features",
                    potential_id="ITSAR-2.11.1",
                ),
                ExtractedRequirement(
                    text="The operating system must implement IMA.",
                    section_id="security_features",
                    section_title="Security Features",
                    potential_id="ITSAR-2.11.2",
                ),
            ]

            # Generate control structure (flat)
            generator = ControlGenerator.__new__(ControlGenerator)
            result = generator.generate_control_structure(
                policy_id="itsar_os",
                policy_title="ITSAR Operating System Requirements",
                requirements=requirements,
                format="directory",
                output_dir=output_dir,
                source_document="ITSAR701012411.pdf",
            )

            # Verify generation succeeded
            assert result.success is True
            assert result.total_requirements == 2
            assert len(result.requirement_files) == 2

            # Verify parent file was created
            assert result.parent_file_path.exists()

            # Verify requirement files were created
            for req_file in result.requirement_files:
                assert req_file.exists()
                assert req_file.suffix == ".yml"

    def test_validate_generated_controls(self):
        """Test validating generated control files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Generate sample controls
            requirements = [
                ExtractedRequirement(
                    text="The operating system shall implement ASLR.",
                    section_id="security",
                    section_title="Security",
                    potential_id="ITSAR-001",
                ),
            ]

            generator = ControlGenerator.__new__(ControlGenerator)
            result = generator.generate_control_structure(
                policy_id="test_itsar",
                policy_title="Test ITSAR",
                requirements=requirements,
                format="directory",
                output_dir=output_dir,
                source_document="test.pdf",
            )

            assert result.success

            # Validate the generated files
            validator = ControlValidator.__new__(ControlValidator)
            validator.rule_discovery = None

            validation = validator.validate_control_file(result.parent_file_path)

            # Should be valid (might have warnings about missing rules, but structure should be valid)
            assert validation.valid or len(validation.errors) == 0

    def test_requirement_text_preservation(self):
        """Test that requirement text is preserved exactly."""
        original_text = "The operating system shall implement ASLR (Address Space Layout Randomization) and KASLR (Kernel Address Space Layout Randomization) to protect against memory-based attacks."

        requirement = ExtractedRequirement(
            text=original_text,
            section_id="security",
            section_title="Security",
            potential_id="ITSAR-001",
        )

        # Verify text is preserved exactly
        assert requirement.text == original_text
        assert len(requirement.text) == len(original_text)

    def test_itsar_conventions_parsing(self):
        """Test that we can extract the conventions/terminology from ITSAR."""
        parser = PDFParser()
        text = parser.extract_text(ITSAR_PDF)

        # ITSAR defines specific conventions for requirement keywords
        # Look for the conventions section
        assert "Must or shall or required denotes" in text
        assert "Must not or shall not denote" in text
        assert "Should or recommended denotes" in text

        # This helps us understand requirement severity
        # Must/Shall = absolute requirement
        # Should/Recommended = may be ignored in certain circumstances
        # Must not/Shall not = absolute prohibition


@pytest.mark.integration
class TestControlWorkflowWithoutAI:
    """Test control workflow without AI (manual requirement creation)."""

    def test_manual_requirement_extraction(self):
        """Test manually creating requirements from parsed document."""
        parser = PDFParser()
        parser.parse(ITSAR_PDF)

        # Extract text to find requirements
        text = parser.extract_text(ITSAR_PDF)
        lines = text.split("\n")

        # Look for numbered items that look like requirements
        import re

        requirements = []

        for i, line in enumerate(lines):
            line = line.strip()
            # Look for patterns like "2.11.1. Something"
            match = re.match(r"^([\d\.]+)\.\s+(.+)", line)
            if match and len(line) < 200:  # Likely a requirement title
                req_id = match.group(1)
                title = match.group(2).strip(".")

                # Try to get description from following lines
                description_lines = []
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j].strip()
                    if not next_line:
                        continue
                    if re.match(r"^[\d\.]+\.", next_line):  # Next requirement
                        break
                    description_lines.append(next_line)

                if description_lines:
                    requirements.append(
                        {
                            "id": f"ITSAR-{req_id}",
                            "title": title,
                            "description": " ".join(description_lines[:3]),  # First 3 lines
                        }
                    )

        # Should find multiple requirements
        assert len(requirements) > 10

        # Verify structure
        for req in requirements[:5]:
            assert "ITSAR-" in req["id"]
            assert req["title"]
            assert req["description"]

    def test_end_to_end_workflow(self):
        """Test complete workflow: parse -> extract -> generate -> validate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Step 1: Parse document
            parser = PDFParser()
            doc = parser.parse(ITSAR_PDF)
            assert doc.title

            # Step 2: Create sample requirements (simulating extraction)
            requirements = [
                ExtractedRequirement(
                    text="ASLR (Address space layout randomization) & KASLR (Kernel Address Space Layout Randomization) shall be implemented.",
                    section_id="security_features",
                    section_title="Security Features",
                    potential_id="ITSAR-2.11.1",
                ),
                ExtractedRequirement(
                    text="IMA (Integrity Measurement Architecture) shall be implemented.",
                    section_id="security_features",
                    section_title="Security Features",
                    potential_id="ITSAR-2.11.2",
                ),
                ExtractedRequirement(
                    text="Kernel Memory Sanitizers shall be enabled.",
                    section_id="security_features",
                    section_title="Security Features",
                    potential_id="ITSAR-2.11.3",
                ),
            ]

            # Step 3: Generate control files (flat structure)
            generator = ControlGenerator.__new__(ControlGenerator)
            result = generator.generate_control_structure(
                policy_id="itsar_os_security",
                policy_title="ITSAR Operating System Security Requirements",
                requirements=requirements,
                format="directory",
                output_dir=output_dir,
                source_document=str(ITSAR_PDF),
            )

            assert result.success
            assert result.total_requirements == 3
            assert result.parent_file_path.exists()

            # Step 4: Validate generated controls
            validator = ControlValidator.__new__(ControlValidator)
            validator.rule_discovery = None

            validation = validator.validate_control_file(result.parent_file_path)
            assert validation.valid or len(validation.errors) == 0

            # Step 5: Verify flat file structure (no subdirectories)
            policy_dir = output_dir / "itsar_os_security"
            assert policy_dir.exists()

            # Should have 3 requirement files directly in policy_dir (flat structure)
            req_files = list(policy_dir.glob("*.yml"))
            assert len(req_files) == 3

            # Step 6: Verify content preservation
            import yaml

            for req_file in req_files:
                with open(req_file) as f:
                    data = yaml.safe_load(f)
                    # New format has controls: wrapper
                    assert "controls" in data
                    control = data["controls"][0]
                    assert "ITSAR-" in control["id"]
                    assert control["title"]
                    assert "shall" in control["title"].lower()
