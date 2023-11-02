=========================
Contributing to Hydrogram
=========================

Contributions to Hydrogram are always welcome! Whether you're reporting a bug, adding a feature, or improving documentation, your help is appreciated.

===============
Code of Conduct
===============

All contributors are expected to adhere to the `Code of Conduct <https://github.com/AmanoTeam/hydrogram/blob/main/CODE_OF_CONDUCT.rst>`_. Please read it before contributing.

================
Reporting Issues
================

If you encounter any issues while using Hydrogram, please report them on our `GitHub Issues <https://github.com/AmanoTeam/hydrogram/issues/new>`_ page. When reporting an issue, please include:

* A clear, descriptive title.
* A detailed description of the issue.
* Steps to reproduce the issue.
* The version of Hydrogram you are using.
* The version of Python you are using.

========================
Submitting Pull Requests
========================

If you'd like to contribute code to Hydrogram, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Make your changes in your branch.
4. Run the tests to ensure your changes do not break existing functionality.
5. Submit a pull request to the main branch.

Please include a detailed description of your changes in the pull request.

=================
Development Setup
=================

To set up Hydrogram for development, please follow these steps:

1. Clone the repository.
2. Create a virtual environment and activate it.
3. Install the requirements for development.

===============
Commit Messages
===============

We use `Conventional Commits <https://www.conventionalcommits.org/en/v1.0.0/>`_ for our commit messages. This is a specification for adding human and machine readable meaning to commit messages. It allows us to automatically determine a semantic version bump (based on the types of commits landed), communicate the nature of changes to teammates, the public, and other stakeholders, and make it easier for people to contribute to our projects, by allowing them to explore a more structured commit history.

A good commit message is one that clearly and concisely tells WHAT changed, and WHY it changed.

Here's a quick summary of the Conventional Commits specification in a table:

+-----------------+-----------------------------------------------------------------------------------+
| Type            | Description                                                                       |
+=================+===================================================================================+
| fix             | A bug fix.                                                                        |
+-----------------+-----------------------------------------------------------------------------------+
| feat            | A new feature.                                                                    |
+-----------------+-----------------------------------------------------------------------------------+
| BREAKING CHANGE | A commit that has a message with BREAKING CHANGE: or appends a ! after the        |
|                 | type/scope, introduces a breaking API change.                                     |
+-----------------+-----------------------------------------------------------------------------------+
| chore           | Changes to the build process or auxiliary tools and libraries such as             |
|                 | documentation generation.                                                         |
+-----------------+-----------------------------------------------------------------------------------+
| docs            | Documentation only changes.                                                       |
+-----------------+-----------------------------------------------------------------------------------+
| style           | Changes that do not affect the meaning of the code (white-space, formatting,      |
|                 | missing semi-colons, etc).                                                        |
+-----------------+-----------------------------------------------------------------------------------+

==========
Code Style
==========

When submitting code, please follow the established coding style. We use `ruff <https://docs.astral.sh/ruff/>`_ to enforce PEP 8 style guidelines.

.. code-block:: bash

  ruff check .          # Lint all files in the current directory.
  ruff check . --fix    # Lint all files in the current directory, and fix any fixable errors.
  ruff check . --watch  # Lint all files in the current directory, and re-lint on change.

  ruff format .         # Format all files in the current directory.
