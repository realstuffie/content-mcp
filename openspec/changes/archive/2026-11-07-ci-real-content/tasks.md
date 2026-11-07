## 1. CI

- [x] 1.1 Check out the pinned content commit in the test job and set `CONTENT_REPO`
- [x] 1.2 Add the "Content drift" workflow against content master
- [x] 1.3 Test Python 3.11 to 3.14
- [x] 1.4 Make mypy blocking
- [x] 1.5 Add `workflow_dispatch`

## 2. Dependencies and docs

- [x] 2.1 Add `jinja2` to the dependencies
- [x] 2.2 Describe the pin and the drift workflow in `CLAUDE.md`

## 3. Verification

- [x] 3.1 Lint both workflows with actionlint
- [x] 3.2 Run the CI install, test, lint and type steps from a clean install against the pinned commit
- [x] 3.3 Run the drift workflow's tests against content master
