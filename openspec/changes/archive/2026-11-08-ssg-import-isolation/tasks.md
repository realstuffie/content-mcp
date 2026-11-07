## Implementation and regression

- [x] Reproduce namespace package poisoning in a fresh unit-first pytest process.
- [x] Restore sys.path and the previous SSG module entries after mock fixtures.
- [x] Keep preloaded real module identities and remove temporary submodules.
- [x] Cover a test's own monkeypatch path edits and correct their teardown order.
- [x] Document the fixture and regression test using unslop.
- [x] Run the targeted unit-first visibility checks. All 27 tests pass.
- [x] Run the full unit-first suite and final code checks. All 517 tests pass.
