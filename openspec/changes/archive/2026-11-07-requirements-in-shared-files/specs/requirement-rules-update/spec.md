## MODIFIED Requirements

### Requirement: Tool locates correct file for directory-based format
For policies with a requirement directory, the tool SHALL update the requirement in the file that defines it, found as `get_requirement_file_path` finds it: a file named after the requirement, the control file, or any other file in the directory. When the control file is not in `controls/` and no product is given, but the policy exists for some products, the error SHALL name those products.

#### Scenario: Requirement in a family file
- **WHEN** the tool is called with `control_id="nist_800_53"`, `requirement_id="ac-2"`, `product="rhel9"`
- **THEN** the tool SHALL update `ac-2` in `products/rhel9/controls/nist_800_53/ac.yml` and leave the other requirements in the file unchanged

#### Scenario: Policy defined only per product
- **WHEN** the tool is called with `control_id="nist_800_53"` and no product
- **THEN** the error SHALL list the products that define `nist_800_53`
