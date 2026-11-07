## 1. Reproduce protocol failures

- [x] 1.1 Add SDK session tests using a temporary content repository.
- [x] 1.2 Reproduce resource discovery, MIME type, extra-path, and tool error failures.
- [x] 1.3 Cover timestamp serialization, Unicode, partial results, and concurrent calls.
- [x] 1.4 Add a real stdio subprocess test with bounded waits and cleanup.

## 2. Fix protocol handling

- [x] 2.1 Convert SDK URIs to strings and return JSON resource contents.
- [x] 2.2 Serialize model timestamps in JSON mode.
- [x] 2.3 Separate concrete resource descriptors from URI templates.
- [x] 2.4 Reject extra segments in rendered-rule resource paths.
- [x] 2.5 Flag tool failures and return distinct resource error codes.
- [x] 2.6 Update direct dispatcher tests to expect exceptions.

## 3. Document and verify

- [x] 3.1 Document behavior in the README, API reference, and test guide.
- [x] 3.2 Add the proposal, design, and protocol requirements. Review prose with unslop.
- [x] 3.3 Run the full suite against the pinned content checkout. All 489 tests pass.
- [x] 3.4 Run formatting, Ruff, mypy, and whitespace checks.
- [x] 3.5 Record results and archive the completed change.
