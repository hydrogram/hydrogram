Hydrogram vs Pyrogram
=====================

Introduction
------------

This is a non-exhaustive list of differences between Hydrogram and Pyrogram.
It is updated periodically.

Key changes
-----------

- Support for the latest MTProto API layer with all new Telegram features
- Support for threads and topics in Telegram groups
- Support for multiple usernames.
- More active development
- Completely refactored, optimized and modernized codebase (utilizing Ruff)
- Open-source documentation
- Adopt modern packaging technologies and standards, such as pyproject.toml
- Use aiosqlite instead of sqlite3 for storage handling.
- Added the property `full_name` for User and Chat objects.
- Added the possibility to define a custom storage class

More technical changes
----------------------

- Declared the special variable `__all__` in all files so now we have a better IDE support.
- Specify optional parameters in methods as keyword-only to prevent potential breakage in the future when introducing new parameters.
- Migrated from setuptools to hatchling with rye.
- Transitioned from using `os.path` to utilizing `Pathlib`.
- Start utilizing towncrier to generate changelogs.

Fixes
-----

- Add FloodWait exception to media download
- Fixed a bug that would treat `0`, `False` or `None` as an empty message
- Fixed minor code issues
