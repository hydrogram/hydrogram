#  Hydrogram - Telegram MTProto API Client Library for Python
#  Copyright (C) 2017-2023 Dan <https://github.com/delivrance>
#  Copyright (C) 2023-present Amano LLC <https://amanoteam.com>
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

HOME = "compiler/errors"
DEST = "hydrogram/errors/exceptions"
NOTICE_PATH = "NOTICE"


def snek(s):
    # https://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-snake-case
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s).lower()


def caml(s):
    s = snek(s).split("_")
    return "".join([str(i.title()) for i in s])


def start():
    shutil.rmtree(DEST, ignore_errors=True)
    Path(DEST).mkdir(parents=True)

    files = os.listdir(f"{HOME}/source")

    with Path(NOTICE_PATH).open(encoding="utf-8") as f:
        notice = [f"# {line}".strip() for line in f]
        notice = "\n".join(notice)

    with Path(f"{DEST}/all.py").open("w", encoding="utf-8") as f_all:
        f_all.write(notice + "\n\n")
        f_all.write("count = {count}\n\n")
        f_all.write("exceptions = {\n")

        count = 0

        for i in files:
            code, name = re.search(r"(\d+)_([A-Z_]+)", i).groups()

            f_all.write(f"    {code}: {{\n")

            init = f"{DEST}/__init__.py"

            if not Path(init).exists():
                with Path(init).open("w", encoding="utf-8") as f_init:
                    f_init.write(notice + "\n\n")

            with Path(init).open("a", encoding="utf-8") as f_init:
                f_init.write(f"from .{name.lower()}_{code} import *\n")

            with Path(f"{HOME}/source/{i}").open(encoding="utf-8") as f_csv, Path(
                f"{DEST}/{name.lower()}_{code}.py"
            ).open("w", encoding="utf-8") as f_class:
                reader = csv.reader(f_csv, delimiter="\t")

                super_class = caml(name)
                name = " ".join(
                    [str(i.capitalize()) for i in re.sub(r"_", " ", name).lower().split(" ")]
                )

                sub_classes = []

                f_all.write(f'        "_": "{super_class}",\n')

                for j, row in enumerate(reader):
                    if j == 0:
                        continue

                    count += 1

                    if not row:  # Row is empty (blank line)
                        continue

                    error_id, error_message = row

                    sub_class = caml(re.sub(r"_X", "_", error_id))
                    sub_class = re.sub(r"^2", "Two", sub_class)
                    sub_class = re.sub(r" ", "", sub_class)

                    f_all.write(f'        "{error_id}": "{sub_class}",\n')

                    sub_classes.append((sub_class, error_id, error_message))

                with Path(f"{HOME}/template/class.txt").open(encoding="utf-8") as f_class_template:
                    class_template = f_class_template.read()

                    with Path(f"{HOME}/template/sub_class.txt").open(
                        encoding="utf-8"
                    ) as f_sub_class_template:
                        sub_class_template = f_sub_class_template.read()

                    class_template = class_template.format(
                        notice=notice,
                        super_class=super_class,
                        code=code,
                        docstring=f'"""{name}"""',
                        sub_classes="".join(
                            [
                                sub_class_template.format(
                                    sub_class=k[0],
                                    super_class=super_class,
                                    id=f'"{k[1]}"',
                                    docstring=f'"""{k[2]}"""',
                                )
                                for k in sub_classes
                            ]
                        ),
                    )

                f_class.write(class_template)

            f_all.write("    },\n")

        f_all.write("}\n")

    with Path(f"{DEST}/all.py").open(encoding="utf-8") as f:
        content = f.read()

    with Path(f"{DEST}/all.py").open("w", encoding="utf-8") as f:
        f.write(re.sub("{count}", str(count), content))


if __name__ == "__main__":
    HOME = "."
    DEST = "../../hydrogram/errors/exceptions"
    NOTICE_PATH = "../../NOTICE"

    start()
