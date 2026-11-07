## Why

`initialized_content_repo` added a temporary content repository to `sys.path`
and reset the server's global objects on teardown, but it left Python's import
state behind. Importing `ssg` from the empty mock directory cached a namespace
package. A following integration fixture then failed to import `ssg.build_yaml`
from a real checkout.

The usual integration-first test order hid the problem because the real package
was already imported. A child pytest run with a unit test first reproduces it.

## What changes

- Save the original path and SSG module entries before initializing mock content.
- Restore the path and module entries in a finally block. Remove SSG modules
  introduced during the fixture and restore replaced preexisting modules.
- Use the fixture's shared monkeypatch for path setup so a test's later path
  edits cannot restore the mock path after fixture teardown.
- Add a subprocess regression for mock-first imports and a second mock fixture
  after real modules have loaded.
- Document the fixture behavior and unit-first test command.

## Capabilities

### New capabilities

- `test-repository-isolation`: restore Python paths and SSG module entries after
  mock repository tests.

## Scope

Only the test harness changes. Production repository initialization and the
server's SSG import behavior stay the same.
