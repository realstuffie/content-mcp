## MODIFIED Requirements

### Requirement: Resolve profile selections like the build

#### Scenario: Rules the product's build doesn't load
- **WHEN** a profile selects, through a control file, a rule outside the directories the product's build reads (its `benchmark_root` and any `additional_content_directories`), or a rule marked `documentation_complete: false`
- **THEN** the rule does not count as selected by that profile, as the build drops it from control selections
