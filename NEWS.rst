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
