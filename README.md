# content-agent

[![CI](https://github.com/ggbecker/content-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/ggbecker/content-agent/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/ggbecker/content-agent/branch/main/graph/badge.svg)](https://codecov.io/gh/ggbecker/content-agent)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

MCP (Model Context Protocol) server for the ComplianceAsCode/content project, enabling AI assistants like Claude to interact with security compliance automation workflows.

## Features

- **Content Discovery**: Search and explore rules, profiles, products, and templates
- **Build Artifacts**: Access rendered content from build directories (post-Jinja processing)
- **Rule Scaffolding**: Generate rule boilerplate with validation
- **Control File Generation**: Create control files from security policy documents (NEW)
  - Parse PDF, Markdown, HTML, and text policy documents
  - Extract requirements with exact text preservation
  - AI-powered rule mapping suggestions (requires Claude API key)
  - Automatic file structure generation organized by section
  - Validation and review tools
- **Build Integration**: Trigger and monitor product/rule builds
- **Test Automation**: Execute and track Automatus test runs
- **Dual Transport**: stdio (Claude Desktop) and HTTP modes

## Quick Start

### Prerequisites

1. **Python 3.11+** installed
2. **ComplianceAsCode/content repository** - Clone it first:
   ```bash
   git clone https://github.com/ComplianceAsCode/content.git ~/workspace/content
   ```

### Installation (Local Development)

1. Clone this repository:
   ```bash
   git clone https://github.com/ggbecker/content-agent.git
   cd content-agent
   ```

2. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

3. Verify installation:
   ```bash
   content-agent --help
   ```

### Claude Desktop Integration

#### Option 1: Using Your Existing ComplianceAsCode/content Repository

Add this to your Claude Desktop config file (`claude_desktop_config.json`):

**Location of config file:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "content-agent": {
      "command": "python",
      "args": ["-m", "content_agent"],
      "env": {
        "CONTENT_AGENT_CONTENT__REPOSITORY": "/home/user/workspace/content"
      }
    }
  }
}
```

Replace `/home/user/workspace/content` with the actual path to your ComplianceAsCode/content repository.

#### Option 2: Let content-agent Manage the Repository

content-agent can automatically clone and manage the ComplianceAsCode/content repository:

```json
{
  "mcpServers": {
    "content-agent": {
      "command": "python",
      "args": ["-m", "content_agent"],
      "env": {
        "CONTENT_AGENT_CONTENT__REPOSITORY": "managed",
        "CONTENT_AGENT_CONTENT__MANAGED_PATH": "~/.content-agent/content"
      }
    }
  }
}
```

**After adding the configuration:**
1. Restart Claude Desktop completely (quit and reopen)
2. Look for a hammer icon (🔨) in the bottom right - this indicates MCP servers are loaded
3. Start asking questions like "What products are available?" or "Search for SSH rules"

### Standalone Usage (CLI)

Run the MCP server directly from command line:

```bash
# Use existing content repository
content-agent --content-repo ~/workspace/content

# Use managed checkout (auto-clones to ~/.content-agent/content)
content-agent --content-repo managed

# With custom configuration file
content-agent --config config.yaml

# Debug mode with detailed logging
content-agent --content-repo ~/workspace/content --log-level DEBUG
```

**Note:** The standalone mode runs the MCP server in stdio mode, which expects MCP protocol messages. For interactive use, integrate with Claude Desktop instead.

### Troubleshooting

#### Claude Desktop Not Showing MCP Tools

1. **Check config file location:**
   - Make sure you edited the correct `claude_desktop_config.json` file
   - Verify the JSON is valid (use a JSON validator)

2. **Check Claude Desktop logs:**
   - **macOS**: `~/Library/Logs/Claude/mcp*.log`
   - **Windows**: `%APPDATA%\Claude\logs\mcp*.log`
   - **Linux**: `~/.config/Claude/logs/mcp*.log`

3. **Verify content-agent is installed:**
   ```bash
   which content-agent
   python -m content_agent --help
   ```

4. **Test manually:**
   ```bash
   content-agent --content-repo ~/workspace/content --log-level DEBUG
   ```
   You should see initialization messages. Press Ctrl+C to exit.

#### MCP Server Fails to Start

**Error: "Content repository not found"**
- Verify the path in `CONTENT_AGENT_CONTENT__REPOSITORY` exists
- Use absolute paths, not relative paths
- Ensure you have read permissions

**Error: "SSG modules not found"**
- Make sure the content repository is complete (has `ssg/` directory)
- Try using a fresh clone of ComplianceAsCode/content

**Error: "Permission denied"**
- Check that Python and content-agent are executable
- Verify file permissions on the content repository

#### Enable Debug Logging

Add debug logging to your Claude Desktop config:

```json
{
  "mcpServers": {
    "content-agent": {
      "command": "python",
      "args": ["-m", "content_agent"],
      "env": {
        "CONTENT_AGENT_CONTENT__REPOSITORY": "/home/user/workspace/content",
        "CONTENT_AGENT_LOGGING__LEVEL": "DEBUG",
        "CONTENT_AGENT_LOGGING__FILE": "/tmp/content-agent.log"
      }
    }
  }
}
```

Then check `/tmp/content-agent.log` for detailed error messages.

## Configuration

### Environment Variables

```bash
# Content repository
CONTENT_AGENT_CONTENT__REPOSITORY=/path/to/content
CONTENT_AGENT_CONTENT__BRANCH=main

# Server mode
CONTENT_AGENT_SERVER__MODE=stdio  # or http
CONTENT_AGENT_SERVER__HTTP__PORT=8080

# Build settings
CONTENT_AGENT_BUILD__MAX_CONCURRENT_BUILDS=2
CONTENT_AGENT_BUILD__TIMEOUT=3600

# Testing settings
CONTENT_AGENT_TESTING__BACKEND=podman
CONTENT_AGENT_TESTING__MAX_CONCURRENT_TESTS=4

# AI settings (for control file generation features)
CONTENT_AGENT_AI__ENABLED=true
CONTENT_AGENT_AI__CLAUDE_API_KEY=your_api_key_here
CONTENT_AGENT_AI__MODEL=claude-3-5-sonnet-20241022
CONTENT_AGENT_AI__MAX_TOKENS=4096
CONTENT_AGENT_AI__TEMPERATURE=0.0
```

### Configuration File

Create `config.yaml`:

```yaml
content:
  repository: /path/to/content
  branch: main

server:
  mode: stdio

build:
  max_concurrent_builds: 2
  timeout: 3600

testing:
  backend: podman
  max_concurrent_tests: 4

ai:
  enabled: true
  claude_api_key: your_api_key_here
  model: claude-3-5-sonnet-20241022
  max_tokens: 4096
  temperature: 0.0
```

Run with: `content-agent --config config.yaml`

## Available Tools

For full parameter details and response schemas, see the [API Reference](docs/api_reference.md).

### Discovery

- `list_products` - List all available products
- `get_product_details` - Get product information
- `search_rules` - Search rules by keyword, product, severity
- `get_rule_details` - Get complete rule information (automatically includes rendered content from builds)
- `list_templates` - List available templates
- `get_template_schema` - Get template parameter schema
- `list_profiles` - List profiles for a product or all products
- `get_profile_details` - Get detailed profile information

### Build Artifacts

- `list_built_products` - List products with build artifacts
- `get_rendered_rule` - Get fully rendered rule (after Jinja processing)
- `get_datastream_info` - Get datastream information and statistics
- `search_rendered_content` - Search in rendered build artifacts

### Scaffolding

- `generate_rule_boilerplate` - Generate basic rule structure
- `generate_rule_from_template` - Generate rule using template
- `validate_rule_yaml` - Validate rule.yml structure
- `generate_profile_boilerplate` - Generate profile structure

### Control Files

- `parse_policy_document` - Parse security policy documents (PDF, Markdown, HTML, text)
- `generate_control_files` - Generate control file structure from requirements
- `suggest_rule_mappings` - Get AI-suggested rule mappings (requires API key)
- `validate_control_file` - Validate control file syntax and structure
- `review_control_generation` - Review generated controls with validation and suggestions
- `list_controls` - List available control frameworks (optional `product` to scope)
- `get_control_details` - Get control framework details (optional `product` to scope)
- `get_control_stats` - Get aggregate requirement statistics for a control file (optional `product` to scope)
- `search_control_requirements` - Search within control requirements (optional `product` to scope)
- `get_control_rule_index` - Build a complete index of requirements and rule mappings across frameworks (optional `product` to scope)
- `find_similar_requirements` - Find requirements with similar text across control frameworks (optional `product` to scope)
- `get_rule_product_availability` - Check which products include a given rule
- `get_requirement_file_path` - Resolve the filesystem path for a specific requirement (optional `product` to scope)
- `list_unmapped_requirements` - List requirements that need rule mappings (optional `product` to scope)
- `update_requirement_rules` - Update rules and status for a requirement in a control file (optional `product` to scope)

### Build

- `build_product` - Build complete product datastream
- `build_rule` - Build thin datastream for single rule
- `get_build_status` - Get build job status and logs

### Testing

- `run_rule_tests` - Execute Automatus tests for a rule
- `run_profile_tests` - Execute tests for all rules in profile
- `get_test_results` - Get test execution results

## Example Workflows

### Find and Understand a Rule

```
User: "Find SSH timeout rules for RHEL 9"
Claude: [calls search_rules(query="ssh timeout", product="rhel9")]
Claude: "Found 3 rules. The main one is sshd_set_idle_timeout..."
User: "Show me details"
Claude: [calls get_rule_details(rule_id="sshd_set_idle_timeout")]
Claude: "This rule checks ClientAliveInterval. I can see the source and rendered content for rhel9 and rhel10. The rendered RHEL 9 version shows ClientAliveInterval 300 (5 minutes)..."
```

### Create a New Rule

```
User: "Create a new rule for SSH MaxAuthTries"
Claude: [calls generate_rule_boilerplate(...)]
Claude: "Created rule structure at linux_os/guide/services/ssh/..."
Claude: [calls validate_rule_yaml(...)]
Claude: "Rule validates successfully!"
```

### Build and Test

```
User: "Build my new rule for RHEL 9"
Claude: [calls build_rule(product="rhel9", rule_id="sshd_max_auth_tries")]
Claude: "Build started (job: build_123)..."
Claude: [polls get_build_status(job_id="build_123")]
Claude: "Build completed! Datastream at /path/to/build/..."

User: "Run tests"
Claude: [calls run_rule_tests(...)]
Claude: "Tests started (job: test_456)..."
Claude: [polls get_test_results(job_id="test_456")]
Claude: "All 5 test scenarios passed!"
```

### Create Control Files from Policy Document

```
User: "Parse this NIST 800-53 PDF and create control files"
Claude: [calls parse_policy_document(source="/path/to/nist_800_53.pdf", document_type="pdf")]
Claude: "Parsed document with 324 requirements across 18 sections..."

User: "Generate control files for these requirements"
Claude: [calls generate_control_files(policy_id="nist_800_53", ...)]
Claude: "Created control structure:
  - Parent file: controls/nist_800_53.yml
  - 324 requirement files in 18 sections
  - Files organized: controls/nist_800_53/access_control/ac_001.yml, ..."

User: "Suggest rule mappings for the password requirements"
Claude: [calls suggest_rule_mappings(requirement_text="Organizations must enforce password complexity...")]
Claude: "Found 5 relevant rules:
  1. accounts_password_minlen_login_defs (85% confidence)
  2. accounts_password_pam_minlen (82% confidence)
  ..."

User: "Review the generated control files"
Claude: [calls review_control_generation(control_file_path="controls/nist_800_53.yml")]
Claude: "Review Report:
  - Total requirements: 324
  - Requirements with rules: 156 (48%)
  - Requirements without rules: 168
  - Validation: PASSED
  - Suggested mappings available for 142 unmapped requirements"
```

## Architecture

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │ stdio
┌────────▼─────────────────────────┐
│  content-agent          │
│  ┌────────────────────────────┐  │
│  │ MCP Protocol Layer         │  │
│  │ - Resources, Tools, Prompts│  │
│  └────────────────────────────┘  │
│  ┌────────────────────────────┐  │
│  │ Core Business Logic        │  │
│  │ - Discovery, Scaffolding   │  │
│  │ - Build, Testing           │  │
│  │ - Control File Generation  │  │
│  └────────────────────────────┘  │
└────────┬─────────────────────────┘
         │
┌────────▼─────────────────────────┐
│ ComplianceAsCode/content         │
│ - SSG modules, Build, Tests      │
└──────────────────────────────────┘
```

## Control File Generation

The control file generation feature enables creating ComplianceAsCode control files from security policy documents.

### Workflow

1. **Parse Policy Document**
   - Supports PDF, Markdown, HTML, and plain text formats
   - Extracts document structure (sections, headings)
   - Preserves exact text (no AI rewording at this stage)

2. **Extract Requirements** (Optional, with Claude API)
   - AI analyzes document to identify security requirements
   - Extracts requirement text with exact wording preserved
   - Associates requirements with their sections

3. **Generate Control Files**
   - Creates individual YAML files per requirement
   - Organizes files by section: `controls/<policy_id>/<section>/<req>.yml`
   - Generates parent file with includes: `controls/<policy_id>.yml`

4. **AI Rule Mapping** (Optional, with Claude API)
   - Suggests ComplianceAsCode rules for each requirement
   - Provides confidence scores and reasoning
   - Classifies match types (exact_ref, keyword, semantic, description)

5. **Validation and Review**
   - Validates YAML syntax and structure
   - Checks rule references exist
   - Compares extracted vs. original text
   - Reports coverage statistics

### File Structure

Generated control files follow this structure:

```
controls/
├── my_policy.yml                 # Parent control file
└── my_policy/                    # Policy directory
    ├── access_control/           # Section directory
    │   ├── ac_001.yml           # Individual requirements
    │   ├── ac_002.yml
    │   └── ac_003.yml
    └── authentication/
        ├── au_001.yml
        └── au_002.yml
```

**Parent file** (`controls/my_policy.yml`):
```yaml
id: my_policy
title: My Security Policy
description: Policy description
source_document: /path/to/policy.pdf
includes:
  - access_control/ac_001.yml
  - access_control/ac_002.yml
  - authentication/au_001.yml
```

**Requirement file** (`controls/my_policy/access_control/ac_001.yml`):
```yaml
id: AC-1
title: Access Control Policy and Procedures
description: |
  The organization develops, documents, and disseminates...
  (exact text from source document)
status: automated
rules:
  - file_permissions_etc_passwd
  - file_ownership_etc_group
related_rules:
  - accounts_password_minlen_login_defs
references:
  nist:
    - AC-1
notes: Implementation notes here
```

### AI Configuration

To use AI-powered features (requirement extraction and rule mapping), configure Claude API access:

**Via environment variables:**
```bash
export CONTENT_AGENT_AI__ENABLED=true
export CONTENT_AGENT_AI__CLAUDE_API_KEY=sk-ant-...
```

**Via Claude Desktop config:**
```json
{
  "mcpServers": {
    "content-agent": {
      "command": "python",
      "args": ["-m", "content_agent"],
      "env": {
        "CONTENT_AGENT_CONTENT__REPOSITORY": "/path/to/content",
        "CONTENT_AGENT_AI__ENABLED": "true",
        "CONTENT_AGENT_AI__CLAUDE_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

**Note:** AI features are optional. You can still parse documents and generate control files manually without an API key.

### Best Practices

1. **Text Preservation**: The system preserves exact text from source documents. Always review extracted requirements for accuracy.

2. **Section Organization**: Organize requirements by logical sections matching your policy document structure.

3. **Rule Mapping**: AI suggestions are starting points. Review confidence scores and reasoning before accepting mappings.

4. **Validation**: Always run validation after generating control files to catch structural issues early.

5. **Incremental Updates**: You can update existing control files by adding new requirements while preserving existing mappings.

## Development

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ggbecker/content-agent.git
   cd content-agent
   ```

2. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Clone the ComplianceAsCode/content repository:**
   ```bash
   git clone https://github.com/ComplianceAsCode/content.git ~/workspace/content
   ```

4. **Test your local installation:**
   ```bash
   # Run with local content repo
   content-agent --content-repo ~/workspace/content --log-level DEBUG
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=content_agent --cov-report=html

# Run specific test file
pytest tests/unit/test_config.py -v

# Run integration tests (requires content repo)
pytest tests/integration/ -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
content-agent/
├── src/content_agent/       # Main source code
│   ├── config/              # Configuration management
│   ├── core/                # Core functionality
│   │   ├── discovery/       # Content discovery (rules, products, etc.)
│   │   ├── integration/     # ComplianceAsCode integration
│   │   └── scaffolding/     # Code generation
│   ├── models/              # Pydantic data models
│   └── server/              # MCP server implementation
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── examples/                # Example configurations
└── docs/                    # Documentation
```

## Requirements

- Python 3.11+
- ComplianceAsCode/content repository (local or managed)
- For testing: podman or docker
- For builds: CMake, standard build dependencies

## Documentation

### User Documentation
- [Architecture](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [Deployment Guide](docs/deployment.md)
- [Build Artifacts Usage](docs/BUILD_ARTIFACTS_USAGE.md) - Guide to using rendered content from builds

### ComplianceAsCode Integration
- [ComplianceAsCode Reference](docs/COMPLIANCEASCODE_REFERENCE.md) - Understanding ComplianceAsCode/content project structure
- [Compliance Summary](docs/COMPLIANCE_SUMMARY.md) - Implementation compliance status
- [Compliance Audit](docs/COMPLIANCE_AUDIT.md) - Detailed audit report

### Features
- [Build Artifacts Feature](docs/BUILD_ARTIFACTS_FEATURE.md) - Technical design for build artifacts support
- [Unified Rule Discovery](UNIFIED_RULE_DISCOVERY.md) - Automatic source + rendered content in one call

## License

Apache License 2.0 - see LICENSE file

## Contributing

Contributions welcome! Please see the ComplianceAsCode/content project for contribution guidelines.

## Support

- **Issues**: https://github.com/ggbecker/content-agent/issues
- **Documentation**: https://github.com/ggbecker/content-agent/blob/main/README.md
- **ComplianceAsCode/content**: https://github.com/ComplianceAsCode/content
