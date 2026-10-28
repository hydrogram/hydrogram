<p align="center">
    <a href="https://github.com/hydrogram/hydrogram">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/hydrogram/hydrogram/main/docs/source/_static/hydrogram-dark.png">
            <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/hydrogram/hydrogram/main/docs/source/_static/hydrogram-light.png">
            <img alt="Hydrogram" width="128" src="https://raw.githubusercontent.com/hydrogram/hydrogram/main/docs/source/_static/hydrogram-light.png">
        </picture>
    </a>
    <br>
    <b>Python Framework for the Telegram MTProto API</b>
    <br>
    <a href="https://hydrogram.org">
        Homepage
    </a>
    •
    <a href="https://docs.hydrogram.org">
        Documentation
    </a>
    •
    <a href="https://docs.hydrogram.org/en/latest/releases.html">
        Releases
    </a>
    •
    <a href="https://t.me/HydrogramNews">
        News
    </a>
</p>

# Hydrogram

[![We use Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI package version](https://img.shields.io/pypi/v/hydrogram.svg)](https://pypi.org/project/hydrogram/)
[![PyPI license](https://img.shields.io/pypi/l/hydrogram.svg)](COPYING.lesser)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/hydrogram.svg)](https://pypi.org/project/hydrogram/)
[![Monthly PyPI downloads](https://img.shields.io/pypi/dm/hydrogram.svg)](https://pypi.org/project/hydrogram/)
[![Tests](https://github.com/hydrogram/hydrogram/actions/workflows/python.yml/badge.svg)](https://github.com/hydrogram/hydrogram/actions/workflows/python.yml)

Hydrogram is an asynchronous Python library for the Telegram MTProto API.
Build bots and user clients with high-level methods, message handlers, and filters,
or access the raw API when you need more control.

## Installation

Requires **Python 3.11 or later**. Install or upgrade with pip:

```bash
python -m pip install --upgrade hydrogram
```

To include optional performance dependencies (TgCrypto and, on supported platforms, uvloop):

```bash
python -m pip install --upgrade "hydrogram[fast]"
```

See the [speedups guide](https://docs.hydrogram.org/en/latest/topics/speedups.html)
for details, including how to enable uvloop.

## Quick start

Get your `api_id` and `api_hash` from [my.telegram.org/apps](https://my.telegram.org/apps).
Replace the placeholders below with your credentials and save the example as `hello.py`.
It replies to private messages from other users:

```python
from hydrogram import Client, filters

app = Client(
    "my_account",
    api_id=12345,
    api_hash="0123456789abcdef0123456789abcdef",
)


@app.on_message(filters.private & ~filters.me)
async def hello(client, message):
    await message.reply("Hello from Hydrogram!")


app.run()
```

Run `python hello.py` and follow the sign-in prompts. Once connected, send a private
message to the account from another account to see the reply.
Hydrogram saves the login in `my_account.session` for subsequent runs; keep this file private.

To sign in as a bot, also pass `bot_token` to `Client`.
See [authorization](https://docs.hydrogram.org/en/latest/start/auth.html)
and the [examples](https://docs.hydrogram.org/en/latest/start/examples/index.html) for more.

## Features

- **Async API:** Use `async` and `await` to handle updates and make concurrent requests.
- **High-level interface:** Work with messages, chats, and users through convenient methods and bound objects.
- **Handlers and filters:** Route updates to callbacks with composable filters.
- **Raw API access:** Call MTProto methods from the API layer supported by Hydrogram.
- **Type hints:** Get editor completion and support for static analysis.
- **Optional speedups:** Use TgCrypto for faster cryptography and uvloop as an alternative event loop.

## Resources

- The [documentation](https://docs.hydrogram.org) is the technical reference for Hydrogram. It includes detailed usage guides, API reference, and more.
- The [homepage](https://hydrogram.org) is the official website for Hydrogram. It includes a quickstart guide, a list of features, and more.
- Our [Telegram channel](https://t.me/HydrogramNews) is where we post news and updates about Hydrogram.
- Ask questions in [GitHub Discussions](https://github.com/orgs/hydrogram/discussions), or report bugs through [GitHub Issues](https://github.com/hydrogram/hydrogram/issues).

## Contributing

Hydrogram is an open source project and we welcome contributions from the community. We appreciate all types of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

See the [Contributing Guide](CONTRIBUTING.md) for development setup, tests, and pull request guidelines.

All contributors are expected to adhere to the [Code of Conduct](https://github.com/hydrogram/.github/blob/main/CODE_OF_CONDUCT.md). Please read it before contributing.

## Support development

Hydrogram is an open source project. Your support helps us maintain and improve the library. You can support the development of Hydrogram through the following platforms:

- [Liberapay](https://liberapay.com/hydrogram)
- [OpenCollective](https://opencollective.com/hydrogram)

## Thanks

- [Pyrogram](https://github.com/pyrogram/pyrogram) and its contributors for the inspiration and base code.

## License

Hydrogram is licensed under the **GNU Lesser General Public License v3.0 or later**
(`LGPL-3.0-or-later`). See [COPYING.lesser](COPYING.lesser) and [COPYING](COPYING)
for the full license terms, and [NOTICE](NOTICE) for copyright information.
