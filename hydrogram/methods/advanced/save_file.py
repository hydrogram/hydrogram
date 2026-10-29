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

import functools
import inspect
import io
import math
from contextlib import AsyncExitStack
from hashlib import md5
from pathlib import PurePath
from typing import TYPE_CHECKING, BinaryIO

import hydrogram
from hydrogram import raw
from hydrogram.session import Session
from hydrogram.transmission import finish, open_file, run_sync

if TYPE_CHECKING:
    from collections.abc import Callable


class SaveFile:
    async def save_file(
        self: hydrogram.Client,
        path: str | BinaryIO,
        file_id: int | None = None,
        file_part: int = 0,
        progress: Callable | None = None,
        progress_args: tuple = (),
    ):
        """Upload a file onto Telegram servers, without actually sending the message to anyone.
        Useful whenever an InputFile type is required.

        .. note::

            This is a utility method intended to be used **only** when working with raw
            :obj:`functions <hydrogram.api.functions>` (i.e: a Telegram API method you wish to use which is not
            available yet in the Client class as an easy-to-use method).

        .. include:: /_includes/usable-by/users-bots.rst

        Parameters:
            path (``str`` | ``BinaryIO``):
                The path of the file you want to upload that exists on your local machine or a binary file-like object
                with its attribute ".name" set for in-memory uploads.

            file_id (``int``, *optional*):
                In case a file part expired, pass the file_id and the file_part to retry uploading that specific chunk.

            file_part (``int``, *optional*):
                In case a file part expired, pass the file_id and the file_part to retry uploading that specific chunk.

            progress (``Callable``, *optional*):
                Pass a callback function to view the file transmission progress.
                The function must take *(current, total)* as positional arguments (look at Other Parameters below for a
                detailed description) and will be called back each time a new file chunk has been successfully
                transmitted.

            progress_args (``tuple``, *optional*):
                Extra custom arguments for the progress callback function.
                You can pass anything you need to be available in the progress callback scope; for example, a Message
                object or a Client instance in order to edit the message with the updated progress status.

        Other Parameters:
            current (``int``):
                The amount of bytes transmitted so far.

            total (``int``):
                The total size of the file.

            *args (``tuple``, *optional*):
                Extra custom arguments as defined in the ``progress_args`` parameter.
                You can either keep ``*args`` or add every single extra argument in your function signature.

        Returns:
            ``InputFile``: On success, the uploaded file is returned in form of an InputFile object.

        Raises:
            RPCError: In case of a Telegram RPC error.
        """
        if path is None:
            return None

        async with self.save_file_semaphore, AsyncExitStack() as stack:
            part_size = 512 * 1024
            if isinstance(path, (str, PurePath)):
                fp = await stack.enter_async_context(open_file(path, "rb"))
            elif isinstance(path, io.IOBase):
                fp = path
            else:
                raise ValueError(
                    "Invalid file. Expected a file path as string or a binary (not text) file pointer"
                )

            await run_sync(fp.seek, 0, io.SEEK_END)
            file_size = await run_sync(fp.tell)
            if file_size == 0:
                raise ValueError("File size equals to 0 B")

            file_name = getattr(fp, "name", "file.jpg")
            file_size_limit_mib = 4000 if self.me.is_premium else 2000
            if file_size > file_size_limit_mib * 1024 * 1024:
                raise ValueError(f"Can't upload files bigger than {file_size_limit_mib} MiB")

            file_total_parts = math.ceil(file_size / part_size)
            is_big = file_size > 10 * 1024 * 1024
            is_missing_part = file_id is not None
            file_id = file_id or self.rnd_id()
            md5_sum = md5() if not is_big and not is_missing_part else None
            session = Session(
                self,
                await self.storage.dc_id(),
                await self.storage.auth_key(),
                await self.storage.test_mode(),
                is_media=True,
            )
            try:
                await session.start()
                await run_sync(fp.seek, part_size * file_part)
                while chunk := await run_sync(fp.read, part_size):
                    if is_big:
                        rpc = raw.functions.upload.SaveBigFilePart(
                            file_id=file_id,
                            file_part=file_part,
                            file_total_parts=file_total_parts,
                            bytes=chunk,
                        )
                    else:
                        rpc = raw.functions.upload.SaveFilePart(
                            file_id=file_id, file_part=file_part, bytes=chunk
                        )

                    # Backpressure: retain only one chunk and wait for its acknowledgement.
                    # Session.invoke handles safe pre-delivery recovery; ambiguous failures
                    # must escape without replaying the upload or reporting success.
                    if not await session.invoke(rpc):
                        raise OSError("Telegram rejected an uploaded file part")
                    if is_missing_part:
                        return None
                    if md5_sum is not None:
                        md5_sum.update(chunk)
                    file_part += 1
                    if progress:
                        func = functools.partial(
                            progress,
                            min(file_part * part_size, file_size),
                            file_size,
                            *progress_args,
                        )
                        if inspect.iscoroutinefunction(progress):
                            await func()
                        else:
                            await finish(self.loop.run_in_executor(self.executor, func))

                if is_big:
                    return raw.types.InputFileBig(
                        id=file_id, parts=file_total_parts, name=file_name
                    )
                return raw.types.InputFile(
                    id=file_id,
                    parts=file_total_parts,
                    name=file_name,
                    md5_checksum=md5_sum.hexdigest(),
                )
            finally:
                await finish(session.stop())
