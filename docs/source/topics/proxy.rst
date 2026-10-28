Proxy Settings
==============

Hydrogram supports SOCKS 4/5, HTTP (CONNECT), and native Telegram MTProto proxies
(MTProxy). Configure them with the ``proxy`` parameter of :class:`~hydrogram.Client`.
Existing SOCKS and HTTP settings continue to work without changes.

SOCKS and HTTP
--------------

Omit ``username`` and ``password`` if your proxy does not require authentication.

.. code-block:: python

    from hydrogram import Client

    proxy = {
        "scheme": "socks5",  # "socks4", "socks5", or "http"
        "hostname": "11.22.33.44",
        "port": 1234,
        "username": "username",
        "password": "password",
    }

    app = Client("my_account", proxy=proxy)
    app.run()

MTProxy
-------

Use the server, port, and secret supplied by your MTProxy operator. For a
``tg://proxy?server=...&port=...&secret=...`` link, copy those three values into
the dictionary; passing a proxy URL directly is not supported.

.. code-block:: python

    import os

    from hydrogram import Client

    app = Client(
        "my_account",
        proxy={
            "scheme": "mtproxy",
            "hostname": "proxy.example.com",
            "port": 443,
            "secret": os.environ["TELEGRAM_PROXY_SECRET"],
        },
    )
    app.run()

Scheme names are case-insensitive; ``mtproto`` is an alias for ``mtproxy``.
``hostname`` must be a non-empty hostname or IP address, and ``port`` must be
an integer from 1 to 65535. Proxy hostnames are resolved independently of the
``ipv6`` setting for Telegram DCs, allowing IPv4 and IPv6 proxy endpoints.
MTProxy uses ``secret`` instead of ``username`` and ``password``; do not supply
username/password credentials with this scheme.

Hydrogram automatically selects secret-authenticated, obfuscated abridged TCP
transport for MTProxy, overriding ``protocol_factory``. Production, test, media,
and CDN DC routing is encoded in the transport handshake. The proxy endpoint
replaces the direct DC socket address. Normal MTProto authorization and session
encryption still take place through that connection.

Supported secrets
~~~~~~~~~~~~~~~~~

* **Standard secrets:** exactly 32 hexadecimal characters representing 16 bytes.
  Uppercase and lowercase hexadecimal are accepted, including standard secrets
  whose first byte happens to be ``dd`` or ``ee``.
* **Padded intermediate secrets:** a ``dd`` prefix followed by a 16-byte secret
  (34 hexadecimal characters total) are currently unsupported.
* **Fake-TLS secrets:** an ``ee`` prefix, secret, and camouflage domain are
  currently unsupported.
* Base64-encoded secrets, byte strings, and full proxy links are unsupported.

Invalid MTProxy settings raise ``ValueError`` before opening a connection.
Error messages do not include the secret. A correctly formatted but incorrect
secret cannot be authenticated locally: the proxy may close the connection or
remain silent, and normal session timeout/retry handling applies. MTProxy has no
separate success reply to its obfuscated transport handshake.

Padded intermediate transport and fake-TLS emulation are separate follow-up
work. They require their own framing/padding and TLS camouflage handshakes,
respectively; removing their prefixes does not enable those modes. Choose a
proxy endpoint that accepts standard obfuscated abridged connections.

See Telegram's `MTProxy guide <https://core.telegram.org/proxy>`_ and
`transport obfuscation specification
<https://core.telegram.org/mtproto/mtproto-transports#transport-obfuscation>`_
for protocol details.
