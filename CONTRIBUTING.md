# Contributing to RepoAura

Thank you for helping improve RepoAura. This repository distributes a GitHub Copilot prompt and its documentation; it is not an application codebase.

## Before opening an issue or pull request

- Check existing issues and pull requests for duplicates.
- For security vulnerabilities, follow [SECURITY.md](SECURITY.md); do not disclose them in a public issue.
- Do not include credentials, private repository content, personal data, or confidential prompts in issues, logs, screenshots, or test fixtures.

## Changes that fit this repository

Useful contributions include:

- improving the prompt's clarity, safety, and compatibility with documented Copilot behavior;
- fixing README or prompt inconsistencies;
- adding focused tests or validation for behavior implemented in this repository;
- improving GitHub issue and pull-request workflows.

Avoid adding placeholder files, unsupported capability claims, unrelated application infrastructure, or dependencies without a clear need.

## Pull request expectations

1. Keep changes focused and explain the problem they solve.
2. Update the README when repository contents, usage, or supported behavior changes.
3. Keep the prompt's frontmatter valid and synchronize its documented release version when changing it.
4. Run the repository checks:

   ```text
   python -m unittest discover --start-directory tests --verbose
   python tools/validate_repo.py --lint
   python tools/validate_repo.py --security
   ```

5. In the pull request description, report checks actually run and any limitations. Do not describe prompt instructions as runtime enforcement.

There is no required branch naming, commit-message format, release process, or response-time commitment.
