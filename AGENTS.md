# Repository Guidelines

## Project Structure & Module Organization

Hydrogram is an async Telegram MTProto client library supporting Python 3.9+.

- `hydrogram/`: client, methods, types, filters, handlers, sessions, storage, transports, and crypto.
- `compiler/`: API schemas, error definitions, templates, and generators.
- `tests/`: pytest suites for filters, parsers, and file identifiers.
- `docs/source/`: Sphinx sources; `_static/` contains assets.
- `news/`: Towncrier fragments; `dev_tools/`: maintenance scripts.

See `CONTRIBUTING.md` for the full workflow.

## Build, Test, and Development Commands

Run from the repository root:

- `uv sync --all-extras --dev`: install development tools and optional dependencies.
- `uv run make api`: generate raw bindings and exceptions before testing fresh checkouts.
- `uv run pytest tests`: run tests.
- `uv run ruff format .`: format; `uv run ruff check . --ignore=E501`: lint as CI does.
- `uv run pre-commit install`: enable hooks; `uv run pre-commit run --all-files`: check everything.
- `uv build`: build distributions with Hatchling.
- `uv run make docs`: generate references and build HTML; `uv run make live-docs`: preview.

## Coding Style & Naming Conventions

Use four spaces (two for YAML), UTF-8, LF, and final newlines. Ruff targets 99-character lines. Use `snake_case` functions/modules, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants.

Type public APIs; use `from __future__ import annotations` for postponed annotations, including `str | None` on Python 3.9. Keep runtime expressions compatible with 3.9; move type-only imports into `TYPE_CHECKING` blocks. Follow neighboring Sphinx docstrings, including parameters, returns, and examples.

Preserve existing copyright notices. New Python files need the LGPL header with Hydrogram's copyright; see `compiler/docs/compiler.py`.

## Testing Guidelines

Use pytest, pytest-asyncio (`@pytest.mark.asyncio`), and pytest-cov. Name files `test_*.py` and functions `test_*`. Add regression/behavioral tests; run focused tests, then the suite. Coverage: `uv run pytest tests --cov=hydrogram`; no minimum is configured. CI covers Python 3.9–3.13 on Linux/macOS.

## Commit & Pull Request Guidelines

Use Conventional Commits, e.g. `fix(session): prevent connection cleanup race`. Follow `.github/PULL_REQUEST_TEMPLATE.md`: explain changes, link issues, document validation and OS/Python versions. Update documentation and add `news/<issue-or-pr>.<category>.rst` (`feature`, `bugfix`, `doc`, `removal`, `misc`).

## Architecture & Implementation Boundaries

- Edit compiler inputs/templates and regenerate API output.
- Register method classes in `hydrogram/methods/<category>/__init__.py` mixins to expose them on `Client`.
- Derive public Telegram objects from `Object`; export types through subpackage and `hydrogram/types/__init__.py`. Preserve client binding for bound methods.
- Implement storage backends against `hydrogram/storage/base.py:BaseStorage`.
- Keep blocking work off the event loop; preserve executor paths for synchronous callbacks/crypto.
- Never commit credentials or session files.
