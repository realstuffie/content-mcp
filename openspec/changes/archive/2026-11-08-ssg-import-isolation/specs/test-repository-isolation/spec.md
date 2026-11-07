## ADDED Requirements

### Requirement: Mock repository import isolation

`initialized_content_repo` SHALL restore the original `sys.path` and the prior
`ssg` and `ssg.*` entries in `sys.modules` after each test. It SHALL remove SSG
entries introduced during the fixture and restore replaced preexisting entries.

#### Scenario: Mock namespace package imported first

- **WHEN** a unit test imports `ssg` from the mock repository's empty directory
- **THEN** teardown removes that namespace package and its temporary submodules
- **AND** a following real repository fixture can import its regular SSG package

#### Scenario: Real modules were already loaded

- **WHEN** a mock fixture starts with a regular SSG package and submodules cached
- **AND** the test replaces one of those module entries
- **THEN** teardown restores the original module objects

### Requirement: Path edits share a restoration point

The mock fixture SHALL restore its original path even when the test also uses
monkeypatch to change `sys.path`. A later monkeypatch undo SHALL NOT reintroduce
the mock repository path.

#### Scenario: Test prepends another directory

- **WHEN** the mock fixture and its test both prepend paths through monkeypatch
- **THEN** their completed teardown leaves the original path
- **AND** neither temporary path remains available for later imports

### Requirement: Import order regression

The regression suite SHALL exercise a mock repository before a regular SSG
package in a fresh pytest process. It SHALL also verify mock fixture teardown
after real SSG modules have loaded. It SHALL require no external checkout and
bound the child process's runtime.

#### Scenario: Both fixture orders

- **WHEN** the regression runs
- **THEN** the mock-first import and the later real import both pass
- **AND** another mock fixture preserves the preloaded real module identities
