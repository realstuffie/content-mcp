## ADDED Requirements

### Requirement: Resolve inline format requirement path

The tool SHALL return the parent control file path when the control file uses inline format (no `controls_dir` field) and the requirement ID exists in the `controls:` list.

The returned `RequirementFilePath` model SHALL include:
- `control_id`: the control framework identifier
- `requirement_id`: the requirement identifier
- `file_path`: absolute path to the control file (e.g., `controls/anssi.yml`)
- `format`: `"inline"`
- `exists`: `True`

#### Scenario: Inline requirement found

- **WHEN** `get_requirement_file_path(control_id="anssi", requirement_id="R1")` is called and `controls/anssi.yml` exists with a `controls:` entry having `id: R1`
- **THEN** the tool returns `RequirementFilePath` with `format="inline"`, `file_path` pointing to `controls/anssi.yml`, and `exists=True`

### Requirement: Resolve directory-based requirement path

The tool SHALL return the individual requirement file path when the control file has a `controls_dir` field. The resolved path SHALL be `controls/<controls_dir>/<requirement_id>.yml`.

#### Scenario: Directory-based requirement file exists

- **WHEN** `get_requirement_file_path(control_id="srg_gpos", requirement_id="SRG-OS-000001-GPOS-00001")` is called and `controls/srg_gpos.yml` has `controls_dir: srg_gpos` and `controls/srg_gpos/SRG-OS-000001-GPOS-00001.yml` exists
- **THEN** the tool returns `RequirementFilePath` with `format="directory"`, `file_path` pointing to `controls/srg_gpos/SRG-OS-000001-GPOS-00001.yml`, and `exists=True`

#### Scenario: Directory-based requirement file does not exist

- **WHEN** `get_requirement_file_path(control_id="srg_gpos", requirement_id="SRG-OS-999999")` is called and `controls/srg_gpos.yml` has `controls_dir: srg_gpos` but `controls/srg_gpos/SRG-OS-999999.yml` does not exist
- **THEN** the tool returns `RequirementFilePath` with `format="directory"`, `file_path` pointing to the expected path, and `exists=False`

### Requirement: Return None for nonexistent control

The tool SHALL return `None` when the control file does not exist.

#### Scenario: Control file not found

- **WHEN** `get_requirement_file_path(control_id="nonexistent", requirement_id="R1")` is called and `controls/nonexistent.yml` does not exist
- **THEN** the tool returns `None`

### Requirement: Return None for nonexistent inline requirement

The tool SHALL return `None` when the control file uses inline format but the requirement ID is not found in the `controls:` list.

#### Scenario: Requirement ID not in inline controls list

- **WHEN** `get_requirement_file_path(control_id="anssi", requirement_id="NONEXISTENT")` is called and `controls/anssi.yml` exists but has no entry with `id: NONEXISTENT`
- **THEN** the tool returns `None`

### Requirement: Returned path is absolute

The `file_path` field in `RequirementFilePath` SHALL always be an absolute path.

#### Scenario: Path is absolute

- **WHEN** `get_requirement_file_path` returns a result
- **THEN** `result.file_path.is_absolute()` is `True`

### Requirement: MCP tool interface

The tool SHALL be exposed as an MCP tool named `get_requirement_file_path` with required parameters `control_id` (string) and `requirement_id` (string). When the requirement is not found, the tool SHALL return a descriptive error message.

#### Scenario: MCP tool returns structured result

- **WHEN** the MCP tool is called with valid `control_id` and `requirement_id`
- **THEN** the response includes a JSON-serialized `RequirementFilePath` object

#### Scenario: MCP tool returns error for not found

- **WHEN** the MCP tool is called with a `requirement_id` that does not exist in the given control
- **THEN** the response includes a text message indicating the requirement was not found

### Requirement: RequirementFilePath Pydantic model

The `RequirementFilePath` model SHALL be defined in `models/control.py` with fields: `control_id` (str), `requirement_id` (str), `file_path` (Path), `format` (Literal["inline", "directory"]), `exists` (bool).

#### Scenario: Model validation

- **WHEN** a `RequirementFilePath` is constructed with valid fields
- **THEN** all fields pass Pydantic v2 validation and `model_dump(mode="json")` serializes `file_path` as a string
