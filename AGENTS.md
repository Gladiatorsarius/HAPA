# Agent Instructions & Guidelines

All autonomous agents operating in this repository must strictly adhere to the following directives:

## 1. Test-Driven Development & Testing Standards
- **Always Write Tests:** Every new feature, bug fix, refactoring, or script addition must include corresponding automated unit or integration tests.
- **Verification:** Ensure that all tests pass prior to finalizing any task or proposing changes.

## 2. Output & File Management (`graphify-out`)
- **Always Commit `graphify-out` Files:** Any artifacts, generated data, graphs, or output files created or updated inside the `graphify-out/` directory **must** be staged and committed to version control.
- Do not add `graphify-out/` to `.gitignore` or skip committing its contents under any circumstances.