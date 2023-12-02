Hydrogram Branch Strategy and Git Convention
============================================

This document describes the branch strategy and git convention for the Hydrogram project. It aims to facilitate collaboration, code quality, and release management among the contributors.

Branch Strategy
---------------

The branch strategy is based on the `Gitflow Workflow`_, which defines a set of rules for creating, naming, and merging different types of branches. The main branches are:

- **main**: This branch contains the official release history of the project. It is updated only when a new version is released from the develop branch. It is always stable and deployable.
- **dev**: This branch contains the latest development changes of the project. It is updated regularly by merging feature, hotfix, or release branches. It is always functional but may contain bugs or unfinished features.

The supporting branches are:

- **feat**: These branches are created from the develop branch and merged back into it when the feature is completed. They are used to implement new features or enhancements for the project. They are named as ``feature/<feature-name>``, where ``<feature-name>`` is a short and descriptive name of the feature.
- **fix**: These branches are created from the develop branch and merged back into it when the fix is completed. They are used to fix bugs or issues in the project. They are named as ``fix/<issue-number>``, where ``<issue-number>`` is the issue number of the bug tracker.
- **hotfix**: These branches are created from the main branch and merged back into it and the develop branch when the hotfix is completed. They are used to fix urgent bugs or issues in the released versions of the project. They are named as ``hotfix/<issue-number>``, where `<issue-number>` is the issue number of the bug tracker.

Git Convention
--------------

The git convention defines a set of rules for writing commit messages, pull requests, and code reviews. The main rules are:

- **Commit messages**: The commit messages should follow the `Conventional Commits`_ specification, which provides a structured and consistent format for describing the changes in the commits. The commit messages should have the following structure:

.. code-block::

  <type>[optional scope]: <description>

  [optional body]

  [optional footer(s)]


where:

- ``<type>``: This is a keyword that indicates the kind of change that the commit introduces. It can be one of the following values: ``feat``, ``fix``, ``docs``, ``style``, ``refactor``, ``perf``, ``test``, ``build``, ``ci``, ``chore``, or ``revert``.
- ``[optional scope]``: This is an optional identifier that specifies the scope of the change. It can be a module, a component, a file, or any other logical unit of the project.
- ``<description>``: This is a short and concise summary of the change in the present tense and imperative mood. It should not end with a period.
- ``[optional body]``: This is an optional section that provides more details and context about the change. It should be separated from the summary by a blank line and wrapped at 72 characters.
- ``[optional footer(s)]``: This is an optional section that provides additional information such as references to issues, breaking changes, or acknowledgments. It should be separated from the body by a blank line and follow the format ``<key>: <value>``.

For example:

.. code-block::

  feat(storage): support multiple database using orm

  This commit adds support for multiple databases using the tortoise-orm. It also updates the configuration file to allow the user to specify the database type and connection string.

  BREAKING CHANGE: The database configuration has changed. The user must update the configuration file to specify the database type and connection string.

  Closes #123

- **Pull requests**: The pull requests should follow the same format as the commit messages, but with a more descriptive and explanatory body. The pull requests should also include a checklist of the tasks that have been done or need to be done, such as writing tests, updating documentation, or fixing linting errors. The pull requests should be linked to the corresponding issues or feature requests, if any, and should request a review from at least one other contributor. The pull requests should be merged only after passing the continuous integration checks and receiving approval from the reviewers.

For example:

.. code-block::

  feat(storage): support multiple database using orm

  Description

  This pull request adds support for multiple databases using the tortoise-orm. It also updates the configuration file to allow the user to specify the database type and connection string.

  Type of change

  - [x] Bug fix (non-breaking change which fixes an issue)
  - [x] New feature (non-breaking change which adds functionality)
  - [x] Breaking change (fix or feature that would cause existing functionality to not work as expected)
  - [ ] This change requires a documentation update

  How has this been tested?

  - [x] Unit tests
  - [ ] Integration tests

  Test configuration

  - Operating system: NixOS
  - Python version: 3.12.0

  - [x] My code follows the style guidelines of this project
  - [x] I have performed a self-review of my own code
  - [x] I have made corresponding changes to the documentation
  - [x] I have added tests that prove my fix is effective or that my feature works
  - [x] My changes generate no new warnings
  - [x] New and existing unit tests pass locally with my changes

- **Code reviews**: The code reviews should provide constructive and respectful feedback to the pull request authors. The code reviews should focus on the quality, readability, functionality, and maintainability of the code, as well as the adherence to the project standards and conventions. The code reviews should also suggest improvements, optimizations, or alternatives, if possible. The code reviews should use the following labels to indicate the status of the review:
- **Comment**: This means that the reviewer has some comments or questions about the pull request, but does not necessarily request changes.
- **Request changes**: This means that the reviewer requests some changes to the pull request before approving it. The changes should be clearly specified and justified.
- **LGTM**: This means "Looks Good To Me" and indicates that the reviewer approves the pull request and has no further comments or requests.
- **Resolve conversation**: This means that the reviewer is satisfied with the response or the resolution of the comment or the request.

For example:

Comment:

.. code-block::

  Thanks for working on this feature. The code looks good overall, but I have a few comments and suggestions.

  - in the storage.py file, line 42, why are you using a for loop instead of a list comprehension?
  - in the storage.py file, line 87, why are you using a ternary operator instead of an if-else statement?
  - in the test.py file, line 12, why are you not testing the error message that the function throws?

  Please let me know what you think and if you have any questions.

Request changes:

.. code-block::

  Thanks for the pull request. I have some comments and questions about the implementation and the performance.

  - in the storage.py file, line 42, you are using a for loop that is too slow. You should use a list comprehension instead.
  - in the storage.py file, line 87, you are using a ternary operator that is hard to read and understand. You should use an if-else statement instead.
  - in the test.py file, line 12, you are not testing the error message that the function throws. You should add an assertion to check that the error message matches the expected one.

  Please make these changes and update the pull request. Thank you.

LGTM:

.. code-block::

  Great work on this feature. The code is clean, efficient, and well-tested. I have no further comments or requests. You can merge the pull request.

Resolve conversation:

.. code-block::

  Thank you for explaining your reasoning and making the changes. I agree with your approach and I think it improves the code quality and performance. I have no more comments or requests. You can resolve this conversation.

.. _Gitflow Workflow: https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow
.. _Conventional Commits: https://www.conventionalcommits.org/en/v1.0.0/
