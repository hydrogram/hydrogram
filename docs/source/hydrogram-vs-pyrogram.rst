Hydrogram vs Pyrogram
=====================

Introduction
------------

This is a non-exhaustive list of differences between Hydrogram and Pyrogram.
It is updated periodically.

Changes
-------

- Support for the latest layer
- Support for threads/topics
- Improvements in IDE support by declaring ``__all__`` in files
- Mark optional parameters in methods as keyword-only, to avoid future breakage when adding new parameters
- Use of newer packaging technologies and standards, such as pyproject.toml
- Use of aiosqlite instead of sqlite3
- Open-source documentation
- More active development
- Completely refactored, optimized and modernized codes (Using Ruff)

Fixes
-----

- Add FloodWait exception to media download
- Fixed a bug that would treat `0`, `False` or `None` as an empty message
- Fixed minor code issues
