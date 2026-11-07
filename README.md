# content-mcp

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

MCP (Model Context Protocol) server for the ComplianceAsCode/content project, enabling AI assistants like Claude to interact with security compliance automation workflows.

## About this fork

This fork of [ComplianceAsCode/content-mcp](https://github.com/ComplianceAsCode/content-mcp) fixes the places where the server misread current ComplianceAsCode content. Upstream has had no commits since March 2026. Each fix is a separate commit with tests, so it can go upstream as its own pull request.

[![CI](https://github.com/realstuffie/content-mcp/actions/workflows/ci.yml/badge.svg?branch=fixes)](https://github.com/realstuffie/content-mcp/actions/workflows/ci.yml)
[![Content drift](https://github.com/realstuffie/content-mcp/actions/workflows/content-drift.yml/badge.svg)](https://github.com/realstuffie/content-mcp/actions/workflows/content-drift.yml)

Measured against ComplianceAsCode/content master at `f09d243` (2026-11-04):

| Check | Upstream | This fork |
|---|---|---|
| `validate_control_file` on `cis_ubuntu2204` | 71 errors, 300 warnings | valid |
| Real rules `validate_rule_yaml` reports invalid | 1060 of 2116 | 9 of 2566 |
| `search_rules(product="ubuntu2204")` | 0 rules | 639 |
| Profiles that lose selections when parsed | 125 of 321 | 0 |
| Products selecting `accounts_umask_interactive_users` | 3 | 10 |
| `stig_rhel9` | fails to parse | 448 requirements |
| `pcidss_4` | 72 requirements | 351 |
| `srg_gpos` / `nist_800_53` | 1 / 0 requirements | 203 / 1196 |
| Policies whose requirement count matches the content build | 47 of 70 | 70 of 70 |
| Rules the `ocp4` CIS profile selects | 0 | 199 |
| Rules that fail to load | 16 | 0 |
| Rules `get_rule_details` crashes on | 6 | 0 |
| Rules the server can find | 2530 of 2566 | 2566 (adds the 36 Firefox rules) |
| `update_requirement_rules` on an `srg_gpos` requirement | file no longer parses | loads in the content build |
| `update_requirement_rules` on `pcidss_4` requirement `1.2` | rewrites its nested requirements; file no longer parses | changes only `1.2` |
| Statuses `update_requirement_rules` offers that the content build accepts | 3 of 5 | 10 of 10 |
| Templates `get_template_schema` gives parameters for | 0 of 65 | 59 |
| Templates with a description or an example | 0 of 65 | 49 / 58 |

The 9 rules still reported invalid are OpenShift rules without a `documentation_complete` line. The validator requires it; the content build doesn't.

Other changes:

- `mcp` is capped below 2.0, because 2.x crashes the server on startup.
- AI requests work with anthropic SDK 2.x, and the default model is `claude-sonnet-5-5`, replacing the retired `claude-3-5-sonnet-20241022`.
- The profile index is shared between tool calls, so `get_rule_product_availability` takes about 0.1 seconds after the first call instead of about 15.
- The product list is shared between tool calls too, so control tools that take a product, like `get_requirement_file_path`, answer in about 1 ms instead of 55 to 65.
- `jinja2` is a declared dependency, because ComplianceAsCode's `ssg` modules import it.
- Deprecated dependencies and APIs are replaced: `pypdf` replaces the deprecated `PyPDF2`, the models use Pydantic 2's `ConfigDict`, and timestamps no longer use `datetime.utcnow()`. The only warnings left in the test run come from Jinja2 escapes in ComplianceAsCode's own macros.
- CI runs the integration tests on Python 3.11 to 3.14 against a pinned content commit, and a weekly job runs them against content master. The [CI design record](openspec/changes/archive/2026-11-07-ci-real-content/design.md) explains why.

`update_requirement_rules` also parses each edited file before writing it, and leaves the file unchanged if anything besides the requirement's rules and status would change. The [design record](openspec/changes/archive/2026-11-07-safe-requirement-updates/design.md) explains why.

The larger changes have design records in [`openspec/changes/archive/`](openspec/changes/archive/), in the entries dated 2026-11-06 and 2026-11-07.

The `fixes` branch holds all changes and is the default branch. `main` mirrors upstream. To use the fork, clone `https://github.com/realstuffie/content-mcp.git` and follow the installation steps below.

Known gaps:

- The server still needs porting to MCP SDK 2.x.
- `update_requirement_rules` refuses requirements whose rules use Jinja2 conditionals, such as two in `srg_gpos`. Those need a manual edit.
- `get_product_details` reports every product type as `unknown`.

Not maintained, on purpose:

- The rule writing tools. An agent with file access can write a `rule.yml` itself, so this fork concentrates on reading content and validating it. `generate_rule_boilerplate` writes rules the content build rejects, with a top-level `products:` key and a placeholder CCE, and two of its default locations don't exist. `generate_rule_from_template` isn't implemented.

## Features

- **Content Discovery**: Search and explore rules, profiles, products, and templates
- **Build Artifacts**: Access rendered content from build directories (post-Jinja processing)
- **Rule Scaffolding**: Generate rule boilerplate with validation
- **Control File Generation**: Create control files from security policy documents
  - Parse PDF, Markdown, HTML, and text policy documents
  - Extract requirements with exact text preservation
  - AI-powered rule mapping suggestions (requires Claude API key)
  - Automatic file structure generation organized by section
  - Validation and review tools

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
   git clone https://github.com/ComplianceAsCode/content-mcp.git
   cd content-mcp
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

# AI settings (for control file generation features)
CONTENT_AGENT_AI__ENABLED=true
CONTENT_AGENT_AI__CLAUDE_API_KEY=your_api_key_here
CONTENT_AGENT_AI__MODEL=claude-sonnet-5-5
CONTENT_AGENT_AI__MAX_TOKENS=4096
CONTENT_AGENT_AI__TEMPERATURE=0.0
```

### Configuration File

Create `config.yaml`:

```yaml
content:
  repository: /path/to/content
  branch: main

ai:
  enabled: true
  claude_api_key: your_api_key_here
  model: claude-sonnet-5-5
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

### Control Files

- `parse_policy_document` - Parse security policy documents (PDF, Markdown, HTML, text). Optional `requirement_id` parameter filters to a single requirement section.
- `generate_control_files` - Generate control file structure from requirements (inline or directory format)
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
│  │ - Control File Generation  │  │
│  └────────────────────────────┘  │
└────────┬─────────────────────────┘
         │
┌────────▼─────────────────────────┐
│ ComplianceAsCode/content         │
│ - SSG modules                    │
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
   git clone https://github.com/ComplianceAsCode/content-mcp.git
   cd content-mcp
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

## Documentation

### User Documentation
- [Architecture](docs/architecture.md)
- [API Reference](docs/api_reference.md)
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

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for spec-driven development. Contributors are encouraged to use the OpenSpec workflow (`/propose`, `/apply`, `/verify`, `/archive`) when working on new features or non-trivial changes. See the [OpenSpec documentation](https://openspec.dev/) for more details. The project configuration is in `openspec/config.yaml` and past changes can be found in `openspec/changes/archive/`.

## Support

- **Issues**: https://github.com/ComplianceAsCode/content-mcp/issues
- **Documentation**: https://github.com/ComplianceAsCode/content-mcp/blob/main/README.md
- **ComplianceAsCode/content**: https://github.com/ComplianceAsCode/content
