import datetime
import sys
from pathlib import Path

docs_dir = Path(__file__).parent.parent
sys.path.insert(0, docs_dir.resolve().as_posix())

import hydrogram  # noqa: E402

project = "Hydrogram"
author = "Hydrogram"
copyright = f"{datetime.date.today().year}, {author}"
release = hydrogram.__version__

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinxcontrib.towncrier.ext",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "aiosqlite": ("https://aiosqlite.omnilib.dev/en/stable/", None),
}

html_use_modindex = False
html_use_index = False

napoleon_use_rtype = False
napoleon_use_param = False

master_doc = "index"
source_suffix = ".rst"
autodoc_member_order = "bysource"
autodoc_typehints = "none"

towncrier_draft_autoversion_mode = "draft"
towncrier_draft_include_empty = True
towncrier_draft_working_directory = Path(__file__).parent.parent.parent

pygments_style = "friendly"

html_theme = "furo"
html_title = f"{project} v{release} Documentation"
html_last_updated_fmt = (
    f"{datetime.datetime.now(tz=datetime.UTC).strftime('%d/%m/%Y, %H:%M:%S')} UTC"
)

html_copy_source = False

html_static_path = ["_static"]
html_css_files = [
    "css/all.min.css",
    "css/custom.css",
]

html_theme_options = {
    "navigation_with_keys": True,
    "dark_css_variables": {
        "admonition-title-font-size": "0.95rem",
        "admonition-font-size": "0.92rem",
    },
    "light_css_variables": {
        "admonition-title-font-size": "0.95rem",
        "admonition-font-size": "0.92rem",
    },
    "light_logo": "hydrogram-light.png",
    "dark_logo": "hydrogram-dark.png",
    "footer_icons": [  # all these icons are from https://react-icons.github.io/react-icons
        {
            "name": "Telegram Channel",
            "url": "https://t.me/HydrogramNews/",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8.287 5.906c-.778.324-2.334.994'
                "-4.666 2.01-.378.15-.577.298-.595.442-.03.243.275.339.69.47l.175.055c.408.133."
                "958.288 1.243.294.26.006.549-.1.868-.32 2.179-1.471 3.304-2.214 3.374-2.23.0"
                "5-.012.12-.026.166.016.047.041.042.12.037.141-.03.129-1.227 1.241-1.846 1.81"
                "7-.193.18-.33.307-.358.336a8.154 8.154 0 0 1-.188.186c-.38.366-.664.64.015 1.08"
                "8.327.216.589.393.85.571.284.194.568.387.936.629.093.06.183.125.27.187.331.23"
                "6.63.448.997.414.214-.02.435-.22.547-.82.265-1.417.786-4.486.906-5.751a1.426 "
                "1.426 0 0 0-.013-.315.337.337 0 0 0-.114-.217.526.526 0 0 0-.31-.093c-.3.005-.7"
                '63.166-2.984 1.09z"></path></svg>'
            ),
            "class": "",
        },
        {
            "name": "GitHub Organization",
            "url": "https://github.com/hydrogram/",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16"><path fill-rule="evenodd" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 '
                "2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.4"
                "9-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23"
                ".82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 "
                "0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.2"
                "7 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.5"
                "1.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 "
                '1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z">'
                "</path></svg>"
            ),
            "class": "",
        },
        {
            "name": "Hydrogram Website",
            "url": "https://hydrogram.org/",
            "html": (
                '<svg stroke="currentColor" fill="currentColor" stroke-width="0" '
                'viewBox="0 0 16 16" height="1em" width="1em" xmlns="http://www.w3.org/2000/svg">'
                '<path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm7.5-6.923c-.67.204-1.335.82-1.887 '
                "1.855-.143.268-.276.56-.395.872.705.157 1.472.257 2.282.287V1.077zM4.249 3.53"
                "9c.142-.384.304-.744.481-1.078a6.7 6.7 0 0 1 .597-.933A7.01 7.01 0 0 0 3.051 "
                "3.05c.362.184.763.349 1.198.49zM3.509 7.5c.036-1.07.188-2.087.436-3.008a9.124 "
                "9.124 0 0 1-1.565-.667A6.964 6.964 0 0 0 1.018 7.5h2.49zm1.4-2.741a12.344 "
                "12.344 0 0 0-.4 2.741H7.5V5.091c-.91-.03-1.783-.145-2.591-.332zM8.5 5.09V7.5h"
                "2.99a12.342 12.342 0 0 0-.399-2.741c-.808.187-1.681.301-2.591.332zM4.51 8.5c.03"
                "5.987.176 1.914.399 2.741A13.612 13.612 0 0 1 7.5 10.91V8.5H4.51zm3.99 0v2.409"
                "c.91.03 1.783.145 2.591.332.223-.827.364-1.754.4-2.741H8.5zm-3.282 3.696c.12.31"
                "2.252.604.395.872.552 1.035 1.218 1.65 1.887 1.855V11.91c-.81.03-1.577.13-2.28"
                "2.287zm.11 2.276a6.696 6.696 0 0 1-.598-.933 8.853 8.853 0 0 1-.481-1.079 8.38 "
                "8.38 0 0 0-1.198.49 7.01 7.01 0 0 0 2.276 1.522zm-1.383-2.964A13.36 13.36 0 0 1"
                " 3.508 8.5h-2.49a6.963 6.963 0 0 0 1.362 3.675c.47-.258.995-.482 1.565-.667zm"
                "6.728 2.964a7.009 7.009 0 0 0 2.275-1.521 8.376 8.376 0 0 0-1.197-.49 8.853 "
                "8.853 0 0 1-.481 1.078 6.688 6.688 0 0 1-.597.933zM8.5 11.909v3.014c.67-.204 "
                "1.335-.82 1.887-1.855.143-.268.276-.56.395-.872A12.63 12.63 0 0 0 8.5 11.91zm"
                "3.555-.401c.57.185 1.095.409 1.565.667A6.963 6.963 0 0 0 14.982 8.5h-2.49a1"
                "3.36 13.36 0 0 1-.437 3.008zM14.982 7.5a6.963 6.963 0 0 0-1.362-3.675c-.47.25"
                "8-.995.482-1.565.667.248.92.4 1.938.437 3.008h2.49zM11.27 2.461c.177.334.339.6"
                "94.482 1.078a8.368 8.368 0 0 0 1.196-.49 7.01 7.01 0 0 0-2.275-1.52c.218.283.4"
                "18.597.597.932zm-.488 1.343a7.765 7.765 0 0 0-.395-.872C9.835 1.897 9.17 1.282 "
                '8.5 1.077V4.09c.81-.03 1.577-.13 2.282-.287z"></path></svg>'
            ),
            "class": "",
        },
    ],
}
