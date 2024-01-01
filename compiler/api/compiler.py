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

import contextlib
import json
import re
import shutil
from functools import partial
from pathlib import Path
from typing import NamedTuple

# from autoflake import fix_code
# from black import format_str, FileMode

HOME_PATH = Path("compiler/api")
DESTINATION_PATH = Path("hydrogram/raw")
NOTICE_PATH = "NOTICE"

SECTION_RE = re.compile(r"---(\w+)---")
LAYER_RE = re.compile(r"//\sLAYER\s(\d+)")
COMBINATOR_RE = re.compile(r"^([\w.]+)#([0-9a-f]+)\s(?:.*)=\s([\w<>.]+);$", re.MULTILINE)
ARGS_RE = re.compile(r"[^{](\w+):([\w?!.<>#]+)")
FLAGS_RE = re.compile(r"flags(\d?)\.(\d+)\?")
FLAGS_RE_2 = re.compile(r"flags(\d?)\.(\d+)\?([\w<>.]+)")
FLAGS_RE_3 = re.compile(r"flags(\d?):#")
INT_RE = re.compile(r"int(\d+)")

CORE_TYPES = [
    "int",
    "long",
    "int128",
    "int256",
    "double",
    "bytes",
    "string",
    "Bool",
    "true",
]

WARNING = """
# # # # # # # # # # # # # # # # # # # # # # # #
#               !!! WARNING !!!               #
#          This is a generated file!          #
# All changes made in this file will be lost! #
# # # # # # # # # # # # # # # # # # # # # # # #
""".strip()

open = partial(open, encoding="utf-8")

types_to_constructors = {}
types_to_functions = {}
constructors_to_functions = {}
namespaces_to_types = {}
namespaces_to_constructors = {}
namespaces_to_functions = {}

try:
    with open("docs.json") as f:
        docs = json.load(f)
except FileNotFoundError:
    docs = {"type": {}, "constructor": {}, "method": {}}


class Combinator(NamedTuple):
    section: str
    qualname: str
    namespace: str
    name: str
    id: str
    has_flags: bool
    args: list[tuple[str, str]]
    qualtype: str
    typespace: str
    type: str


def snake(s: str):
    # https://stackoverflow.com/q/1175208
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def camel(s: str):
    return "".join([i[0].upper() + i[1:] for i in s.split("_")])


def get_type_hint(type: str) -> str:
    is_flag = FLAGS_RE.match(type)
    is_core = False

    if is_flag:
        type = type.split("?")[1]

    if type in CORE_TYPES:
        is_core = True

        if type == "long" or "int" in type:
            type = "int"
        elif type == "double":
            type = "float"
        elif type == "string":
            type = "str"
        elif type in {"Bool", "true"}:
            type = "bool"
        else:  # bytes and object
            type = "bytes"

    if type in {"Object", "!X"}:
        return "TLObject"

    if re.match("^vector", type, re.I):
        is_core = True

        sub_type = type.split("<")[1][:-1]
        type = f"List[{get_type_hint(sub_type)}]"

    if is_core:
        return f"Optional[{type}] = None" if is_flag else type
    ns, name = type.split(".") if "." in type else ("", type)
    type = '"raw.base.' + ".".join([ns, name]).strip(".") + '"'

    return f'{type}{" = None" if is_flag else ""}'


def sort_args(args):
    """Put flags at the end"""
    args = args.copy()
    flags = [i for i in args if FLAGS_RE.match(i[1])]

    for i in flags:
        args.remove(i)

    for i in args[:]:
        if re.match(r"flags\d?", i[0]) and i[1] == "#":
            args.remove(i)

    return args + flags


def remove_whitespaces(source: str) -> str:
    """Remove whitespaces from blank lines"""
    lines = source.split("\n")

    for i, _ in enumerate(lines):
        if re.match(r"^\s+$", lines[i]):
            lines[i] = ""

    return "\n".join(lines)


def get_docstring_arg_type(t: str):
    if t in CORE_TYPES:
        if t == "long":
            return "``int`` ``64-bit``"
        if "int" in t:
            size = INT_RE.match(t)
            return f"``int`` ``{size.group(1)}-bit``" if size else "``int`` ``32-bit``"
        if t == "double":
            return "``float`` ``64-bit``"
        if t == "string":
            return "``str``"
        if t == "true":
            return "``bool``"
        return f"``{t.lower()}``"
    if t in {"TLObject", "X"}:
        return "Any object from :obj:`~hydrogram.raw.types`"
    if t == "!X":
        return "Any function from :obj:`~hydrogram.raw.functions`"
    if t.lower().startswith("vector"):
        return "List of " + get_docstring_arg_type(t.split("<", 1)[1][:-1])
    return f":obj:`{t} <hydrogram.raw.base.{t}>`"


def get_references(t: str, kind: str):
    if kind == "constructors":
        t = constructors_to_functions.get(t)
    elif kind == "types":
        t = types_to_functions.get(t)
    else:
        raise ValueError("Invalid kind")

    return ("\n            ".join(t), len(t)) if t else (None, 0)


def start(format: bool = False):
    shutil.rmtree(DESTINATION_PATH / "types", ignore_errors=True)
    shutil.rmtree(DESTINATION_PATH / "functions", ignore_errors=True)
    shutil.rmtree(DESTINATION_PATH / "base", ignore_errors=True)

    with open(HOME_PATH / "source/auth_key.tl") as f1, open(
        HOME_PATH / "source/sys_msgs.tl"
    ) as f2, open(HOME_PATH / "source/main_api.tl") as f3:
        schema = (f1.read() + f2.read() + f3.read()).splitlines()

    with open(HOME_PATH / "template/type.txt") as f1, open(
        HOME_PATH / "template/combinator.txt"
    ) as f2:
        type_tmpl = f1.read()
        combinator_tmpl = f2.read()

    with open(NOTICE_PATH, encoding="utf-8") as f:
        notice = [f"#  {line}".strip() for line in f]
        notice = "\n".join(notice)

    layer = None
    combinators = []

    section = None
    for line in schema:
        if section_match := SECTION_RE.match(line):
            section = section_match.group(1)
            continue

        if layer_match := LAYER_RE.match(line):
            layer = layer_match.group(1)
            continue

        if combinator_match := COMBINATOR_RE.match(line):
            qualname, id, qualtype = combinator_match.groups()

            namespace, name = qualname.split(".") if "." in qualname else ("", qualname)
            name = camel(name)
            qualname = ".".join([namespace, name]).lstrip(".")

            typespace, type = qualtype.split(".") if "." in qualtype else ("", qualtype)
            type = camel(type)
            qualtype = ".".join([typespace, type]).lstrip(".")

            has_flags = bool(FLAGS_RE_3.findall(line))

            args = ARGS_RE.findall(line)

            # Fix arg name being "self" or "from" (reserved python keywords)
            for i, item in enumerate(args):
                if item[0] == "self":
                    args[i] = ("is_self", item[1])
                if item[0] == "from":
                    args[i] = ("from_peer", item[1])

            combinator = Combinator(
                section=section,
                qualname=qualname,
                namespace=namespace,
                name=name,
                id=f"0x{id}",
                has_flags=has_flags,
                args=args,
                qualtype=qualtype,
                typespace=typespace,
                type=type,
            )

            combinators.append(combinator)

    for c in combinators:
        qualtype = c.qualtype

        if qualtype.startswith("Vector"):
            qualtype = qualtype.split("<")[1][:-1]

        d = types_to_constructors if c.section == "types" else types_to_functions

        if qualtype not in d:
            d[qualtype] = []

        d[qualtype].append(c.qualname)

        if c.section == "types":
            key = c.namespace

            if key not in namespaces_to_types:
                namespaces_to_types[key] = []

            if c.type not in namespaces_to_types[key]:
                namespaces_to_types[key].append(c.type)

    for k, v in types_to_constructors.items():
        for i in v:
            with contextlib.suppress(KeyError):
                constructors_to_functions[i] = types_to_functions[k]

    # import json
    # print(json.dumps(namespaces_to_types, indent=2))

    for qualtype in types_to_constructors:
        typespace, type = qualtype.split(".") if "." in qualtype else ("", qualtype)
        dir_path = DESTINATION_PATH / "base" / typespace

        module = type

        if module == "Updates":
            module = "UpdatesT"

        Path(dir_path).mkdir(parents=True, exist_ok=True)

        constructors = sorted(types_to_constructors[qualtype])
        constr_count = len(constructors)
        items = "\n            ".join([f"{c}" for c in constructors])

        type_docs = docs["type"].get(qualtype, None)

        type_docs = type_docs["desc"] if type_docs else "Telegram API base type."

        docstring = type_docs

        docstring += (
            f"\n\n    Constructors:\n"
            f"        This base type has {constr_count} constructor{'s' if constr_count > 1 else ''} available.\n\n"
            f"        .. currentmodule:: hydrogram.raw.types\n\n"
            f"        .. autosummary::\n"
            f"            :nosignatures:\n\n"
            f"            {items}"
        )

        references, ref_count = get_references(qualtype, "types")

        if references:
            docstring += f"\n\n    Functions:\n        This object can be returned by {ref_count} function{'s' if ref_count > 1 else ''}.\n\n        .. currentmodule:: hydrogram.raw.functions\n\n        .. autosummary::\n            :nosignatures:\n\n            {references}"

        with open(dir_path / f"{snake(module)}.py", "w") as f:
            f.write(
                type_tmpl.format(
                    notice=notice,
                    warning=WARNING,
                    docstring=docstring,
                    name=type,
                    qualname=qualtype,
                    types=", ".join([f'"raw.types.{c}"' for c in constructors]),
                    doc_name=snake(type).replace("_", "-"),
                )
            )

    for c in combinators:
        sorted_args = sort_args(c.args)

        arguments = (", *, " if c.args else "") + (
            ", ".join([f"{i[0]}: {get_type_hint(i[1])}" for i in sorted_args])
            if sorted_args
            else ""
        )

        fields = (
            "\n        ".join([f"self.{i[0]} = {i[0]}  # {i[1]}" for i in sorted_args])
            if sorted_args
            else "pass"
        )

        docstring = ""
        docstring_args = []

        combinator_docs = docs["method"] if c.section == "functions" else docs["constructor"]

        for arg in sorted_args:
            arg_name, arg_type = arg
            is_optional = FLAGS_RE.match(arg_type)
            arg_type = arg_type.split("?")[-1]

            arg_docs = combinator_docs.get(c.qualname, None)

            arg_docs = arg_docs["params"].get(arg_name, "N/A") if arg_docs else "N/A"

            docstring_args.append(
                f'{arg_name} ({get_docstring_arg_type(arg_type)}{", *optional*" if is_optional else ""}):\n            {arg_docs}\n'
            )

        if c.section == "types":
            constructor_docs = docs["constructor"].get(c.qualname, None)

            constructor_docs = (
                constructor_docs["desc"] if constructor_docs else "Telegram API type."
            )
            docstring += constructor_docs + "\n"
            docstring += f"\n    Constructor of :obj:`~hydrogram.raw.base.{c.qualtype}`."
        elif function_docs := docs["method"].get(c.qualname, None):
            docstring += function_docs["desc"] + "\n"
        else:
            docstring += "Telegram API function."

        docstring += f"\n\n    Details:\n        - Layer: ``{layer}``\n        - ID: ``{c.id[2:].upper()}``\n\n"
        docstring += "    Parameters:\n        " + (
            "\n        ".join(docstring_args) if docstring_args else "No parameters required.\n"
        )

        if c.section == "functions":
            docstring += "\n    Returns:\n        " + get_docstring_arg_type(c.qualtype)
        else:
            references, count = get_references(c.qualname, "constructors")

            if references:
                docstring += f"\n    Functions:\n        This object can be returned by {count} function{'s' if count > 1 else ''}.\n\n        .. currentmodule:: hydrogram.raw.functions\n\n        .. autosummary::\n            :nosignatures:\n\n            {references}"

        write_types = read_types = "" if c.has_flags else "# No flags\n        "

        for arg_name, arg_type in c.args:
            flag = FLAGS_RE_2.match(arg_type)

            if re.match(r"flags\d?", arg_name) and arg_type == "#":
                write_flags = []

                for i in c.args:
                    flag = FLAGS_RE_2.match(i[1])

                    if flag:
                        if arg_name != f"flags{flag.group(1)}":
                            continue

                        if flag.group(3) == "true" or flag.group(3).startswith("Vector"):
                            write_flags.append(
                                f"{arg_name} |= (1 << {flag.group(2)}) if self.{i[0]} else 0"
                            )
                        else:
                            write_flags.append(
                                f"{arg_name} |= (1 << {flag.group(2)}) if self.{i[0]} is not None else 0"
                            )

                write_flags = "\n        ".join([
                    f"{arg_name} = 0",
                    "\n        ".join(write_flags),
                    f"b.write(Int({arg_name}))\n        ",
                ])

                write_types += write_flags
                read_types += f"\n        {arg_name} = Int.read(b)\n        "

                continue

            if flag:
                number, index, flag_type = flag.groups()

                if flag_type == "true":
                    read_types += "\n        "
                    read_types += f"{arg_name} = True if flags{number} & (1 << {index}) else False"
                elif flag_type in CORE_TYPES:
                    write_types += "\n        "
                    write_types += f"if self.{arg_name} is not None:\n            "
                    write_types += f"b.write({flag_type.title()}(self.{arg_name}))\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = {flag_type.title()}.read(b) if flags{number} & (1 << {index}) else None"
                elif "vector" in flag_type.lower():
                    sub_type = arg_type.split("<")[1][:-1]

                    write_types += "\n        "
                    write_types += f"if self.{arg_name} is not None:\n            "
                    write_types += f'b.write(Vector(self.{arg_name}{f", {sub_type.title()}" if sub_type in CORE_TYPES else ""}))\n        '

                    read_types += "\n        "
                    read_types += f'{arg_name} = TLObject.read(b{f", {sub_type.title()}" if sub_type in CORE_TYPES else ""}) if flags{number} & (1 << {index}) else []\n        '
                else:
                    write_types += "\n        "
                    write_types += f"if self.{arg_name} is not None:\n            "
                    write_types += f"b.write(self.{arg_name}.write())\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = TLObject.read(b) if flags{number} & (1 << {index}) else None\n        "
            else:
                write_types += "\n        "
                if arg_type in CORE_TYPES:
                    write_types += f"b.write({arg_type.title()}(self.{arg_name}))\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = {arg_type.title()}.read(b)\n        "
                elif "vector" in arg_type.lower():
                    sub_type = arg_type.split("<")[1][:-1]

                    write_types += f'b.write(Vector(self.{arg_name}{f", {sub_type.title()}" if sub_type in CORE_TYPES else ""}))\n        '

                    read_types += "\n        "
                    read_types += f'{arg_name} = TLObject.read(b{f", {sub_type.title()}" if sub_type in CORE_TYPES else ""})\n        '
                else:
                    write_types += f"b.write(self.{arg_name}.write())\n        "

                    read_types += "\n        "
                    read_types += f"{arg_name} = TLObject.read(b)\n        "

        slots = ", ".join([f'"{i[0]}"' for i in sorted_args])
        return_arguments = ", ".join([f"{i[0]}={i[0]}" for i in sorted_args])

        compiled_combinator = combinator_tmpl.format(
            notice=notice,
            warning=WARNING,
            name=c.name,
            docstring=docstring,
            slots=slots,
            id=c.id,
            qualname=f"{c.section}.{c.qualname}",
            arguments=arguments,
            fields=fields,
            read_types=read_types,
            write_types=write_types,
            return_arguments=return_arguments,
        )

        directory = "types" if c.section == "types" else c.section

        dir_path = DESTINATION_PATH / directory / c.namespace

        Path(dir_path).mkdir(exist_ok=True, parents=True)

        module = c.name

        if module == "Updates":
            module = "UpdatesT"

        with open(dir_path / f"{snake(module)}.py", "w") as f:
            f.write(compiled_combinator)

        d = namespaces_to_constructors if c.section == "types" else namespaces_to_functions

        if c.namespace not in d:
            d[c.namespace] = []

        d[c.namespace].append(c.name)

    for namespace, types in namespaces_to_types.items():
        with open(DESTINATION_PATH / "base" / namespace / "__init__.py", "w") as f:
            f.write(f"{notice}\n\n")
            f.write(f"{WARNING}\n\n")

            for t in types:
                module = t

                if module == "Updates":
                    module = "UpdatesT"

                f.write(f"from .{snake(module)} import {t}\n")

            if not namespace:
                f.write(f"from . import {', '.join(filter(bool, namespaces_to_types))}")

    for namespace, types in namespaces_to_constructors.items():
        with open(DESTINATION_PATH / "types" / namespace / "__init__.py", "w") as f:
            f.write(f"{notice}\n\n")
            f.write(f"{WARNING}\n\n")

            for t in types:
                module = t

                if module == "Updates":
                    module = "UpdatesT"

                f.write(f"from .{snake(module)} import {t}\n")

            if not namespace:
                f.write(f"from . import {', '.join(filter(bool, namespaces_to_constructors))}\n")

    for namespace, types in namespaces_to_functions.items():
        with open(DESTINATION_PATH / "functions" / namespace / "__init__.py", "w") as f:
            f.write(f"{notice}\n\n")
            f.write(f"{WARNING}\n\n")

            for t in types:
                module = t

                if module == "Updates":
                    module = "UpdatesT"

                f.write(f"from .{snake(module)} import {t}\n")

            if not namespace:
                f.write(f"from . import {', '.join(filter(bool, namespaces_to_functions))}")

    with open(DESTINATION_PATH / "all.py", "w", encoding="utf-8") as f:
        f.write(notice + "\n\n")
        f.write(WARNING + "\n\n")
        f.write(f"layer = {layer}\n\n")
        f.write("objects = {")

        for c in combinators:
            f.write(f'\n    {c.id}: "hydrogram.raw.{c.section}.{c.qualname}",')

        f.write('\n    0xbc799737: "hydrogram.raw.core.BoolFalse",')
        f.write('\n    0x997275b5: "hydrogram.raw.core.BoolTrue",')
        f.write('\n    0x1cb5c415: "hydrogram.raw.core.Vector",')
        f.write('\n    0x73f1f8dc: "hydrogram.raw.core.MsgContainer",')
        f.write('\n    0xae500895: "hydrogram.raw.core.FutureSalts",')
        f.write('\n    0x0949d9dc: "hydrogram.raw.core.FutureSalt",')
        f.write('\n    0x3072cfa1: "hydrogram.raw.core.GzipPacked",')
        f.write('\n    0x5bb8e511: "hydrogram.raw.core.Message",')

        f.write("\n}\n")


if __name__ == "__main__":
    HOME_PATH = Path()
    DESTINATION_PATH = Path("../../hydrogram/raw")
    NOTICE_PATH = Path("../../NOTICE")

    start(format=False)
