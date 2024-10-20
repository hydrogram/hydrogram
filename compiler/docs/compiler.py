#  Hydrogram - Telegram MTProto API Client Library for Python
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

import ast
import os
import re
import shutil
from pathlib import Path

DOCS_HOME_PATH = Path(__file__).parent.resolve()
REPO_HOME_PATH = DOCS_HOME_PATH.parent.parent

DOCS_DEST_PATH = REPO_HOME_PATH / "docs" / "source" / "telegram"
API_DOCS_DEST_PATH = REPO_HOME_PATH / "docs" / "source" / "api"

FUNCTIONS_PATH = REPO_HOME_PATH / "hydrogram" / "raw" / "functions"
TYPES_PATH = REPO_HOME_PATH / "hydrogram" / "raw" / "types"
BASE_PATH = REPO_HOME_PATH / "hydrogram" / "raw" / "base"

FUNCTIONS_BASE = "functions"
TYPES_BASE = "types"
BASE_BASE = "base"


def snake(s: str):
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def generate(source_path: Path, base_name: str):
    all_entities: dict[str, list[str]] = {}

    def build(path: Path, level=0):
        last = path.name

        for i in os.listdir(path):
            if not i.startswith("__"):
                item_path = path / i
                if item_path.is_dir():
                    build(item_path, level=level + 1)
                elif item_path.is_file():
                    with item_path.open(encoding="utf-8") as f:
                        p = ast.parse(f.read())

                    for node in ast.walk(p):
                        if isinstance(node, ast.ClassDef):
                            name = node.name
                            break
                    else:
                        continue

                    full_path = Path(last, snake(name).replace("_", "-") + ".rst")

                    if level:
                        full_path = Path(base_name, full_path)

                    namespace = "" if last in {"base", "types", "functions"} else last

                    full_name = f"{f'{namespace}.' if namespace else ''}{name}"

                    (DOCS_DEST_PATH / full_path).parent.mkdir(parents=True, exist_ok=True)

                    with (DOCS_DEST_PATH / full_path).open("w", encoding="utf-8") as f:
                        f.write(
                            page_template.format(
                                title=full_name,
                                title_markup="=" * len(full_name),
                                full_class_path="hydrogram.raw.{}".format(
                                    ".".join(full_path.parts[:-1]) + "." + name
                                ),
                            )
                        )

                    if last not in all_entities:
                        all_entities[last] = []

                    all_entities[last].append(name)

    build(source_path)

    for k, v in sorted(all_entities.items()):
        v = sorted(v)
        entities = []

        entities = [f'{i} <{snake(i).replace("_", "-")}>' for i in v]

        if k != base_name:
            inner_path = Path(base_name, k, "index.rst")
            module = f"hydrogram.raw.{base_name}.{k}"
        else:
            for i in sorted(all_entities, reverse=True):
                if i != base_name:
                    entities.insert(0, f"{i}/index")

            inner_path = Path(base_name, "index.rst")
            module = f"hydrogram.raw.{base_name}"

        with (DOCS_DEST_PATH / inner_path).open("w", encoding="utf-8") as f:
            if k == base_name:
                f.write(":tocdepth: 1\n\n")
                k = f"Raw {k}"

            f.write(
                toctree.format(
                    title=k.title(),
                    title_markup="=" * len(k),
                    module=module,
                    entities="\n    ".join(entities),
                )
            )

            f.write("\n")


def hydrogram_api():
    def get_title_list(s: str) -> list[str]:
        return [i.strip() for i in [j.strip() for j in s.split("\n") if j] if i]

    # Methods

    categories = {
        "utilities": """
        Utilities
            start
            stop
            run
            restart
            add_handler
            remove_handler
            stop_transmission
            export_session_string
            set_parse_mode
        """,
        "messages": """
        Messages
            send_message
            forward_messages
            copy_message
            copy_media_group
            send_photo
            send_audio
            send_document
            send_sticker
            send_video
            send_animation
            send_voice
            send_video_note
            send_media_group
            send_location
            send_venue
            send_contact
            send_cached_media
            send_reaction
            edit_message_text
            edit_message_caption
            edit_message_media
            edit_message_reply_markup
            edit_inline_text
            edit_inline_caption
            edit_inline_media
            edit_inline_reply_markup
            send_chat_action
            delete_messages
            get_messages
            get_media_group
            get_chat_history
            get_chat_history_count
            read_chat_history
            send_poll
            vote_poll
            stop_poll
            retract_vote
            send_dice
            search_messages
            search_messages_count
            search_global
            search_global_count
            download_media
            stream_media
            get_discussion_message
            get_discussion_replies
            get_discussion_replies_count
            get_custom_emoji_stickers
        """,
        "chats": """
        Chats
            join_chat
            leave_chat
            ban_chat_member
            unban_chat_member
            restrict_chat_member
            promote_chat_member
            set_administrator_title
            set_chat_photo
            delete_chat_photo
            set_chat_title
            set_chat_description
            set_chat_permissions
            pin_chat_message
            unpin_chat_message
            unpin_all_chat_messages
            get_chat
            get_chat_member
            get_chat_members
            get_chat_members_count
            get_dialogs
            get_dialogs_count
            set_chat_username
            get_nearby_chats
            archive_chats
            unarchive_chats
            add_chat_members
            create_channel
            create_group
            create_supergroup
            delete_channel
            delete_supergroup
            delete_user_history
            set_slow_mode
            mark_chat_unread
            get_chat_event_log
            get_chat_online_count
            get_send_as_chats
            set_send_as_chat
            set_chat_protected_content
            transfer_chat_ownership
        """,
        "users": """
        Users
            get_me
            get_users
            get_chat_photos
            get_chat_photos_count
            set_profile_photo
            delete_profile_photos
            set_username
            update_profile
            block_user
            unblock_user
            get_common_chats
            get_default_emoji_statuses
            set_emoji_status
        """,
        "invite_links": """
        Invite Links
            get_chat_invite_link
            export_chat_invite_link
            create_chat_invite_link
            edit_chat_invite_link
            revoke_chat_invite_link
            delete_chat_invite_link
            get_chat_invite_link_joiners
            get_chat_invite_link_joiners_count
            get_chat_admin_invite_links
            get_chat_admin_invite_links_count
            get_chat_admins_with_invite_links
            get_chat_join_requests
            delete_chat_admin_invite_links
            approve_chat_join_request
            approve_all_chat_join_requests
            decline_chat_join_request
            decline_all_chat_join_requests
        """,
        "contacts": """
        Contacts
            add_contact
            delete_contacts
            import_contacts
            get_contacts
            get_contacts_count
        """,
        "password": """
        Password
            enable_cloud_password
            change_cloud_password
            remove_cloud_password
        """,
        "bots": """
        Bots
            get_inline_bot_results
            send_inline_bot_result
            answer_callback_query
            answer_inline_query
            request_callback_answer
            send_game
            set_game_score
            get_game_high_scores
            set_bot_commands
            get_bot_commands
            delete_bot_commands
            set_bot_default_privileges
            get_bot_default_privileges
            set_chat_menu_button
            get_chat_menu_button
            answer_web_app_query
        """,
        "authorization": """
        Authorization
            connect
            disconnect
            initialize
            terminate
            send_code
            resend_code
            sign_in
            sign_in_bot
            sign_up
            get_password_hint
            check_password
            send_recovery_code
            recover_password
            accept_terms_of_service
            log_out
        """,
        "advanced": """
        Advanced
            invoke
            resolve_peer
            save_file
        """,
        "phone": """
        Phone:
            create_group_call
            discard_group_call
            invite_group_call_members
        """,
    }

    root = API_DOCS_DEST_PATH / "methods"

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with (DOCS_HOME_PATH / "template" / "methods.rst").open() as f:
        template = f.read()

    with (root / "index.rst").open("w") as f:
        fmt_keys = {}

        for k, v in categories.items():
            _, *methods = get_title_list(v)
            fmt_keys[k] = "\n    ".join(f"{m} <{m}>" for m in methods)

            for method in methods:
                with (root / f"{method}.rst").open("w") as f2:
                    title = f"{method}()"

                    f2.write(title + "\n" + "=" * len(title) + "\n\n")
                    f2.write(f".. automethod:: hydrogram.Client.{method}()")

            functions = ["idle", "compose"]

            for func in functions:
                with (root / f"{func}.rst").open("w") as f2:
                    title = f"{func}()"

                    f2.write(title + "\n" + "=" * len(title) + "\n\n")
                    f2.write(f".. autofunction:: hydrogram.{func}()")

        f.write(template.format(**fmt_keys))

    # Types

    categories = {
        "users_chats": """
        Users & Chats
            User
            Chat
            ChatPreview
            ChatPhoto
            ChatMember
            ChatPermissions
            ChatPrivileges
            ChatInviteLink
            ChatAdminWithInviteLinks
            ChatEvent
            ChatEventFilter
            ChatMemberUpdated
            ChatJoinRequest
            ChatJoiner
            Dialog
            Restriction
            EmojiStatus
            ChatBackground
        """,
        "messages_media": """
        Messages & Media
            Message
            MessageEntity
            Photo
            Thumbnail
            Audio
            Document
            Animation
            Video
            Voice
            VideoNote
            Contact
            Location
            Venue
            Sticker
            Game
            WebPage
            Poll
            PollOption
            Dice
            Reaction
            VideoChatScheduled
            VideoChatStarted
            VideoChatEnded
            VideoChatMembersInvited
            WebAppData
            MessageReactions
            ChatReactions
        """,
        "bot_keyboards": """
        Bot keyboards
            ReplyKeyboardMarkup
            KeyboardButton
            ReplyKeyboardRemove
            InlineKeyboardMarkup
            InlineKeyboardButton
            LoginUrl
            ForceReply
            CallbackQuery
            GameHighScore
            CallbackGame
            WebAppInfo
            MenuButton
            MenuButtonCommands
            MenuButtonWebApp
            MenuButtonDefault
            SentWebAppMessage
        """,
        "bot_commands": """
        Bot commands
            BotCommand
            BotCommandScope
            BotCommandScopeDefault
            BotCommandScopeAllPrivateChats
            BotCommandScopeAllGroupChats
            BotCommandScopeAllChatAdministrators
            BotCommandScopeChat
            BotCommandScopeChatAdministrators
            BotCommandScopeChatMember
        """,
        "input_media": """
        Input Media
            InputMedia
            InputMediaPhoto
            InputMediaVideo
            InputMediaAudio
            InputMediaAnimation
            InputMediaDocument
            InputPhoneContact
        """,
        "inline_mode": """
        Inline Mode
            InlineQuery
            InlineQueryResult
            InlineQueryResultCachedAudio
            InlineQueryResultCachedDocument
            InlineQueryResultCachedAnimation
            InlineQueryResultCachedPhoto
            InlineQueryResultCachedSticker
            InlineQueryResultCachedVideo
            InlineQueryResultCachedVoice
            InlineQueryResultArticle
            InlineQueryResultAudio
            InlineQueryResultContact
            InlineQueryResultDocument
            InlineQueryResultAnimation
            InlineQueryResultLocation
            InlineQueryResultPhoto
            InlineQueryResultVenue
            InlineQueryResultVideo
            InlineQueryResultVoice
            ChosenInlineResult
        """,
        "input_message_content": """
        InputMessageContent
            InputMessageContent
            InputPollOption
            InputTextMessageContent
        """,
        "authorization": """
        Authorization
            SentCode
            TermsOfService
        """,
    }

    root = API_DOCS_DEST_PATH / "types"

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with (DOCS_HOME_PATH / "template" / "types.rst").open() as f:
        template = f.read()

    with (root / "index.rst").open("w") as f:
        fmt_keys = {}

        for k, v in categories.items():
            _, *types = get_title_list(v)

            fmt_keys[k] = "\n    ".join(types)

            for type in types:
                with (root / f"{type}.rst").open("w") as f2:
                    f2.write(f"{type}\n" + "=" * len(type) + "\n\n")
                    f2.write(f".. autoclass:: hydrogram.types.{type}()\n")

        f.write(template.format(**fmt_keys))

    # Bound Methods

    categories = {
        "message": """
        Message
            Message.click
            Message.delete
            Message.download
            Message.forward
            Message.copy
            Message.pin
            Message.unpin
            Message.edit
            Message.edit_text
            Message.edit_caption
            Message.edit_media
            Message.edit_reply_markup
            Message.reply
            Message.reply_text
            Message.reply_animation
            Message.reply_audio
            Message.reply_cached_media
            Message.reply_chat_action
            Message.reply_contact
            Message.reply_document
            Message.reply_game
            Message.reply_inline_bot_result
            Message.reply_location
            Message.reply_media_group
            Message.reply_photo
            Message.reply_poll
            Message.reply_sticker
            Message.reply_venue
            Message.reply_video
            Message.reply_video_note
            Message.reply_voice
            Message.get_media_group
            Message.react
        """,
        "chat": """
        Chat
            Chat.archive
            Chat.unarchive
            Chat.set_title
            Chat.set_description
            Chat.set_photo
            Chat.ban_member
            Chat.unban_member
            Chat.restrict_member
            Chat.promote_member
            Chat.get_member
            Chat.get_members
            Chat.add_members
            Chat.join
            Chat.leave
            Chat.mark_unread
            Chat.set_protected_content
            Chat.unpin_all_messages
            Chat.ask
            Chat.listen
            Chat.stop_listening
        """,
        "user": """
        User
            User.archive
            User.unarchive
            User.block
            User.unblock
            User.ask
            User.listen
            User.stop_listening
        """,
        "callback_query": """
        Callback Query
            CallbackQuery.answer
            CallbackQuery.edit_message_text
            CallbackQuery.edit_message_caption
            CallbackQuery.edit_message_media
            CallbackQuery.edit_message_reply_markup
        """,
        "inline_query": """
        InlineQuery
            InlineQuery.answer
        """,
        "chat_join_request": """
        ChatJoinRequest
            ChatJoinRequest.approve
            ChatJoinRequest.decline
        """,
    }

    root = API_DOCS_DEST_PATH / "bound-methods"

    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)

    with (DOCS_HOME_PATH / "template" / "bound-methods.rst").open() as f:
        template = f.read()

    with (root / "index.rst").open("w") as f:
        fmt_keys = {}

        for k, v in categories.items():
            _, *bound_methods = get_title_list(v)

            fmt_keys[f"{k}_hlist"] = "\n    ".join(f"- :meth:`~{bm}`" for bm in bound_methods)

            fmt_keys[f"{k}_toctree"] = "\n    ".join(
                "{} <{}>".format(bm.split(".")[1], bm) for bm in bound_methods
            )

            for bm in bound_methods:
                with (root / f"{bm}.rst").open("w") as f2:
                    title = f"{bm}()"

                    f2.write(title + "\n" + "=" * len(title) + "\n\n")
                    f2.write(f".. automethod:: hydrogram.types.{bm}()")

        f.write(template.format(**fmt_keys))


def start():
    global page_template, toctree

    shutil.rmtree(DOCS_DEST_PATH, ignore_errors=True)

    with (DOCS_HOME_PATH / "template" / "page.txt").open(encoding="utf-8") as f:
        page_template = f.read()

    with (DOCS_HOME_PATH / "template" / "toctree.txt").open(encoding="utf-8") as f:
        toctree = f.read()

    generate(TYPES_PATH, TYPES_BASE)
    generate(FUNCTIONS_PATH, FUNCTIONS_BASE)
    generate(BASE_PATH, BASE_BASE)
    hydrogram_api()


if __name__ == "__main__":
    start()
