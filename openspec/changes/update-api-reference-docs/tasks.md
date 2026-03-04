## 1. Update existing tool entry

- [ ] 1.1 Update `get_rule_details` entry in `docs/api_reference.md` to add the `include_rendered` (boolean, default true), `product` (string, optional), and `rendered_detail` (string, enum, default "metadata") parameters

## 2. Add Build Artifact Tools section

- [ ] 2.1 Add `### Build Artifact Tools` section after Scaffolding Tools with entries for `list_built_products`, `get_rendered_rule`, `get_datastream_info`, `search_rendered_content` — parameters and return types derived from `TOOLS` list in `tools.py`

## 3. Add Control File Tools section

- [ ] 3.1 Add `### Control File Tools` section after Build Artifact Tools with entries for `parse_policy_document`, `generate_control_files`, `suggest_rule_mappings`, `validate_control_file`, `review_control_generation`, `list_controls`, `get_control_details`, `search_control_requirements` — parameters and return types derived from `TOOLS` list in `tools.py`

## 4. Add missing Data Models

- [ ] 4.1 Add Data Models entries for new return types referenced by the added tool documentation (e.g., RenderedRule, DatastreamInfo, ControlDetails, ControlRequirement)

## 5. Verification

- [ ] 5.1 Verify the total tool entry count in `docs/api_reference.md` matches the `TOOLS` list length (19) in `tools.py`
- [ ] 5.2 Verify all new entries follow the same heading/parameter/returns/example format as existing entries
