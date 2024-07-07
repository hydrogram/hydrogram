=========
Changelog
=========

..
    You should *NOT* be adding new change log entries to this file, this
    file is managed by towncrier. You *may* edit previous change logs to
    fix problems like typo corrections or such.
    To add a new change log entry, please see
    https://pip.pypa.io/en/latest/development/#adding-a-news-entry
    we named the news folder "news".
    WARNING: Don't drop the next directive!

.. towncrier-draft-entries:: |release| [UNRELEASED DRAFT]

.. towncrier release notes start

0.2.0 (2024-06-30)
===================

Deprecations and Removals
-------------------------

- Removed the `async-to-sync` wrapper, making the library fully asynchronous.
- Removed the `emoji` submodule. Please try out the `emoji` package from PyPI.

Features
--------

- Integrate pyromod patches into the project (many thanks to @usernein for his excellent work). To check out the pyromod specific features, have a look at https://pyromod.pauxis.dev/.
  You can use the features in the same way as in pyromod, except that you import them directly from the hydrogram package.
  `#1 <https://github.com/hydrogram/hydrogram/issues/1>`_
- Changed the minimum required version of Python to 3.9 and integrated the newest Python type hints.
  `#5 <https://github.com/hydrogram/hydrogram/issues/5>`_
- Added the attribute `is_participants_hidden` to the `Chat` type. If the list of members is hidden, `True` will be returned; otherwise, `False` will be returned.
  `#11 <https://github.com/hydrogram/hydrogram/issues/11>`_
- Allowed the use of filters.{private,group,channel} in callback queries.
  `#32 <https://github.com/hydrogram/hydrogram/issues/32>`_
- Added the `ChatBackground` type and the `background` field for the `Chat` object.
  `#33 <https://github.com/hydrogram/hydrogram/issues/33>`_
- Added support for error handlers.
  `#38 <https://github.com/hydrogram/hydrogram/issues/38>`_


Bugfixes
--------

- Fixed `Message.is_scheduled` field being always `False` when parsing `UpdateNewScheduledMessage`.
  `#14 <https://github.com/hydrogram/hydrogram/issues/14>`_
- Fixed an issue with the bool parsing of the raw api that was causing the wrong value to be returned.
  `#20 <https://github.com/hydrogram/hydrogram/issues/20>`_
- Make the quiz explanation an optional parameter.
  `#21 <https://github.com/hydrogram/hydrogram/issues/21>`_
- Support newly-created chats by increating `MIN_CHANNEL_ID` and `MIN_CHAT_ID`.
  `#25 <https://github.com/hydrogram/hydrogram/issues/25>`_


Improved Documentation
----------------------

- Added a tool to extract documentation parameters from the Telegram documentation, allowing us to self-host raw API documentation.
  `#34 <https://github.com/hydrogram/hydrogram/issues/34>`_


Misc
----

- Make `Message._parse` accept only keyword-only arguments.
  `#14 <https://github.com/hydrogram/hydrogram/issues/14>`_
- Added `if TYPE_CHECKING` to import modules for type checking only when needed. This flag avoids importing modules that are not needed for runtime execution. This change reduces the number of imports in the module and improves the performance of the code.
  `#24 <https://github.com/hydrogram/hydrogram/issues/24>`_
- Added the `from __future__ import annotations` statement to the codebase in order to simplify the usage of the typing module. This statement allows for the use of forward references in type hints, which can improve code readability and maintainability.
  `#24 <https://github.com/hydrogram/hydrogram/issues/24>`_
- Various fixes, improvements and micro-optimizations.



0.1.4 (2023-12-04)
===================

Bugfixes
--------

- Fix a boolean instead of file name in send_audio
  `#4 <https://github.com/hydrogram/hydrogram/issues/4>`_
- Prevent from closing BytesIO object in handle_download
  `#4 <https://github.com/hydrogram/hydrogram/issues/4>`_


0.1.3 (2023-12-03)
===================

Bugfixes
--------

- Fix handle_download file name
  `#3 <https://github.com/hydrogram/hydrogram/issues/3>`_


0.1.2 (2023-12-03)
===================

Bugfixes
--------

- Fix save_file reporting size as 0


0.1.1 (2023-12-01)
===================

Fixup release that fixes our logo url in PyPI.


0.1.0 (2023-12-01)
===================

Initial project release. To see all changes and improvements compared to Pyrogram, see `Hydrogram vs Pyrogram <https://hydrogram.org/en/latest/hydrogram-vs-pyrogram.html>`_
