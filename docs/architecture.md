# Architecture

## Overview

The `content-agent` is designed as a layered architecture that exposes ComplianceAsCode/content capabilities through the Model Context Protocol (MCP).

```
┌─────────────────────────────────────────────┐
│         Claude Desktop / AI Client          │
└──────────────────┬──────────────────────────┘
                   │ MCP Protocol (stdio/HTTP)
┌──────────────────▼──────────────────────────┐
│          MCP Protocol Layer                 │
│  ┌────────────────────────────────────────┐ │
│  │ Resources  │  Tools  │  Prompts        │ │
│  └────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
┌──────────────────▼──────────────────────────┐
│          Core Business Logic                │
│  ┌────────────────────────────────────────┐ │
│  │ Discovery │ Scaffolding │ Build │ Test │ │
│  └────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
┌──────────────────▼──────────────────────────┐
│       Content Repository Integration        │
│  ┌────────────────────────────────────────┐ │
│  │  Content Manager  │  SSG Modules       │ │
│  └────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────┘
┌──────────────────▼──────────────────────────┐
│     ComplianceAsCode/content Repository     │
│  SSG modules │ Build system │ Tests         │
└─────────────────────────────────────────────┘
```

## Layers

### 1. MCP Protocol Layer

**Location:** `src/content_agent/server/`

**Responsibility:** Implements MCP protocol and handles client communication.

**Components:**
- `mcp_server.py`: Main MCP server implementation using official SDK
- `handlers/resources.py`: Resource (read-only) request handlers
- `handlers/tools.py`: Tool (action) request handlers
- `handlers/prompts.py`: Prompt request handlers (Phase 4)

**Key Features:**
- stdio transport for Claude Desktop integration
- HTTP transport for web integrations (Phase 4)
- JSON-based request/response handling
- Async request processing

### 2. Core Business Logic

**Location:** `src/content_agent/core/`

**Responsibility:** Implements domain logic for content operations.

**Modules:**

#### Discovery (`core/discovery/`)
- `products.py`: Product listing and details
- `rules.py`: Rule search and information
- `profiles.py`: Profile discovery
- `templates.py`: Template listing and schemas
- `controls.py`: Control framework discovery

**Features:**
- Efficient rule indexing and search
- Structured data extraction from YAML
- Caching for performance

#### Scaffolding (`core/scaffolding/`)
- `rule_generator.py`: Rule boilerplate generation
- `validators.py`: YAML validation
- `template_generator.py`: Template-based generation (Phase 3)
- `ai_generator.py`: AI-assisted generation (Phase 3)

**Features:**
- Smart directory placement based on rule naming
- Comprehensive validation with helpful errors
- Automatic subdirectory creation

#### Build (`core/build/`) - Phase 2
- Build orchestration
- CMake wrapper
- Artifact management

#### Testing (`core/testing/`) - Phase 2
- Automatus integration
- Container backend management
- Test result parsing

### 3. Content Repository Integration

**Location:** `src/content_agent/core/integration/`

**Responsibility:** Manages content repository and SSG module access.

**Components:**

#### Content Manager (`content_manager.py`)
- Managed repository mode (auto-clone/update)
- Existing repository mode
- Git operations
- Python path management

#### SSG Modules (`ssg_modules.py`)
- Safe import wrapper for SSG modules
- Module lifecycle management
- Error handling

**Key Features:**
- Automatic repository cloning
- Optional auto-updates
- Version detection
- SSG module isolation

### 4. Data Models

**Location:** `src/content_agent/models/`

**Responsibility:** Pydantic models for type safety and validation.

**Models:**
- `product.py`: Product-related models
- `rule.py`: Rule and validation models
- `profile.py`: Profile and template models
- `build.py`: Build job models (Phase 2)
- `test.py`: Test job models (Phase 2)

**Features:**
- JSON serialization
- Validation
- Documentation via examples

### 5. Configuration

**Location:** `src/content_agent/config/`

**Responsibility:** Configuration management.

**Components:**
- `settings.py`: Pydantic Settings with env var support
- `defaults.yaml`: Default configuration

**Configuration Sources (priority order):**
1. Environment variables (`CAC_MCP_*`)
2. Config file (if specified)
3. Defaults

### 6. Job Management

**Location:** `src/content_agent/jobs/` (Phase 2)

**Responsibility:** Async job execution and tracking.

**Features:**
- Thread pool executor
- SQLite persistence
- Job lifecycle management
- Status polling

## Design Patterns

### Repository Pattern
Content repository is abstracted behind `ContentRepository` class, allowing for:
- Different repository modes (managed vs existing)
- Testing with mock repositories
- Future support for multiple repositories

### Facade Pattern
SSG modules wrapped in `SSGModules` facade to:
- Simplify imports
- Handle initialization
- Provide error handling
- Enable testing without actual SSG modules

### Factory Pattern
Discovery classes instantiate and return appropriate model objects:
- Consistent data structures
- Easy serialization
- Type safety

## Data Flow

### Tool Call Flow

```
1. Claude Desktop sends tool call via stdio
   ↓
2. MCP server receives and deserializes request
   ↓
3. handlers/tools.py routes to appropriate function
   ↓
4. Core business logic executes
   ↓
5. Result serialized to JSON
   ↓
6. MCP server sends response via stdio
   ↓
7. Claude Desktop receives and displays result
```

### Resource Read Flow

```
1. Claude Desktop requests resource (e.g., cac://rules/ssh_idle)
   ↓
2. MCP server parses URI
   ↓
3. handlers/resources.py routes to appropriate handler
   ↓
4. Discovery module fetches data
   ↓
5. JSON serialized and returned
   ↓
6. Claude Desktop receives resource content
```

### Rule Generation Flow

```
1. generate_rule_boilerplate tool called
   ↓
2. RuleGenerator determines directory location
   ↓
3. Directory structure created
   ↓
4. rule.yml generated from template
   ↓
5. Validation performed
   ↓
6. ScaffoldingResult returned with file paths
```

## Async Design

### Current (Phase 1)
- MCP handlers are async (required by SDK)
- Core business logic is synchronous
- Works well for fast operations (discovery, scaffolding)

### Future (Phase 2+)
- Build and test operations run in background
- JobManager tracks async operations
- Clients poll for results
- SQLite persistence for job state

## Error Handling

### Levels
1. **Protocol Level**: MCP server catches all exceptions, returns error responses
2. **Handler Level**: Validation, logging, graceful degradation
3. **Core Level**: Domain-specific errors with context
4. **Integration Level**: Repository and SSG module errors

### Error Response Format
```json
{
  "error": "Brief error message",
  "details": "Detailed information",
  "suggestions": "How to fix"
}
```

## Security

### Phase 1 (MVP)
- Input validation (regex, enums, size limits)
- Path traversal prevention
- YAML size limits
- Assumes trusted local environment

### Phase 2+
- Authentication for HTTP mode
- Authorization (RBAC)
- Audit logging
- Container sandboxing for builds/tests

## Performance Considerations

### Caching
- The profile-to-rule index is shared between tool calls, because building it takes
  about 15 seconds. It is rebuilt when any file it was built from changes.
- Everything else reads the content files on each call.

### Lazy Loading
- SSG modules loaded only when needed
- Repository cloned only if managed mode
- Heavy operations deferred to Phase 2 jobs

### Scalability
- Single repository instance (singleton)
- Thread pool for concurrent jobs (Phase 2)
- Connection pooling for HTTP mode (Phase 4)

## Testing Strategy

### Unit Tests
- Models: Serialization, validation
- Discovery: Search, parsing
- Scaffolding: Generation, validation
- Config: Loading, merging

### Integration Tests
- MCP protocol compliance
- End-to-end tool calls
- Resource access
- Repository integration

### Test Fixtures
- Sample YAML files
- Mock repositories
- Example configurations

## Deployment Models

### Claude Desktop (stdio)
```
Claude Desktop
  ↓ spawns process
content-agent (stdio mode)
  ↓ reads from
ComplianceAsCode/content repo
```

### HTTP Server (Phase 4)
```
Web Client
  ↓ HTTP
content-agent (HTTP mode)
  ↓ reads from
ComplianceAsCode/content repo
```

### Container (Future)
```
Docker container
  ├─ content-agent
  ├─ content repo (volume mount)
  └─ build tools
```

## Future Enhancements

### Phase 2: Build & Test
- Async job management
- Build orchestration
- Automatus integration
- Result caching

### Phase 3: Advanced Scaffolding
- Template-based generation
- AI-assisted content creation
- Auto-fixing validation errors

### Phase 4: Production Features
- HTTP transport
- Authentication/authorization
- Comprehensive prompts
- Audit logging

### Phase 5+: Enterprise
- Multi-repository support
- Collaboration features
- CI/CD integration
- Performance optimization
