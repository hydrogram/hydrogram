# Contributing to Hydrogram

Contributions are welcome: bug reports, features, tests, documentation, and code reviews. Read the [Code of Conduct](https://github.com/hydrogram/.github/blob/main/CODE_OF_CONDUCT.md) and [repository guidelines](AGENTS.md) before contributing.

## Questions, Feedback, and Issues

Use [GitHub Discussions](https://github.com/orgs/hydrogram/discussions) for questions and general feedback. Search existing issues before reporting a bug or requesting a feature, then use the appropriate issue template.

For bug reports, include:

- A minimal reproducible example and the steps to run it.
- Expected behavior, actual behavior, and relevant tracebacks.
- Hydrogram and Python versions, operating system, and relevant optional dependencies.

For feature requests, explain the use case, proposed behavior, and any relevant Telegram API references. Remove API hashes, bot tokens, session strings, and other credentials from examples and logs. Never attach session databases.

## Set Up the Development Environment

Install [uv](https://docs.astral.sh/uv/) and Git. Hydrogram supports Python 3.9 and later; `.python-version` selects Python 3.13 for local development. The Makefile commands below also require `make`.

Fork the repository, then run these commands, replacing `YOUR_USERNAME` with your GitHub username:

```bash
git clone https://github.com/YOUR_USERNAME/hydrogram.git
cd hydrogram
git remote add upstream https://github.com/hydrogram/hydrogram.git
git switch -c fix/describe-your-change
uv sync --locked --all-extras --dev
uv run make api
uv run pre-commit install
```

Run subsequent commands from the repository root. `uv run` uses the project's virtual environment without requiring activation.

`--locked` checks that `uv.lock` matches the project without updating it. The standard
`dependency-groups.dev` group installs testing and development tools and is included by
default; `--dev` makes that selection explicit. Use `uv add --dev` to add development
dependencies and commit both `pyproject.toml` and `uv.lock`.

`--all-extras` also installs Sphinx documentation dependencies and the optional
`fast` dependencies, including TgCrypto and, on supported platforms, uvloop. The
performance extras are optional for using Hydrogram. For a smaller development
environment, use `uv sync --locked --dev`; add `--extra docs` when working on
documentation.

## Find and Change the Right Code

- `hydrogram/`: the client library, including `methods/`, `types/`, filters, handlers, sessions, storage, and transports.
- `compiler/`: API schemas, RPC error definitions, templates, and generators.
- `tests/`: unit tests, including filter, parser, and file identifier tests.
- `docs/source/`: Sphinx sources and static assets.
- `news/`: release note fragments; `dev_tools/` contains maintenance scripts.

Generated raw API modules and RPC exceptions are ignored by Git. Change sources or templates under `compiler/api/` or `compiler/errors/`, then run `uv run make api`. Do not patch generated output directly.

When adding a client method, follow the existing method-class pattern and import and register the class in `hydrogram/methods/<category>/__init__.py`. Export new public types through the relevant package `__init__.py` files. Keep asynchronous operations nonblocking and preserve Python 3.9 compatibility.

## Coding Style

Use four-space indentation, UTF-8, LF endings, and final newlines; YAML uses two spaces. Follow existing naming conventions: `snake_case` for modules and functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Preserve license headers and document public APIs with type hints and docstrings matching neighboring code.

Ruff handles formatting and linting, with a target line length of 99 characters. Format changes, then run the same style checks as CI:

```bash
uv run ruff format .
uv run ruff format --check .
uv run ruff check . --ignore=E501
uv run pre-commit run --all-files
```

Pre-commit also checks whitespace, merge conflicts, private keys, TOML/YAML, and release fragment filenames. Its Ruff hooks can modify files, including applying unsafe fixes; review the resulting diff and rerun checks after fixes.

## Testing

Add regression tests for bug fixes and behavioral tests for new features. Use `test_*.py` filenames and `test_*` functions, placing tests alongside related suites. For asynchronous tests, use pytest-asyncio with explicit `@pytest.mark.asyncio` markers.

Generate the API before testing a fresh checkout or after compiler changes:

```bash
uv run make api
uv run pytest tests
```

Run a focused test or collect coverage with:

```bash
uv run pytest tests/filters/test_command.py::test_single
uv run pytest tests --cov=hydrogram --cov-report=term-missing
```

No minimum coverage percentage is configured. CI runs tests on Python 3.9–3.13 on Linux and macOS. Prefer isolated tests with local fixtures or test doubles, following the existing filter tests.

## Documentation and Package Builds

Update documentation when public behavior changes. Edit handwritten Sphinx sources under `docs/source/` and API docstrings in the library. Regenerate API reference pages before building or previewing:

```bash
uv run make api
uv run make docs
uv run make live-docs
```

`make docs` generates reference pages and builds HTML in `docs/build/html/`; it does not start a server. `make live-docs` starts the live preview and watches `hydrogram/`. Generated reference pages are ignored by Git; edit their source docstrings or compiler templates instead.

To build source and wheel distributions in `dist/`:

```bash
uv run --locked make build
```

Hatchling's custom wheel hook generates raw API bindings and exceptions for both
regular and editable installations. `make build` runs `uv build --no-sources`;
`uv build`, `pip install .`, and Git/archive installations also work directly.
Source distributions include the compiler inputs and build hook, and regenerate
the API when a wheel is built from them. Generated modules are explicitly included
as wheel artifacts even though Git ignores them. Both distributions use core
metadata 2.4 for compatibility with the validation tools pinned in `uv.lock`.

The package version is read from `__version__` in `hydrogram/__init__.py`; update
that value for a release, then update `uv.lock`. Hatchling is an isolated build
dependency and does not need to be installed as a development or runtime dependency.
The uv cache tracks the version source, build hook, compiler inputs, and NOTICE;
rerun `uv run make api` after compiler changes if regenerating manually.

## Commits and Release Notes

Use Conventional Commits:

```text
<type>[optional scope]: <description>
```

Types include `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, and `revert`. Use a short imperative summary without a trailing period. Separate optional body and footer paragraphs with blank lines, and wrap body text at 72 characters. For example:

```text
fix(session): prevent race condition during connection cleanup

Closes #123
```

Add a concise, user-facing release note at `news/<issue-or-pr>.<category>.rst`. Categories are `feature`, `bugfix`, `doc`, `removal`, and `misc`. For example, `news/123.bugfix.rst` could contain:

```rst
Prevent a race condition when closing a connection.
```

Preview release notes with `uv run make towncrier-draft`. Leave `NEWS.rst` assembly to the release process.

## Open a Pull Request

Follow `.github/PULL_REQUEST_TEMPLATE.md`. Include the motivation, behavior changes, linked issues, and any new dependencies. Describe the tests you ran, how to reproduce them, and your OS and Python version. Identify breaking changes and update affected documentation.

Before submitting, review the diff, run the tests and style checks above, and ensure your release fragment describes the final change. Keep the pull request focused so reviewers can assess it independently.
