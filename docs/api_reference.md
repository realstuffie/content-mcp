# API Reference

## MCP Resources

Resources provide read-only access to content via URI.

### Products

**List all products**
```
URI: cac://products
Returns: JSON array of ProductSummary objects
```

**Get product details**
```
URI: cac://products/{product_id}
Example: cac://products/rhel9
Returns: ProductDetails object
```

### Rules

**List rules**
```
URI: cac://rules
Returns: JSON array of RuleSearchResult objects (limited to 100)
```

**Get rule details**
```
URI: cac://rules/{rule_id}
Example: cac://rules/sshd_set_idle_timeout
Returns: RuleDetails object
```

### Templates

**List templates**
```
URI: cac://templates
Returns: JSON array of TemplateSummary objects
```

**Get template schema**
```
URI: cac://templates/{template_name}
Example: cac://templates/sshd_lineinfile
Returns: TemplateSchema object
```

### Profiles

**List all profiles**
```
URI: cac://profiles
Returns: JSON array of ProfileSummary objects
```

**Get profile details**
```
URI: cac://profiles/{product}/{profile_id}
Example: cac://profiles/rhel9/ospp
Returns: ProfileDetails object
```

### Controls

**List control frameworks**
```
URI: cac://controls
Returns: JSON array of control framework names
```

### Build Artifacts

**List built products**
```
URI: cac://build
Returns: JSON object with products array and count
```

**Get product build info**
```
URI: cac://build/{product}
Example: cac://build/rhel9
Returns: DatastreamInfo object
```

**Get rendered rule**
```
URI: cac://build/{product}/rules/{rule_id}
Example: cac://build/rhel9/rules/sshd_set_idle_timeout
Returns: RenderedRule object (fully rendered after Jinja processing)
```

## MCP Tools

Tools are invokable actions that perform operations.

### Discovery Tools

#### list_products

List all available products.

**Parameters:** None

**Returns:**
```json
[
  {
    "product_id": "rhel9",
    "name": "Red Hat Enterprise Linux 9",
    "product_type": "rhel",
    "version": "9",
    "description": "Security compliance content for RHEL 9"
  }
]
```

#### get_product_details

Get detailed information about a product.

**Parameters:**
- `product_id` (string, required): Product identifier

**Returns:** ProductDetails object

**Example:**
```json
{
  "product_id": "rhel9",
  "name": "Red Hat Enterprise Linux 9",
  "profiles": ["ospp", "stig", "cis"],
  "benchmark_root": "linux_os/guide",
  "product_dir": "products/rhel9"
}
```

#### search_rules

Search for rules by keyword, product, or severity.

**Parameters:**
- `query` (string, optional): Search query (matches ID, title, description)
- `product` (string, optional): Filter by product ID
- `severity` (string, optional): Filter by severity (low, medium, high, unknown)
- `limit` (integer, optional): Maximum results (default: 50)

**Returns:** Array of RuleSearchResult objects

**Example:**
```json
[
  {
    "rule_id": "sshd_set_idle_timeout",
    "title": "Set SSH Idle Timeout Interval",
    "severity": "medium",
    "description": "Configure SSH to automatically terminate...",
    "products": ["rhel7", "rhel8", "rhel9"],
    "file_path": "linux_os/guide/services/ssh/..."
  }
]
```

#### get_rule_details

Get complete information about a rule. Automatically includes rendered content metadata from build artifacts if available.

**Parameters:**
- `rule_id` (string, required): Rule identifier
- `include_rendered` (boolean, optional): Include rendered content from builds (default: true). Automatically detects and includes info about rendered YAML, OVAL, and remediations.
- `product` (string, optional): Product filter for rendered content. If specified, only includes rendered content for this product.
- `rendered_detail` (string, optional): Detail level for rendered content: "metadata" (default, ~2k tokens — sizes and availability only) or "full" (~18k tokens — includes complete rendered text). Use "full" only when you need to see actual rendered content. Enum: `metadata`, `full`.

**Returns:** RuleDetails object with full metadata, remediations, tests, and optionally rendered build artifact content

#### list_templates

List all available rule templates.

**Parameters:** None

**Returns:** Array of TemplateSummary objects

#### get_template_schema

Get parameter schema for a template.

**Parameters:**
- `template_name` (string, required): Template name

**Returns:** TemplateSchema object with parameter definitions

#### list_profiles

List profiles for a product or all products.

**Parameters:**
- `product` (string, optional): Filter by product ID

**Returns:** Array of ProfileSummary objects

#### get_profile_details

Get detailed information about a profile.

**Parameters:**
- `profile_id` (string, required): Profile identifier
- `product` (string, required): Product identifier

**Returns:** ProfileDetails object

### Scaffolding Tools

#### generate_rule_boilerplate

Generate basic rule structure with boilerplate files.

**Parameters:**
- `rule_id` (string, required): Rule identifier (directory name)
- `title` (string, required): Rule title
- `description` (string, required): Rule description
- `severity` (string, required): Rule severity (low, medium, high, unknown)
- `product` (string, required): Primary product
- `location` (string, optional): Custom location path
- `rationale` (string, optional): Rule rationale

**Returns:** ScaffoldingResult object

**Example:**
```json
{
  "success": true,
  "rule_id": "sshd_max_auth_tries",
  "rule_dir": "linux_os/guide/services/ssh/ssh_server/sshd_max_auth_tries",
  "files_created": [
    "linux_os/.../rule.yml",
    "linux_os/.../bash/",
    "linux_os/.../ansible/",
    "linux_os/.../oval/",
    "linux_os/.../tests/"
  ],
  "message": "Rule boilerplate created successfully"
}
```

#### validate_rule_yaml

Validate rule.yml YAML content.

**Parameters:**
- `rule_yaml` (string, required): YAML content to validate
- `check_references` (boolean, optional): Check reference format (default: true)
- `auto_fix` (boolean, optional): Attempt auto-fixing (default: false)

**Returns:** ValidationResult object

**Example:**
```json
{
  "valid": false,
  "errors": [
    {
      "field": "severity",
      "error": "Invalid severity value 'critical'",
      "line": 5,
      "suggestion": "Use one of: low, medium, high, unknown"
    }
  ],
  "warnings": [],
  "fixes_applied": []
}
```

#### generate_rule_from_template

Generate rule using a template (Phase 3 feature - not yet implemented).

**Parameters:**
- `template_name` (string, required): Template name
- `parameters` (object, required): Template parameters
- `rule_id` (string, required): Rule identifier
- `product` (string, required): Product identifier

**Returns:** ScaffoldingResult object

### Build Artifact Tools

#### list_built_products

List products that have been built and have artifacts available in the build/ directory.

**Parameters:** None

**Returns:** Object with `products` (array of product ID strings) and `count` (integer)

#### get_rendered_rule

Get fully rendered rule content from build directory (after Jinja template processing and variable expansion). Shows the actual content that goes into the datastream.

**Parameters:**
- `product` (string, required): Product identifier (e.g., rhel9, fedora)
- `rule_id` (string, required): Rule identifier

**Returns:** RenderedRule object

**Example:**
```json
{
  "rule_id": "sshd_set_idle_timeout",
  "product": "rhel9",
  "rendered_yaml": "title: Set SSH Idle Timeout...",
  "rendered_oval": "<def-group>...</def-group>",
  "rendered_remediations": {
    "bash": "#!/bin/bash\necho 'ClientAliveInterval 300' >> /etc/ssh/sshd_config"
  },
  "build_path": "build/rhel9/rules/sshd_set_idle_timeout"
}
```

#### get_datastream_info

Get information about a built datastream for a product.

**Parameters:**
- `product` (string, required): Product identifier

**Returns:** DatastreamInfo object

**Example:**
```json
{
  "product": "rhel9",
  "datastream_path": "build/ssg-rhel9-ds.xml",
  "file_size": 10485760,
  "build_time": "2026-01-28T10:32:15Z",
  "profiles_count": 15,
  "rules_count": 450,
  "exists": true
}
```

#### search_rendered_content

Search in rendered build artifacts (useful for finding actual values after template expansion, searching in final content).

**Parameters:**
- `query` (string, required): Search query
- `product` (string, optional): Product filter
- `limit` (integer, optional): Maximum number of results (default: 50)

**Returns:** Array of RenderSearchResult objects

### Control File Tools

#### parse_policy_document

Parse security policy document (PDF, Markdown, HTML, or text) and extract requirements with exact text preservation.

**Parameters:**
- `source` (string, required): Path to file or URL of policy document
- `document_type` (string, required): Document type. Enum: `pdf`, `markdown`, `text`, `html`.

**Returns:** ParsedDocument object with sections hierarchy and extracted requirements

#### generate_control_files

Generate control file structure from extracted requirements. Creates individual requirement files in a flat directory structure (ComplianceAsCode format).

**Parameters:**
- `policy_id` (string, required): Policy identifier
- `policy_title` (string, required): Policy title
- `requirements_json` (string, required): JSON string of extracted requirements. Format: `{"requirements": [{"id": "...", "title": "...", "description": "...", "section": "..."}]}` or just the array.
- `source_document` (string, optional): Source document path or URL
- `version` (string, optional): Version string (e.g., "v3r1", "1.0")
- `levels` (array of strings, optional): Compliance levels (e.g., ["high", "medium", "low"])
- `nested_by_section` (boolean, optional): Deprecated — always uses flat structure as required by ComplianceAsCode. Default: false.
- `product` (string, optional): Product ID; generates into `products/<product>/controls/` instead of `controls/`

**Returns:** ControlGenerationResult object

**Example:**
```json
{
  "policy_id": "nist_800_53",
  "parent_file_path": "controls/nist_800_53.yml",
  "requirement_files": ["controls/nist_800_53/ac-2.yml", "controls/nist_800_53/ac-3.yml"],
  "total_requirements": 2,
  "sections": ["access_control"],
  "success": true,
  "errors": [],
  "warnings": []
}
```

#### suggest_rule_mappings

Get AI-suggested rule mappings for a control requirement. Requires Claude API key configured (`CONTENT_AGENT_AI__ENABLED=true` and `CONTENT_AGENT_AI__CLAUDE_API_KEY`).

**Parameters:**
- `requirement_text` (string, required): Control requirement text
- `requirement_id` (string, optional): Requirement ID
- `max_suggestions` (integer, optional): Maximum number of suggestions (default: 10)
- `min_confidence` (number, optional): Minimum confidence score 0.0–1.0 (default: 0.3)
- `cross_reference` (boolean, optional): Include cross-framework evidence from similar requirements in other control files (default: false)
- `target_product` (string, optional): Prioritize rules with identifiers for this product (e.g., "rhel9")

**Returns:** Array of RuleSuggestion objects

**Example:**
```json
[
  {
    "rule_id": "sshd_set_idle_timeout",
    "confidence": 0.85,
    "reasoning": "Rule directly implements session timeout requirement",
    "match_type": "semantic",
    "metadata": {}
  }
]
```

#### validate_control_file

Validate control file YAML syntax, structure, and rule references.

**Parameters:**
- `control_file_path` (string, required): Path to control file

**Returns:** ControlValidationResult object

#### review_control_generation

Review generated control files with validation, text comparison, and AI suggestions.

**Parameters:**
- `control_file_path` (string, required): Path to generated control file
- `generate_suggestions` (boolean, optional): Whether to generate AI rule suggestions (default: true)

**Returns:** Formatted review report with validation results, text comparisons, and rule suggestions

#### list_controls

List available control frameworks.

**Parameters:**
- `product` (string, optional): Product ID to scope to product-specific controls (e.g., "rhel9"). When set, scans both global `controls/` and `products/<product>/controls/` with override semantics.

**Returns:** Object with `controls` (array of control framework ID strings) and `count` (integer)

#### get_control_details

Get detailed information about a control framework.

**Parameters:**
- `control_id` (string, required): Control framework identifier
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** ControlFile object with full requirements list

#### get_control_stats

Get aggregate requirement statistics for a control file. Returns pre-computed counts by status and mapped/unmapped tallies, avoiding unreliable manual counting.

**Parameters:**
- `control_id` (string, required): Control framework identifier
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** ControlStats object with total, by_status, mapped, and unmapped counts

#### search_control_requirements

Search within control files for specific requirements.

**Parameters:**
- `query` (string, required): Search query (matches title, description, ID)
- `control_id` (string, optional): Control framework to search within
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** Array of ControlRequirement objects

#### get_control_rule_index

Build a complete index of all requirements and rule mappings across all control frameworks. Useful for cross-framework rule discovery.

**Parameters:**
- `include_unmapped` (boolean, optional): Include requirements without rule mappings (default: true)
- `control_ids` (array of strings, optional): List of control framework IDs to index (default: all)
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** ControlRuleIndex object

#### find_similar_requirements

Find requirements with similar text across all control frameworks using text similarity. Useful for discovering how different frameworks address the same security concern.

**Parameters:**
- `requirement_text` (string, required): Requirement text to search for similar requirements
- `min_similarity` (number, optional): Minimum similarity score 0.0–1.0 (default: 0.2)
- `max_results` (integer, optional): Maximum number of results (default: 20)
- `exclude_control_id` (string, optional): Control framework to exclude from results
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** Array of SimilarRequirement objects

#### get_rule_product_availability

Check which products include a given rule, via identifiers, profile selections, and build artifacts. Useful for cross-product compliance analysis.

**Parameters:**
- `rule_id` (string, required): Rule identifier

**Returns:** RuleProductAvailability object

#### get_requirement_file_path

Resolve the filesystem path for a specific requirement in a control file. Handles both inline (monolithic YAML) and directory-based (controls_dir) formats.

**Parameters:**
- `control_id` (string, required): Control framework identifier (e.g., "anssi", "srg_gpos")
- `requirement_id` (string, required): Requirement identifier (e.g., "R1", "SRG-OS-000001-GPOS-00001")
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** RequirementFilePath object

**Example:**
```json
{
  "control_id": "srg_gpos",
  "requirement_id": "SRG-OS-000001-GPOS-00001",
  "file_path": "/path/to/content/controls/srg_gpos/SRG-OS-000001-GPOS-00001.yml",
  "format": "directory",
  "exists": true
}
```

#### update_requirement_rules

Update the rules list and status for a specific requirement in a control file. Handles both inline (monolithic YAML) and directory-based (controls_dir) formats. Preserves Jinja2 templating, comments, and formatting.

**Parameters:**
- `control_id` (string, required): Control framework identifier (e.g., "anssi", "srg_gpos")
- `requirement_id` (string, required): Requirement identifier (e.g., "R1", "SRG-OS-000001-GPOS-00001")
- `rules` (array of strings, required): Rule IDs to set for this requirement (replaces existing rules)
- `status` (string, optional): Status to set (default: "automated"). Enum: `automated`, `partially_automated`, `manual`, `not_applicable`, `pending`
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** ControlUpdateResult object

**Example:**
```json
{
  "file_path": "/path/to/content/controls/anssi.yml",
  "requirements_added": 0,
  "requirements_updated": 1,
  "requirements_unchanged": 0,
  "success": true,
  "errors": []
}
```

#### list_unmapped_requirements

List requirements in a control file that need rule mappings. Returns requirements filtered by status, defaulting to "pending". Lighter than `get_control_details` when you only need the work queue.

**Parameters:**
- `control_id` (string, required): Control framework identifier (e.g., "anssi", "srg_gpos")
- `status_filter` (array of strings, optional): Status values to include (default: `["pending"]`). Common values: pending, manual, partial, does not meet
- `product` (string, optional): Product ID to scope to product-specific controls

**Returns:** Array of IndexedRequirement objects (includes requirements matching status filter OR with empty rules lists)

**Example:**
```json
[
  {
    "control_id": "anssi",
    "requirement_id": "R1",
    "title": "Minimize installed services",
    "description": "Only install strictly necessary services...",
    "rules": [],
    "status": "pending",
    "levels": ["minimal"]
  }
]
```

## Data Models

### ProductSummary

```typescript
{
  product_id: string;
  name: string;
  product_type: string;
  version?: string;
  description?: string;
}
```

### ProductDetails

```typescript
{
  product_id: string;
  name: string;
  product_type: string;
  version?: string;
  description?: string;
  profiles: string[];
  benchmark_root: string;
  product_dir: string;
  cpe?: string;
  stats?: ProductStats;
  last_modified?: string;
}
```

### RuleSearchResult

```typescript
{
  rule_id: string;
  title: string;
  severity: string;
  description?: string;
  products: string[];
  file_path: string;
}
```

### RuleDetails

```typescript
{
  rule_id: string;
  title: string;
  description: string;
  rationale?: string;
  severity: string;
  identifiers: RuleIdentifiers;
  references: RuleReferences;
  products: string[];
  platforms: string[];
  remediations: Record<string, boolean>;
  checks: Record<string, boolean>;
  test_scenarios: string[];
  file_path: string;
  rule_dir: string;
  last_modified?: string;
  template?: Record<string, string>;
}
```

### ValidationResult

```typescript
{
  valid: boolean;
  errors: ValidationError[];
  warnings: ValidationError[];
  fixes_applied: string[];
}
```

### ScaffoldingResult

```typescript
{
  success: boolean;
  rule_id: string;
  rule_dir: string;
  message: string;
  files_created: string[];
  validation?: ValidationResult;
}
```

### RenderedRule

```typescript
{
  rule_id: string;
  product: string;
  rendered_yaml?: string;
  rendered_oval?: string;
  rendered_remediations: Record<string, string>;
  build_path: string;
}
```

### DatastreamInfo

```typescript
{
  product: string;
  datastream_path: string;
  file_size: number;
  build_time?: string;
  profiles_count: number;
  rules_count: number;
  exists: boolean;
}
```

### RenderSearchResult

```typescript
{
  rule_id: string;
  product: string;
  match_type: string;
  match_snippet: string;
  file_path: string;
}
```

### ParsedDocument

```typescript
{
  title: string;
  sections: DocumentSection[];
  requirements: ExtractedRequirement[];
  metadata: Record<string, any>;
  source_path?: string;
  source_type: "pdf" | "markdown" | "text" | "html";
  parsed_at: string;
}
```

### ControlFile

```typescript
{
  id: string;
  title: string;
  policy?: string;
  version?: string;
  source?: string;
  controls_dir?: string;
  description?: string;
  source_document?: string;
  includes: string[];
  controls: ControlRequirement[];
  levels?: ControlLevel[];
  metadata: Record<string, any>;
}
```

### ControlRequirement

```typescript
{
  id: string;
  title: string;
  description: string;
  rules: string[];
  related_rules: string[];
  status: "automated" | "partially_automated" | "manual" | "not_applicable" | "pending";
  references: Record<string, string[]>;
  notes?: string;
  levels: string[];
  section?: string;
}
```

### ControlStats

```typescript
{
  control_id: string;
  title: string;
  total: number;
  by_status: Record<string, number>;
  mapped: number;
  unmapped: number;
}
```

### IndexedRequirement

```typescript
{
  control_id: string;
  requirement_id: string;
  title: string;
  description: string;
  rules: string[];
  status: string;
  levels: string[];
}
```

### ControlRuleIndex

```typescript
{
  total_controls: number;
  total_requirements: number;
  total_mapped_rules: number;
  requirements: IndexedRequirement[];
}
```

### SimilarRequirement

```typescript
{
  control_id: string;
  requirement_id: string;
  title: string;
  description: string;
  rules: string[];
  similarity_score: number;
  matching_terms: string[];
}
```

### RuleProductAvailability

```typescript
{
  rule_id: string;
  products_with_identifiers: string[];
  products_in_profiles: Record<string, string[]>;
  platforms: string[];
  template?: Record<string, any>;
  has_build_artifacts: Record<string, boolean>;
}
```

### RequirementFilePath

```typescript
{
  control_id: string;
  requirement_id: string;
  file_path: string;
  format: "inline" | "directory";
  exists: boolean;
}
```

### ControlGenerationResult

```typescript
{
  policy_id: string;
  parent_file_path: string;
  requirement_files: string[];
  total_requirements: number;
  sections: string[];
  success: boolean;
  errors: string[];
  warnings: string[];
}
```

### ControlValidationResult

```typescript
{
  valid: boolean;
  errors: string[];
  warnings: string[];
  file_path?: string;
}
```

### RuleSuggestion

```typescript
{
  rule_id: string;
  confidence: number;
  reasoning: string;
  match_type: "exact_ref" | "keyword" | "semantic" | "description";
  metadata: Record<string, any>;
}
```

## Error Handling

All tools return structured error messages in the response:

```json
{
  "error": "Error message describing what went wrong",
  "details": "Additional details if available"
}
```

Common errors:
- Resource not found (e.g., invalid product_id, rule_id)
- Invalid parameters (e.g., wrong severity value)
- Validation failures
- File system errors

## Usage Examples

### Example 1: Find SSH Rules

```javascript
// Search for SSH-related rules
search_rules({
  query: "ssh timeout",
  severity: "medium",
  limit: 10
})

// Get details for a specific rule
get_rule_details({
  rule_id: "sshd_set_idle_timeout"
})
```

### Example 2: Create New Rule

```javascript
// Generate rule boilerplate
generate_rule_boilerplate({
  rule_id: "sshd_max_auth_tries",
  title: "Set SSH MaxAuthTries",
  description: "Configure maximum authentication attempts",
  severity: "medium",
  product: "rhel9",
  rationale: "Limit brute force attack attempts"
})

// Validate the generated rule
validate_rule_yaml({
  rule_yaml: "...",
  check_references: true
})
```

### Example 3: Explore Products

```javascript
// List all products
list_products()

// Get details for RHEL 9
get_product_details({
  product_id: "rhel9"
})

// List profiles for RHEL 9
list_profiles({
  product: "rhel9"
})
```
