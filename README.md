<p align="center">
    <a href="https://github.com/AmanoTeam/hydrogram">
        <img src="https://hydrogram.amanoteam.com/docs/_static/hydrogram.png" alt="Hydrogram" width="128">
    </a>
    <br>
    <b>Telegram MTProto API Framework for Python</b>
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
    <a href="https://t.me/hydrogram">
        News
    </a>
</p>

## Hydrogram

> Elegant, modern and asynchronous Telegram MTProto API framework in Python for users and bots

``` python
from hydrogram import Client, filters

app = Client("my_account")


@app.on_message(filters.private)
async def hello(client, message):
    await message.reply("Hello from Hydrogram!")


app.run()
```

**Hydrogram** is a modern, elegant and asynchronous [MTProto API](https://hydrogram.amanoteam.com/docs/topics/mtproto-vs-botapi)
framework. It enables you to easily interact with the main Telegram API through a user account (custom client) or a bot
identity (bot API alternative) using Python.

### Support

If you'd like to support Hydrogram, you can consider:

- [Become a LiberaPay patron](https://liberapay.com/AmanoTeam).
- [Become an OpenCollective backer](https://opencollective.com/AmanoTeam).

### Key Features

- **Ready**: Install Hydrogram with pip and start building your applications right away.
- **Easy**: Makes the Telegram API simple and intuitive, while still allowing advanced usages.
- **Elegant**: Low-level details are abstracted and re-presented in a more convenient way.
- **Fast**: Boosted up by [TgCrypto](https://github.com/pyrogram/tgcrypto), a high-performance cryptography library written in C.
- **Type-hinted**: Types and methods are all type-hinted, enabling excellent editor support.
- **Async**: Fully asynchronous (also usable synchronously if wanted, for convenience).
- **Powerful**: Full access to Telegram's API to execute any official client action and more.

### Installing

``` bash
pip3 install hydrogram
```

### Resources

- Check out the docs at https://hydrogram.amanoteam.com/docs to learn more about Hydrogram, get started right
away and discover more in-depth material for building your client applications.
- Join the official channel at https://t.me/hydrogram and stay tuned for news, updates and announcements.
