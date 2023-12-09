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

import logging
from typing import Union

import hydrogram
from hydrogram import raw, types

log = logging.getLogger(__name__)


class SignIn:
    async def sign_in(
        self: "hydrogram.Client",
        phone_number: str,
        phone_code_hash: str,
        phone_code: str,
    ) -> Union["types.User", "types.TermsOfService", bool]:
        """Authorize a user in Telegram with a valid confirmation code.

        .. include:: /_includes/usable-by/users.rst

        Parameters:
            phone_number (``str``):
                Phone number in international format (includes the country prefix).

            phone_code_hash (``str``):
                Code identifier taken from the result of :meth:`~hydrogram.Client.send_code`.

            phone_code (``str``):
                The valid confirmation code you received (either as Telegram message or as SMS in your phone number).

        Returns:
            :obj:`~hydrogram.types.User` | :obj:`~hydrogram.types.TermsOfService` | bool: On success, in case the
            authorization completed, the user is returned. In case the phone number needs to be registered first AND the
            terms of services accepted (with :meth:`~hydrogram.Client.accept_terms_of_service`), an object containing
            them is returned. In case the phone number needs to be registered, but the terms of services don't need to
            be accepted, False is returned instead.

        Raises:
            BadRequest: In case the arguments are invalid.
            SessionPasswordNeeded: In case a password is needed to sign in.
        """
        phone_number = phone_number.strip(" +")

        r = await self.invoke(
            raw.functions.auth.SignIn(
                phone_number=phone_number,
                phone_code_hash=phone_code_hash,
                phone_code=phone_code,
            )
        )

        if isinstance(r, raw.types.auth.AuthorizationSignUpRequired):
            return (
                types.TermsOfService._parse(terms_of_service=r.terms_of_service)
                if r.terms_of_service
                else False
            )
        await self.storage.user_id(r.user.id)
        await self.storage.is_bot(False)

        return types.User._parse(self, r.user)
