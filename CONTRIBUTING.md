# Contributing to duvc-ctl

Thanks for contributing! Follow these guidelines to ensure smooth collaboration.

## Reporting Issues

- **Search first:** Check existing issues.
- **New issue:** Use the template. Include:
    - Description
    - Steps to reproduce
    - Expected vs. actual behavior
    - Environment (OS, compiler, hardware)
    - Logs/screenshots
- **Labels:** Add tags like `bug`, `feature`, `docs`.


## Submitting Pull Requests

1. **Fork \& Branch:** Create a branch: `feature/my-feature` or `fix/issue-123`.
2. **Commit Messages:** Use semantic style:
    - `feat: add new property`
    - `fix: resolve memory leak`
    - `docs: update README`
3. **PR Guidelines:**
    - Reference related issues (\#123)
    - Describe changes and why
    - Include tests for new features/bugs
    - Ensure code builds and tests pass
    - Keep PRs focused; split large changes
4. **Review Process:** Address feedback promptly. Maintainers will merge once approved.

## Code Guidelines

- **C++ Standard:** C++17
- **Naming:**
    - Classes: `PascalCase`
    - Functions/vars: `snake_case`
    - Constants: `UPPER_CASE`
- **Style Rules:**
    - Use RAII for resources
    - Error handling: `duvc::Result<T>`
    - Platform code: `#ifdef _WIN32`
    - Doxygen comments for public APIs
    - No exceptions in C API
- **Files:** Use `#pragma once`; follow existing structure.
- **Use clang-format:** Format all C++ files on LLVM style


## Testing

- **Add tests:** Unit for logic, integration for devices.
- **Coverage:** Test edge cases, errors.
- **Run tests:** All must pass before PR.


## Other Guidelines

- **Branching:** Main is protected; use features branches.
- **Licensing:** Contributions under MIT license.
- **Questions:** Open an issue or discussion.
