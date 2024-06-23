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

import csv
import os
import re
import shutil
from pathlib import Path

ERRORS_HOME_PATH = Path(__file__).parent.resolve()
REPO_HOME_PATH = ERRORS_HOME_PATH.parent.parent

ERRORS_DEST_PATH = REPO_HOME_PATH / "hydrogram" / "errors" / "exceptions"
NOTICE_PATH = REPO_HOME_PATH / "NOTICE"


def snake(s):
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def camel(s):
    s = snake(s).split("_")
    return "".join(str(i.title()) for i in s)


def start():
    shutil.rmtree(ERRORS_DEST_PATH, ignore_errors=True)
    ERRORS_DEST_PATH.mkdir(parents=True)

    files = os.listdir(f"{ERRORS_HOME_PATH}/source")

    with NOTICE_PATH.open(encoding="utf-8") as f:
        notice = [f"# {line}".strip() for line in f]
        notice = "\n".join(notice)

    with (ERRORS_DEST_PATH / "all.py").open("w", encoding="utf-8") as f_all:
        f_all.write(notice + "\n\n")
        f_all.write("count = {count}\n\n")
        f_all.write("exceptions = {\n")

        count = 0

        for i in files:
            code, name = re.search(r"(\d+)_([A-Z_]+)", i).groups()

            f_all.write(f"    {code}: {{\n")

            init = ERRORS_DEST_PATH / "__init__.py"

            if not init.exists():
                with init.open("w", encoding="utf-8") as f_init:
                    f_init.write(notice + "\n\n")

            with init.open("a", encoding="utf-8") as f_init:
                f_init.write(f"from .{name.lower()}_{code} import *\n")

            with (
                (ERRORS_HOME_PATH / "source" / i).open(encoding="utf-8") as f_csv,
                (ERRORS_DEST_PATH / f"{name.lower()}_{code}.py").open(
                    "w", encoding="utf-8"
                ) as f_class,
            ):
                reader = csv.reader(f_csv, delimiter="\t")

                super_class = camel(name)
                name = " ".join([
                    i.capitalize() for i in re.sub(r"_", " ", name).lower().split(" ")
                ])

                sub_classes = []

                f_all.write(f'        "_": "{super_class}",\n')

                for j, row in enumerate(reader):
                    if j == 0:
                        continue

                    count += 1

                    if not row:  # Row is empty (blank line)
                        continue

                    error_id, error_message = row

                    sub_class = camel(re.sub(r"_X", "_", error_id))
                    sub_class = re.sub(r"^2", "Two", sub_class)
                    sub_class = re.sub(r" ", "", sub_class)

                    f_all.write(f'        "{error_id}": "{sub_class}",\n')

                    sub_classes.append((sub_class, error_id, error_message))

                with (ERRORS_HOME_PATH / "template" / "class.txt").open(
                    encoding="utf-8"
                ) as f_class_template:
                    class_template = f_class_template.read()

                    with (ERRORS_HOME_PATH / "template" / "sub_class.txt").open(
                        encoding="utf-8"
                    ) as f_sub_class_template:
                        sub_class_template = f_sub_class_template.read()

                    class_template = class_template.format(
                        notice=notice,
                        super_class=super_class,
                        code=code,
                        docstring=f'"""{name}"""',
                        sub_classes="".join([
                            sub_class_template.format(
                                sub_class=k[0],
                                super_class=super_class,
                                id=f'"{k[1]}"',
                                docstring=f'"""{k[2]}"""',
                            )
                            for k in sub_classes
                        ]),
                    )

                f_class.write(class_template)

            f_all.write("    },\n")

        f_all.write("}\n")

    with (ERRORS_DEST_PATH / "all.py").open(encoding="utf-8") as f:
        content = f.read()

    with (ERRORS_DEST_PATH / "all.py").open("w", encoding="utf-8") as f:
        f.write(re.sub("{count}", str(count), content))  # noqa: RUF027


if __name__ == "__main__":
    start()
