## Changes

- [x] Reproduce macros rendering with the first product's variables.
- [x] Keep one environment per set of variables, with a limit of 16.
- [x] Make environments with ssg.jinja's bytecode cache in a temporary directory.
- [x] Leave the caller's variables unchanged.
- [x] Check that profile memberships at f09d243 are unchanged.
- [x] Test with real macros for rhel9 and ubuntu2204, and with a fake ssg.jinja.
- [x] Update the README and OpenSpec requirements using unslop.
- [x] Run the full suite, formatting, Ruff, mypy, and whitespace checks.
