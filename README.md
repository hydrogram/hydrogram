<p align="center">
    <a href="https://github.com/AmanoTeam/hydrogram">
        <picture>
            <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/AmanoTeam/hydrogram/main/docs/source/_static/hydrogram-dark.png">
            <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/AmanoTeam/hydrogram/main/docs/source/_static/hydrogram-light.png">
            <img alt="Hydrogram" width="128" src="https://raw.githubusercontent.com/AmanoTeam/hydrogram/main/docs/source/_static/hydrogram-light.png">
        </picture>
    </a>
    <br>
    <b>Python Framework for the Telegram MTProto API</b>
    <br>
    <a href="https://hydrogram.amanoteam.com">
        Homepage
    </a>
    •
    <a href="https://hydrogram.amanoteam.com/docs">
        Documentation
    </a>
    •
    <a href="https://hydrogram.amanoteam.com/docs/releases">
        Releases
    </a>
    •
    <a href="https://t.me/HydrogramNews">
        News
    </a>
</p>

# Hydrogram

[![We use Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI package version](https://img.shields.io/pypi/v/hydrogram.svg)](https://pypi.python.org/pypi/hydrogram)
[![PyPI license](https://img.shields.io/pypi/l/hydrogram.svg)](https://pypi.python.org/pypi/hydrogram)
[![PyPI python versions](https://img.shields.io/pypi/pyversions/hydrogram.svg)](https://pypi.python.org/pypi/hydrogram)
[![PyPI download month](https://img.shields.io/pypi/dm/hydrogram.svg)](https://pypi.python.org/pypi/hydrogram/)
[![GitHub Actions status](https://github.com/AmanoTeam/hydrogram/actions/workflows/python.yml/badge.svg)](https://github.com/AmanoTeam/hydrogram/actions)

## Description

Hydrogram is a Python library for interacting with the Telegram MTProto API. It provides a simple and intuitive interface for developers to leverage the power of Telegram's API in their Python applications.

## Installation

To install Hydrogram, you need Python 3 installed on your system. If you don't have Python installed, you can download it from the official website.

To install Hydrogram, use pip:

```bash
pip install hydrogram -U
```

## Usage

Here is a basic example of how to use Hydrogram:

```python
from hydrogram import Client, filters

app = Client("my_account")


@app.on_message(filters.private)
async def hello(client, message):
    await message.reply("Hello from Hydrogram!")


app.run()
```

## Features

- **Easy to use:** Hydrogram provides a simple and intuitive interface for developers to leverage the power of Telegram's API in their Python applications, while still allowing advanced usages.
- **Elegant:** Low-level details are abstracted and re-presented in a more convenient way, making the Telegram API more accessible.
- **Fast:** Hydrogram is boosted by [TgCrypto](https://github.com/pyrogram/tgcrypto), a high-performance cryptography library written in C, which makes it faster than other Python Telegram libraries.
- **Type-hinted:** Types and methods are all type-hinted, enabling excellent editor support and making it easier to write and maintain code.
- **Async:** Hydrogram is fully asynchronous, which means it can handle multiple requests at the same time, making it faster and more efficient (also usable synchronously if wanted, for convenience).
- **Powerful:** Hydrogram provides full access to Telegram's API to execute any official client action and more, giving developers the flexibility to build powerful applications.

## Resources

- The [documentation](https://hydrogram.amanoteam.com/docs) is the technical reference for Hydrogram. It includes detailed usage guides, API reference, and more.
- The [homepage](https://hydrogram.amanoteam.com) is the official website for Hydrogram. It includes a quickstart guide, a list of features, and more.
- Our [Telegram channel](https://t.me/HydrogramNews) is where we post news and updates about Hydrogram.

## Contributing

Hydrogram is an open source project and we welcome contributions from the community. We appreciate all types of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

To get started, please review our [contribution guidelines](https://github.com/AmanoTeam/hydrogram/blob/main/CONTRIBUTING.rst) for more information. You can also help by [reporting bugs or feature requests](https://github.com/AmanoTeam/hydrogram/issues/new/choose).

If you're interested in contributing code, you'll need to set up the development environment. Here are the steps:

1. Clone the repository: `git clone https://github.com/AmanoTeam/hydrogram.git`
2. Install the dependencies: `pip install .[dev]`
3. Run the tests: `pytest`
4. Make your changes and submit a pull request.

All contributors are expected to adhere to the [Code of Conduct](https://github.com/AmanoTeam/hydrogram/blob/main/CODE_OF_CONDUCT.rst). Please read it before contributing.

We appreciate your help in making Hydrogram better!

## Support

Hydrogram is an open source project. Your support helps us maintain and improve the library. You can support the development of Hydrogram through the following platforms:

- [Liberapay](https://liberapay.com/hydrogram)
- [OpenCollective](https://opencollective.com/hydrogram)

## Thanks

- [Pyrogram](https://github.com/pyrogram/pyrogram) and its contributors for the inspiration and base code.

## License

You may copy, distribute and modify the software provided that modifications are described and licensed for free under [LGPL-3](https://www.gnu.org/licenses/lgpl-3.0.html). Derivatives works (including modifications or anything statically linked to the library) can only be redistributed under LGPL-3, but applications that use the library don't have to be.
