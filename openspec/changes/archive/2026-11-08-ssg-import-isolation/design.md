## Reproduce the order failure

The regression launches a fresh pytest process. Its first test imports the
namespace package from the actual mock fixture and a temporary submodule. The
next test uses the actual real repository fixture with a small regular SSG
package containing the modules the initializer imports. Before the fix, that
fixture fails with `No module named 'ssg.build_yaml'`.

The remaining two child tests cover the opposite order. With the regular
package already loaded, another mock fixture replaces `sys.modules` entries
and adds a path through monkeypatch. The final test checks that the original
module identity and path were restored and the temporary submodule is gone.
These checks need no external checkout and run without inheriting the parent
pytest process's cached modules.

## Restore the prior module entries

Snapshot the `ssg` and `ssg.*` entries before setup. Teardown removes the current
entries under those names and puts the snapshot back. A fixture that began
without SSG leaves no cached package. A fixture that began with real SSG
preserves those module objects. Other module names are outside this cleanup.

The cleanup uses a finally block so it also runs if setup fails after changing
the import path. The existing reset of settings and repository wrapper globals
remains part of teardown.

## Share monkeypatch path restoration

An independent monkeypatch context was insufficient. If the test later called
the shared fixture's `monkeypatch.syspath_prepend`, its undo could restore a
snapshot that still contained the mock path after our context had removed it.
The regression caught that second leak.

Prepend the mock repository through the shared monkeypatch before the test can
make its own path changes. Save and restore the path in the fixture as well, so
both teardown steps return to the original state.

## Verification

The subprocess regression failed before the fix and now passes all four child
tests. The targeted run places fixture and hidden-profile unit tests before
the real profile visibility tests. All 27 tests pass in that order.

The full run with `tests/unit` before `tests/integration` passes all 517 tests
against content at `f09d243`. Formatting, Ruff, mypy, and whitespace checks pass.
