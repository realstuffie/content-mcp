## 1. Model Update

- [ ] 1.1 Add `documentation: str | None = None` field to `TemplateSchema` in `src/content_agent/models/profile.py`

## 2. Core Logic

- [ ] 2.1 Add `_get_template_documentation(self, template_name: str) -> str | None` method to `TemplateDiscovery` in `src/content_agent/core/discovery/templates.py` that reads `docs/templates/template_reference.md` from the content repo and extracts the section under the `#### <template_name>` heading
- [ ] 2.2 Call `_get_template_documentation` from `get_template_schema()` and pass the result to the `TemplateSchema` constructor as the `documentation` field

## 3. Tests

- [ ] 3.1 Add unit test: `_get_template_documentation` returns correct section content when template exists in reference file
- [ ] 3.2 Add unit test: `_get_template_documentation` returns `None` when template is not in reference file
- [ ] 3.3 Add unit test: `_get_template_documentation` returns `None` when reference file does not exist
- [ ] 3.4 Add unit test: `get_template_schema` includes `documentation` field in returned `TemplateSchema`
- [ ] 3.5 Add unit test: `TemplateSchema` serialization includes `documentation` field

## 4. Quality

- [ ] 4.1 Run `black --check src/ tests/` and fix any formatting issues
- [ ] 4.2 Run `ruff check src/ tests/` and fix any lint issues
- [ ] 4.3 Run `mypy src/` and fix any type errors
- [ ] 4.4 Run `pytest` and confirm all tests pass
