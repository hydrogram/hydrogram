# Contributing to Hydrogram

Welcome, and thank you for your interest in contributing to Hydrogram!

Hydrogram is an open source project that depends on the generous help of contributors who volunteer their time and skills. We appreciate your involvement and support.

You can contribute in many ways, not only by writing code. This document aims to give you a high-level overview of how you can get involved.

## Asking Questions

If you have a question, please use the [discussions](https://github.com/orgs/hydrogram/discussions) instead of opening an issue. Simply start a discussion with the Q&A topic and our community will gladly answer.

## Providing Feedback

Feedback from the community is very important to us at Hydrogram. You can share your thoughts and suggestions by creating [discussions](https://github.com/orgs/hydrogram/discussions).

## Creating Issues

Have you identified a reproducible problem in Hydrogram? Do you have a feature request? Here's how you can report your issue as efficiently as possible.

### Look For an Existing Issue

Before creating a new issue, check the open issues to see if someone else has already reported the same problem or requested the same feature.

If you find an existing issue that is relevant to yours, you can comment on it and express your support or disagreement with a reaction:

- upvote 👍
- downvote 👎

If none of the open issues match your case, then create a new issue following the guidelines below..

### How to Write a Bug Report

A bug report should contain the following information:

- A clear and descriptive title that summarizes the problem.
- A brief description of what you were doing when the bug occurred, and what you expected to happen.
- A detailed description of the actual behavior and how it differs from the expected behavior.
- Steps to reproduce the bug, preferably with screenshots or a video recording.
- The version of Hydrogram and the operating system you are using.
- Any relevant error messages or logs.

### How to Write a Feature Request

A feature request should contain the following information:

- A clear and descriptive title that summarizes the feature.
- A brief explanation of why you need this feature and how it would benefit the project and the community.
- A detailed description of how the feature should work and what it should look like, preferably with mockups or examples.
- Optionally any relevant links or references to similar features in other projects or applications.

## Creating a Pull Request

To contribute code to Hydrogram, simply open a pull request by following the guide below.

You can read more about pull requests in the [GitHub docs](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request).

### Setting Up Development Environment

1. Fork the Hydrogram repository to your GitHub account.
2. Clone your forked repository of Hydrogram to your computer:

bash```
git clone <https://github.com/><your username>/hydrogram
cd hydrogram```

4. Add a track to the original repository:

bash```
git remote add upstream <https://github.com/hydrogram/hydrogram>```

5. Install dependencies:

Hydrogram uses and recommends [Rye](https://rye-up.com/) for managing virtual environmens and dependencies.

bash```
rye sync --all-features```

> We use `--all-features` to install all the optional dependencies, which are required to run the tests and build the documentation.

6. Install pre-commit hooks:

[Pre-commit](https://pre-commit.com/) is a tool that runs various checks before you make a commit. It helps you avoid committing any errors or warnings that might break your code or violate the coding standards.

bash```
pre-commit install```

### Format the code (code-style)

Hydrogram uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting the code to maintain it consistent and clean. You should [install](https://docs.astral.sh/ruff/installation/) and run Ruff on your code before committing:

bash```
ruff check .```

However, you can also rely on [pre-commit](https://pre-commit.com/) for it:

bash```
pre-commit run --run-all-files```

### Run tests

All changes should be tested:

bash```
pytest tests```

Remember to write tests for your new features or modify the existing tests to cover your code changes. Testing is essential to ensure the quality and reliability of your code.

### Docs

We use Sphinx to generate documentation in the `docs` directory. You can edit the sources and preview the changes using a live-preview server with:

bash```
sphinx-autobuild docs/source/ docs/build/ --watch hydrogram/```

### Commit Messages

We use conventional commits, which provide a standardized and structured format for commit messages. This helps ensure clear and consistent communication about the changes made in each commit.

- **Commit messages**: The commit messages should follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification, which provides a structured and consistent format for describing the changes in the commits. The commit messages should have the following structure:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

where:

- `<type>`: This is a keyword that indicates the kind of change that the commit introduces. It can be one of the following values: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, or `revert`.
- `[optional scope]`: This is an optional identifier that specifies the scope of the change. It can be a module, a component, a file, or any other logical unit of the project.
- `<description>`: This is a short and concise summary of the change in the present tense and imperative mood. It should not end with a period.
- `[optional body]`: This is an optional section that provides more details and context about the change. It should be separated from the summary by a blank line and wrapped at 72 characters.
- `[optional footer(s)]`: This is an optional section that provides additional information such as references to issues, breaking changes, or acknowledgments. It should be separated from the body by a blank line and follow the format `<key>: <value>`.

For example:

```
feat(storage): support multiple database using orm

This commit adds support for multiple databases using the tortoise-orm. It also updates the configuration file to allow the user to specify the database type and connection string.

BREAKING CHANGE: The database configuration has changed. The user must update the configuration file to specify the database type and connection string.

Closes #123
```

### Describing Changes

Write a concise summary of your changes in one or more sentences, so that bot developers can see what's new or updated in the library. Create a file named `<code>.<category>.rst` in the `news` directory and include your description there.

`<code>` is the issue or pull request number. After the release, a link to this issue will be added to the [changelog](https://docs.hydrogram.org/en/latest/releases.html) page.

`<category>` is a marker for the type of change, which can be one of:

- `feature` - when you add a new feature
- `bugfix` - when you fix a bug
- `doc` - when you improve the documentation
- `removal` - when you remove something from the library968sm6
- `misc` - when you change something in the core or the project configuration

If you are not sure which category to use, you can ask the core contributors for help.

## Thank You

Your contributions to open source, large or small, make great projects like this possible. Thank you for taking the time to contribute.
