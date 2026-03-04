"""AI-powered requirement extraction from policy documents."""

from typing import Any

from content_agent.core.ai.claude_client import ClaudeClient
from content_agent.models.control import ExtractedRequirement, ParsedDocument


class RequirementExtractor:
    """Extract structured requirements from policy documents using AI."""

    SYSTEM_PROMPT = """You are a policy document analyzer. Your task is to extract security and compliance requirements from policy documents.

CRITICAL RULES:
1. Preserve EXACT text from the document - do NOT rephrase, summarize, or modify requirement text
2. Extract the complete requirement text verbatim
3. Identify requirement IDs if present (e.g., "AC-2(5)", "1.1.1", "REQ-001")
4. Associate each requirement with its section

Output Format:
Return a JSON array of requirements with this structure:
[
  {
    "text": "EXACT requirement text from document",
    "section_id": "section_identifier",
    "section_title": "Section Title",
    "potential_id": "REQ-ID or null",
    "context": "Any additional context or notes"
  }
]

Focus on requirements that:
- Describe specific security controls or practices
- Contain "must", "shall", "should", "required", or similar obligation language
- Specify technical or procedural controls
- Define compliance criteria

Skip:
- General introductory text
- Definitions sections (unless defining control requirements)
- Pure informational content without obligations"""

    def __init__(self, claude_client: ClaudeClient):
        """Initialize requirement extractor.

        Args:
            claude_client: Configured Claude client
        """
        self.client = claude_client

    def extract_requirements(self, document: ParsedDocument) -> list[ExtractedRequirement]:
        """Extract requirements from a parsed document.

        Args:
            document: Parsed document to extract requirements from

        Returns:
            List of extracted requirements

        Raises:
            Exception: If extraction fails
        """
        # Build user prompt from document sections
        user_prompt = self._build_extraction_prompt(document)

        # Get response from Claude
        response = self.client.create_message(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        # Parse JSON response
        requirements_data = self.client.extract_json_response(response)

        # Convert to ExtractedRequirement objects
        requirements = []
        if isinstance(requirements_data, list):
            for req_data in requirements_data:
                requirements.append(ExtractedRequirement(**req_data))
        elif isinstance(requirements_data, dict) and "requirements" in requirements_data:
            for req_data in requirements_data["requirements"]:
                requirements.append(ExtractedRequirement(**req_data))

        return requirements

    def extract_requirements_from_text(
        self,
        text: str,
        section_id: str = "default",
        section_title: str = "Document",
    ) -> list[ExtractedRequirement]:
        """Extract requirements from raw text.

        Args:
            text: Text to extract requirements from
            section_id: Section identifier
            section_title: Section title

        Returns:
            List of extracted requirements
        """
        user_prompt = f"""Extract requirements from the following text:

Section: {section_title}

Text:
{text}

Return the requirements as a JSON array."""

        response = self.client.create_message(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        requirements_data = self.client.extract_json_response(response)

        requirements: list[ExtractedRequirement] = []
        if isinstance(requirements_data, list):
            for req_data in requirements_data:
                # Ensure section_id and section_title are set
                req_data["section_id"] = req_data.get("section_id", section_id)
                req_data["section_title"] = req_data.get("section_title", section_title)
                requirements.append(ExtractedRequirement(**req_data))

        return requirements

    def _build_extraction_prompt(self, document: ParsedDocument) -> str:
        """Build extraction prompt from document.

        Args:
            document: Parsed document

        Returns:
            Formatted prompt text
        """
        prompt_parts = [
            f"Document: {document.title}",
            "",
            "Extract all requirements from the following sections:",
            "",
        ]

        # Add sections with their content
        for section in document.sections:
            prompt_parts.extend(self._format_section(section))
            prompt_parts.append("")

        prompt_parts.append(
            "Return a JSON array of all extracted requirements with EXACT text from the document."
        )

        return "\n".join(prompt_parts)

    def _format_section(self, section: Any, depth: int = 0) -> list[str]:
        """Format a section for the prompt.

        Args:
            section: DocumentSection to format
            depth: Current nesting depth

        Returns:
            List of formatted lines
        """
        lines = []
        indent = "  " * depth

        # Add section header
        lines.append(f"{indent}## {section.title} (ID: {section.id})")

        # Add content if present
        if section.content.strip():
            lines.append(f"{indent}{section.content}")

        # Add subsections recursively
        for subsection in section.subsections:
            lines.extend(self._format_section(subsection, depth + 1))

        return lines
