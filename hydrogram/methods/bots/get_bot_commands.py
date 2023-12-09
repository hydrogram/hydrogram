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


import hydrogram
from hydrogram import raw, types


class GetBotCommands:
    async def get_bot_commands(
        self: "hydrogram.Client",
        scope: "types.BotCommandScope" = types.BotCommandScopeDefault(),
        language_code: str = "",
    ) -> list["types.BotCommand"]:
        """Get the current list of the bot's commands for the given scope and user language.
        Returns Array of BotCommand on success. If commands aren't set, an empty list is returned.

        The commands passed will overwrite any command set previously.
        This method can be used by the own bot only.

        .. include:: /_includes/usable-by/bots.rst

        Parameters:
            scope (:obj:`~hydrogram.types.BotCommandScope`, *optional*):
                An object describing the scope of users for which the commands are relevant.
                Defaults to :obj:`~hydrogram.types.BotCommandScopeDefault`.

            language_code (``str``, *optional*):
                A two-letter ISO 639-1 language code.
                If empty, commands will be applied to all users from the given scope, for whose language there are no
                dedicated commands.

        Returns:
            List of :obj:`~hydrogram.types.BotCommand`: On success, the list of bot commands is returned.

        Example:
            .. code-block:: python

                # Get commands
                commands = await app.get_bot_commands()
                print(commands)
        """

        r = await self.invoke(
            raw.functions.bots.GetBotCommands(
                scope=await scope.write(self),
                lang_code=language_code,
            )
        )

        return types.List(types.BotCommand.read(c) for c in r)
