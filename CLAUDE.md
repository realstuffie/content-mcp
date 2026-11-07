# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

content-agent is an MCP (Model Context Protocol) server that bridges AI assistants with the ComplianceAsCode/content project for security compliance automation. It's a Python 3.11+ project using async patterns, Pydantic v2 models, and the MCP SDK. It runs in stdio mode (HTTP planned for Phase 4).

## Commands

### Install
```bash
pip install -e ".[dev]"
```

### Run tests
```bash
pytest                                    # all tests (includes coverage by default via pyproject.toml)
pytest tests/unit/                        # unit tests only
pytest tests/integration/                 # integration tests only
pytest tests/unit/test_validators.py      # single file
pytest tests/unit/test_validators.py::TestRuleValidator::test_valid_rule -x  # single test, stop on first failure
```

Integration tests auto-detect a ComplianceAsCode/content repo and skip if none is found. CI runs them against the content commit pinned as `CONTENT_REF` in `.github/workflows/ci.yml`, and the weekly "Content drift" workflow runs them against content master; bump the pin when that workflow passes. To enable them locally:
```bash
CONTENT_REPO=/path/to/content pytest tests/integration/   # explicit path
# or clone to ~/.content-agent/content (auto-detected)
```

### Lint and format
```bash
black --check src/ tests/                 # check formatting
black src/ tests/                         # apply formatting
ruff check src/ tests/                    # lint
ruff check --fix src/ tests/             # lint with auto-fix
mypy src/                                 # type check (blocking in CI)
```

### Run the server
```bash
content-agent                                         # managed repo (auto-clone)
content-agent --content-repo /path/to/content         # existing repo
content-agent --log-level DEBUG                       # debug mode
```

## Architecture

### Layered design
```
MCP Client (Claude Desktop / AI Assistant)
  → MCP Protocol Layer (server/mcp_server.py, server/handlers/)
    → Core Business Logic (core/)
      → Content Repository Integration (core/integration/)
        → ComplianceAsCode/content repo (external)
```

### Source layout (`src/content_agent/`)

- **`__main__.py`** — CLI entry point (click). Initializes settings → logging → content repo → SSG modules → MCP server.
- **`config/`** — Pydantic Settings with env var support (`CONTENT_AGENT_` prefix, `__` nested delimiter). Priority: env vars > config file > `defaults.yaml`.
- **`server/`** — MCP server and handler registration. `handlers/tools.py` defines all MCP tools, `handlers/resources.py` and `handlers/prompts.py` handle resources and prompts.
- **`core/discovery/`** — Read-only queries: products, rules, profiles, templates, controls, build artifacts.
- **`core/scaffolding/`** — Code generation: rule/profile/template/control file generators and validators.
- **`core/parsing/`** — Document parsers (PDF, Markdown, HTML, text) with abstract base. Used for policy document ingestion.
- **`core/ai/`** — Anthropic API integration: Claude client wrapper, requirement extraction, rule mapping.
- **`core/integration/`** — Content repository management (git clone/update) and SSG Python module loading.
- **`core/review/`** — Mapping review and text comparison.
- **`models/`** — Pydantic data models for rules, products, profiles, controls, builds, tests.

### Control file generation flow
Policy documents (PDF/MD/HTML/text) → parser extracts requirements → flat directory structure generated:
```
controls/
├── policy.yml           # parent file
└── policy/
    ├── req1.yml
    └── req2.yml
```
AI-powered rule mapping with confidence scores is available via `suggest_rule_mappings`.

### Configuration
Settings are in `config/settings.py` using pydantic-settings. Key sections: `content` (repository path/mode), `server` (mode), `build` (artifacts), `ai` (Claude API), `logging`, `security`. Default config path: `~/.content-agent/config.yaml`.

## Code Style

- **Formatter**: black, line-length 100, target Python 3.11
- **Linter**: ruff — rules: E, W, F, I (isort), B (bugbear), C4 (comprehensions), UP (pyupgrade). E501 ignored (black handles line length).
- **Type checking**: mypy strict mode (disallow_untyped_defs, disallow_incomplete_defs, strict_equality, etc.)
- **Async**: Use `async/await` throughout; tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- All models use Pydantic v2 (`pydantic>=2.0.0`)
