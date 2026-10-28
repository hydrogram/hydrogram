# Hydrogram - Telegram MTProto API Client Library for Python
# Copyright (C) 2023-present Hydrogram <https://hydrogram.org>
#
# This file is part of Hydrogram.
#
# Hydrogram is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hydrogram is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hydrogram.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import annotations

import ast
import importlib
import inspect
import re
import struct
from io import BytesIO
from pathlib import Path

import pytest

from compiler.api import compiler
from dev_tools import check_api_schema_updates as updater
from hydrogram import errors, raw
from hydrogram.raw.core import TLObject

ROOT = Path(__file__).resolve().parents[1]


def schema_cases():
    cases = []
    section = None
    for path in (ROOT / "compiler/api/source").glob("*.tl"):
        for line in path.read_text().splitlines():
            if match := compiler.SECTION_RE.match(line):
                section = match[1]
            if match := compiler.COMBINATOR_RE.match(line):
                name, constructor_id, _ = match.groups()
                namespace, _, name = name.rpartition(".")
                qualname = ".".join(filter(None, [namespace, compiler.camel(name)]))
                cases.append((f"{section}.{qualname}", int(constructor_id, 16), line))
    return cases


def field_value(tl_type):
    tl_type = tl_type.split("?")[-1]
    if tl_type in {"int", "long", "int128", "int256"}:
        return 42
    if tl_type == "double":
        return 1.25
    if tl_type == "string":
        return "Hydrogram 🌊"
    if tl_type == "bytes":
        return b"\x00\xffpayload"
    if tl_type in {"Bool", "true"}:
        return True
    if "vector" in tl_type.lower():
        return [field_value(tl_type.split("<", 1)[1][:-1])]
    # TLObject dispatch is polymorphic. Exercise a nested boxed value without
    # recursively constructing potentially cyclic application object graphs.
    return raw.types.InputPeerSelf()


@pytest.mark.parametrize(("qualname", "constructor_id", "line"), schema_cases())
@pytest.mark.parametrize("with_optional", [False, True])
def test_every_generated_declaration_roundtrips(qualname, constructor_id, line, with_optional):
    namespace, _, name = qualname.rpartition(".")
    cls = getattr(importlib.import_module("hydrogram.raw." + namespace), name)
    kwargs = {}
    for arg_name, tl_type in compiler.ARGS_RE.findall(line):
        if tl_type == "#" or ("?" in tl_type and not with_optional):
            continue
        arg_name = {"self": "is_self", "from": "from_peer"}.get(arg_name, arg_name)
        kwargs[arg_name] = field_value(tl_type)
    value = cls(**kwargs)
    payload = value.write()
    assert int.from_bytes(payload[:4], "little") == constructor_id == cls.ID
    stream = BytesIO(payload)
    parsed = TLObject.read(stream)
    assert type(parsed) is cls
    assert stream.read() == b""
    assert parsed.write() == payload


def test_optional_empty_vector_keeps_its_flag_and_stream_alignment():
    value = raw.types.InputMediaPoll(
        poll=raw.types.Poll(
            id=1,
            hash=0,
            question=raw.types.TextWithEntities(text="Quiz?", entities=[]),
            answers=[],
        ),
        correct_answers=[0],
        solution="Explanation",
        solution_entities=[],
    )
    stream = BytesIO(value.write() + raw.types.PeerUser(user_id=123).write())
    parsed = TLObject.read(stream)
    assert parsed.solution_entities == []
    assert parsed.correct_answers == [0]
    assert TLObject.read(stream).user_id == 123
    assert stream.read() == b""


def test_pinned_schema_provenance():
    updater.check_provenance(ROOT)
    assert raw.all.layer == updater.get_layer((ROOT / updater.SCHEMA_PATH).read_text())


def test_handwritten_raw_references_and_call_signatures():
    # These stale references predate this update (already absent in layer 223).
    # Keep the baseline explicit so future updates cannot silently add regressions.
    known_missing = {
        "raw.types.Wallpaper": {"hydrogram/types/user_and_chats/chat_background.py"},
        "raw.functions.channels.EditForumTopic": {
            f"hydrogram/methods/chats/{module}.py"
            for module in (
                "close_forum_topic",
                "close_general_topic",
                "edit_forum_topic",
                "edit_general_topic",
                "hide_general_topic",
                "reopen_forum_topic",
                "reopen_general_topic",
                "unhide_general_topic",
            )
        },
        **{
            f"raw.functions.channels.{name}": {f"hydrogram/methods/chats/{module}.py"}
            for name, module in (
                ("CreateForumTopic", "create_forum_topic"),
                ("DeleteTopicHistory", "delete_forum_topic"),
                ("GetForumTopics", "get_forum_topics"),
                ("GetForumTopicsByID", "get_forum_topics_by_id"),
                ("EditCreator", "transfer_chat_ownership"),
            )
        },
    }
    failures = []
    for path in (ROOT / "hydrogram").rglob("*.py"):
        if "raw" in path.relative_to(ROOT / "hydrogram").parts:
            continue
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute):
                continue
            # Inspect only the outermost raw.types/functions/base attribute.
            dotted = ast.unparse(node)
            if not re.fullmatch(r"raw\.(?:types|functions|base)\.[\w.]+", dotted):
                continue
            obj = raw
            try:
                for part in dotted.split(".")[1:]:
                    obj = getattr(obj, part)
            except AttributeError:
                if path.relative_to(ROOT).as_posix() not in known_missing.get(dotted, set()):
                    failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: missing {dotted}")
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            dotted = ast.unparse(node.func)
            if not re.fullmatch(r"raw\.(?:types|functions)\.[\w.]+", dotted):
                continue
            obj = raw
            for part in dotted.split(".")[1:]:
                obj = getattr(obj, part, None)
            if (
                obj is None
                or not inspect.isclass(obj)
                or any(k.arg is None for k in node.keywords)
            ):
                continue
            try:
                inspect.signature(obj).bind(
                    *[None for _ in node.args], **{k.arg: None for k in node.keywords}
                )
            except TypeError as error:
                failures.append(f"{path.relative_to(ROOT)}:{node.lineno}: {dotted}: {error}")
    assert not failures, "\n".join(failures)


@pytest.mark.parametrize(
    ("code", "name", "exception"),
    [
        (400, "REVOTE_NOT_ALLOWED", "RevoteNotAllowed"),
        (406, "POLL_COUNTRY_RESTRICTED", "PollCountryRestricted"),
        (406, "POLL_MEMBER_RESTRICTED", "PollMemberRestricted"),
    ],
)
def test_poll_rpc_errors(code, name, exception):
    with pytest.raises(getattr(errors, exception)):
        errors.RPCError.raise_it(
            raw.types.RpcError(error_code=code, error_message=name),
            raw.functions.messages.SendVote,
        )


def test_generated_registry_covers_every_schema_declaration():
    expected = {}
    for path in (ROOT / "compiler/api/source").glob("*.tl"):
        for name, declaration in updater.definitions(path.read_text()).items():
            constructor_id = int(declaration.split("#", 1)[1].split()[0], 16)
            expected[constructor_id] = name
    assert expected.keys() <= raw.all.objects.keys()


@pytest.mark.parametrize(
    "declaration",
    [
        "unsupported syntax;",
        "example#1234 data:Vector<Vector<int>> = Example;",
        "example#1234 data:flags10.0?int = Example;",
        "example#1234 data:unknown$syntax = Example;",
    ],
)
def test_compiler_rejects_unsupported_syntax(declaration):
    with pytest.raises(ValueError, match="Unsupported"):
        compiler.validate_schema(["---types---", declaration])


def test_transport_config_bare_vectors_match_wire_format():
    value = raw.types.help.ConfigSimple(
        date=1,
        expires=2,
        rules=[
            raw.types.AccessPointRule(
                phone_prefix_rules="",
                dc_id=2,
                ips=[raw.types.IpPort(ipv4=0x7F000001, port=443)],
            )
        ],
    )
    expected = (
        struct.pack("<Iiii", 0x5A592A6C, 1, 2, 1)
        + struct.pack("<I", 0x4679B65F)
        + bytes(4)
        + struct.pack("<iiIii", 2, 1, 0xD433AD73, 0x7F000001, 443)
    )
    assert value.write() == expected
    stream = BytesIO(expected)
    parsed = TLObject.read(stream)
    assert parsed.rules[0].ips[0].port == 443
    assert stream.read() == b""
