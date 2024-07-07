#!/bin/env python
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

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import httpx
from lxml import html

ROOT_DIR = Path.cwd().absolute()
if ROOT_DIR.name == "dev_tools":
    ROOT_DIR = ROOT_DIR.parent


SECTION_RE = re.compile(r"---(\w+)---")
COMBINATOR_RE = re.compile(r"^([\w.]+)#([0-9a-f]+)\s(?:.*)=\s([\w<>.]+);$", re.MULTILINE)


BASE_URL = "https://corefork.telegram.org/"


MAX_TASKS = 10


sem = asyncio.Semaphore(MAX_TASKS)


client = httpx.AsyncClient()


async def main():
    tl_data = parse_tl_file(ROOT_DIR / "compiler" / "api" / "source" / "main_api.tl")

    it_count = len(tl_data["constructor"]) + len(tl_data["method"]) + len(tl_data["type"])

    print(f"Getting {it_count} objects from {BASE_URL}…")

    doc_dict = {"type": {}, "constructor": {}, "method": {}}

    tasks = []

    it_count_done = 0

    for it_type, items in tl_data.items():
        for it_name in items:
            it_count_done += 1
            print(f"Parsing items {it_count_done}/{it_count}", end="\r", flush=True)
            await sem.acquire()
            tasks.append(asyncio.create_task(get_object_data(it_type, it_name, doc_dict)))

    # Be sure that all tasks are done before continuing
    for task in tasks:
        await task

    await client.aclose()

    json.dump(
        doc_dict, (ROOT_DIR / "compiler" / "api" / "docs.json").open("w"), indent=2, sort_keys=True
    )
    print("\nDone!")


async def get_object_data(it_type: str, it_name: str, doc_dict: dict[str, dict]):
    try:
        request = await client.get(f"{BASE_URL}{it_type}/{it_name}")
        if request.status_code != 200:
            print(f"Error {request.status_code} for {it_type}/{it_name}\n")
            return

        tree = html.fromstring(request.text)

        page_content_xp = tree.xpath("//div[@id='dev_page_content'][1]")
        if not page_content_xp:
            print(f"No page content for {it_type}/{it_name}")
            return

        page_content = page_content_xp[0]

        # Get the description of the object - always used
        desc_xp = page_content.xpath("./p[1]")

        if desc_xp:
            desc = desc_xp[0].text_content().strip()
        else:
            print(f"No description for {it_type}/{it_name}")
            desc = ""

        if it_type == "type":
            doc_dict["type"][it_name] = {"desc": desc}
        elif it_type in {"constructor", "method"}:
            params_link_xp = page_content.xpath("./h3/a[@id='parameters'][1]")
            if params_link_xp:
                params_xp = params_link_xp[0].getparent().getnext().xpath("./tbody[1]")
                if params_xp:
                    params = {
                        x.getchildren()[0].text_content().strip(): x.getchildren()[2]
                        .text_content()
                        .strip()
                        for x in params_xp[0].xpath("./tr")
                    }
                else:
                    print(f"No parameters for {it_type}/{it_name}")
                    params = {}
            else:
                print(f"No parameters section for {it_type}/{it_name}")
                params = {}

            doc_dict[it_type][it_name] = {"desc": desc, "params": params}
        else:
            raise ValueError(f"Unknown type {it_type}")
    finally:
        sem.release()


def devectorize(ttype: str) -> str:
    ivec = ttype.find("Vector<")
    if ivec != -1:
        return ttype[7:-1]

    return ttype


def adjust_name(qualname: str) -> str:
    names = qualname.split(".")

    if len(names) == 2:
        name = names[1][:1].upper() + names[1][1:]
        return ".".join([names[0], name])

    return qualname[:1].upper() + qualname[1:]


def parse_tl_file(file_path: Path) -> dict[str, list[str]]:
    lines = file_path.read_text().splitlines()

    section = None

    types = set()
    constructors = set()
    methods = set()

    for line in lines:
        if section_match := SECTION_RE.match(line):
            section = section_match.group(1)
            continue

        if combinator_match := COMBINATOR_RE.match(line):
            qualname, _id, qualtype = combinator_match.groups()

            qualtype = devectorize(qualtype)

            if section == "types":
                types.add(qualtype)
                constructors.add(adjust_name(qualname))
                pass
            elif section == "functions":
                types.add(qualtype)
                methods.add(adjust_name(qualname))

    return {
        "type": sorted(types),
        "constructor": sorted(constructors),
        "method": sorted(methods),
    }


if __name__ == "__main__":
    asyncio.run(main())
