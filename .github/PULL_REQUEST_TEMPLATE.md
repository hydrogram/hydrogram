## Description

<!-- Explain the problem, motivation, and resulting behavior. Link related issues;
use "Closes #123" only when this PR resolves the issue. List new dependencies
and explain why they are needed. -->

## Type of change

<!-- Select all that apply. -->

- [ ] Bug fix
- [ ] New feature or enhancement
- [ ] Documentation
- [ ] Refactoring, maintenance, or tooling
- [ ] Breaking change (describe the impact and migration steps below)

## Compatibility and migration

<!-- Describe public API or behavior changes and any required migration.
For breaking changes, include a before/after example when helpful.
Write "Not applicable" if there is no compatibility impact. -->

## Validation

<!-- List the exact commands you ran and their results, including focused tests.
Explain any checks you could not run. For documentation-only changes, describe
how you checked the documentation; runtime tests may be marked not applicable.
Typical checks from the repository root:
  uv run make api
  uv run pytest tests
  uv run ruff format --check .
  uv run ruff check . --ignore=E501
  uv run pre-commit run --all-files
For documentation builds: uv run make docs
-->

- Operating system:
- Python version:
- Commands and results:

## Checklist

<!-- Check applicable items and explain any exceptions. See CONTRIBUTING.md. -->

- [ ] I reviewed my changes and followed the repository guidelines.
- [ ] The code remains compatible with Python 3.9+.
- [ ] I added or updated tests for changed behavior, where applicable.
- [ ] Tests and style checks pass, or limitations are explained above.
- [ ] I updated affected public API docstrings and documentation, where applicable.
- [ ] I added a release fragment at `news/<issue-or-pr>.<category>.rst` (`feature`, `bugfix`, `doc`, `removal`, or `misc`).
- [ ] For compiler changes, I updated sources/templates and regenerated the API rather than editing generated files.
- [ ] For new public methods/types, I registered method mixins and exported types through the relevant `__init__.py` files.
