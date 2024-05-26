#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
#  This file is part of Hydrogram.
#
#  Hydrogram is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Hydrogram is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import os

import hydrogram
from hydrogram import raw
from hydrogram.utils import btoi, compute_password_hash, itob


class EnableCloudPassword:
    async def enable_cloud_password(
        self: hydrogram.Client, password: str, hint: str = "", email: str | None = None
    ) -> bool:
        """Enable the Two-Step Verification security feature (Cloud Password) on your account.

        This password will be asked when you log-in on a new device in addition to the SMS code.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            password (``str``):
                Your password.

            hint (``str``, *optional*):
                A password hint.

            email (``str``, *optional*):
                Recovery e-mail.

        Returns:
            ``bool``: True on success.

        Raises:
            ValueError: In case there is already a cloud password enabled.

        Example:
            .. code-block:: python

                # Enable password without hint and email
                await app.enable_cloud_password("password")

                # Enable password with hint and without email
                await app.enable_cloud_password("password", hint="hint")

                # Enable password with hint and email
                await app.enable_cloud_password("password", hint="hint", email="user@email.com")
        """
        r = await self.invoke(raw.functions.account.GetPassword())

        if r.has_password:
            raise ValueError("There is already a cloud password enabled")

        r.new_algo.salt1 += os.urandom(32)
        new_hash = btoi(compute_password_hash(r.new_algo, password))
        new_hash = itob(pow(r.new_algo.g, new_hash, btoi(r.new_algo.p)))

        await self.invoke(
            raw.functions.account.UpdatePasswordSettings(
                password=raw.types.InputCheckPasswordEmpty(),
                new_settings=raw.types.account.PasswordInputSettings(
                    new_algo=r.new_algo,
                    new_password_hash=new_hash,
                    hint=hint,
                    email=email,
                ),
            )
        )

        return True
