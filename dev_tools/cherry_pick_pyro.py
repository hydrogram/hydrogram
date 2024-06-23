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

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
from git import Repo, exc

# Config variables
ORIGIN_REPO = "pyrogram/pyrogram"
ORIGIN_BRANCH = "master"

HYDRO_ROOT_DIR = Path.cwd().absolute()
if HYDRO_ROOT_DIR.name == "dev_tools":
    HYDRO_ROOT_DIR = HYDRO_ROOT_DIR.parent

PATCH_DIR = Path(tempfile.mkdtemp())


# Function to replace text in a file
def replace_text_in_file(file_path: Path, content: str, replacements: dict[str, str]):
    for old, new in replacements.items():
        content = content.replace(old, new)

    file_path.write_text(content, encoding="utf-8")


# Function to search for files and apply replacements
def search_and_replace(root_dir: Path, replacements: dict[str, str], exclude_dirs={".git"}):
    for root, dirs, files in root_dir.walk():
        # Skip the excluded directory
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            file_path = root / file
            try:
                content = file_path.read_text(encoding="utf-8")
                for search_term in replacements:
                    if search_term in content:
                        replace_text_in_file(file_path, content, replacements)
                        continue
            except (OSError, UnicodeDecodeError):
                # Skip files that cannot be read
                continue


def hydrogramify(repo: Repo):
    # Use our pyproject.toml file, where our Ruff settings live
    shutil.copyfile(HYDRO_ROOT_DIR / "pyproject.toml", PATCH_DIR / "pyproject.toml")

    # Rename everything from "pyrogram" to "hydrogram"
    print('Renaming everything from "pyrogram" to "hydrogram"…')
    shutil.move(PATCH_DIR / "pyrogram", PATCH_DIR / "hydrogram")

    search_and_replace(PATCH_DIR, {"pyrogram": "hydrogram", "Pyrogram": "Hydrogram"})

    # Format the code
    print("Formatting code…")
    subprocess.run(
        ["ruff", "check", "--quiet", "--fix", "--unsafe-fixes", PATCH_DIR],
        check=False,
        capture_output=True,
    )
    subprocess.run(["ruff", "format", "--quiet", PATCH_DIR], check=False, capture_output=True)

    # Commit the changes
    repo.git.add(all=True)
    repo.git.rm("pyproject.toml", cached=True)
    repo.index.commit("Format code", skip_hooks=True)


def checkout_code(repo: Repo, cp_type: str, cp_data: str, target_branch: str):
    if cp_type == "pr":
        print("Checking out PR code…")
        repo.git.fetch("origin", f"pull/{cp_data}/head:{target_branch}", quiet=True)
        repo.git.switch(target_branch, quiet=True)
        repo.git.rebase(ORIGIN_BRANCH, quiet=True)
    elif cp_type == "branch":
        print("Checking out branch code…")
        repo.git.switch("-c", target_branch, ORIGIN_BRANCH, quiet=True)
        repo.git.fetch(PATCH_DIR, cp_data, quiet=True)
        repo.git.merge("FETCH_HEAD", quiet=True, no_edit=True, no_ff=True)
    elif cp_type == "commit":
        print("Checking out commit code…")
        repo.git.switch("-c", target_branch, ORIGIN_BRANCH, quiet=True)
        repo.git.cherry_pick(cp_data, quiet=True)


def create_patch(repo: Repo, formatted_origin_branch: str, target_branch: str) -> Path:
    patch_path = Path(tempfile.mkdtemp()) / f"{target_branch}.patch"

    print(f"Creating patch and saving to {patch_path}…")
    patch = repo.git.diff(formatted_origin_branch, target_branch)

    patch_path.write_text(patch + "\n", encoding="utf-8")

    return patch_path


def apply_patch_to_formatted(repo: Repo, formatted_origin_branch: str, patch_path: Path):
    repo.git.switch(formatted_origin_branch, quiet=True)
    print("Applying patch…")
    repo.git.apply(patch_path)
    repo.git.add(all=True)
    repo.git.rm("pyproject.toml", cached=True)
    repo.index.commit("patch")


def fetch_commit(repo: Repo, temp_dir: Path, commit: str):
    print("Fetching commit…")
    repo.git.fetch(temp_dir, commit, quiet=True)


def apply_patch_to_hydrogram(
    repo: Repo, commit: str, changes_author: str, changes_date: str, changes_message: str
):
    print("Applying commit…")
    applied_successfully = True
    try:
        repo.git.cherry_pick(commit, X="ignore-all-space", no_commit=True)
    except exc.GitCommandError:
        applied_successfully = False

    if applied_successfully:
        print("\n✅ Patch applied successfully!")
        print("Now you can commit the changes with:")
    else:
        print("\n❗️ Patch applied with conflicts! Please resolve them and add the changes with:")
        print("git add .")
        print("and then commit the changes with:")

    print("git commit --all \\")
    print(f"    --author='{changes_author}' \\")
    print(f"    --date='{changes_date}' \\")
    print(f"    --message='{changes_message}'\n")

    print("If you would like to abort the cherry-pick, run:")
    print("git reset --merge")


def cleanup(temp_dir: Path):
    print("\nCleaning up…")
    shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    if len(sys.argv) < 3 or sys.argv[1] not in {"pr", "branch", "commit"}:
        print(f"Usage: {sys.argv[0]} pr <PR number>")
        print(f"       {sys.argv[0]} branch <branch name>")
        print(f"       {sys.argv[0]} commit <commit hash>")
        sys.exit(1)

    cp_type = sys.argv[1]
    cp_data = sys.argv[2]

    target_branch = f"{cp_type}-{cp_data}"
    formatted_origin_branch = f"formatted-{ORIGIN_BRANCH}"

    # Clone the Pyrogram repository into a temporary directory
    print("Cloning Pyrogram repository…")
    patch_repo = Repo.clone_from(f"https://github.com/{ORIGIN_REPO}.git", PATCH_DIR, quiet=True)

    hydro_repo = Repo.init(HYDRO_ROOT_DIR)

    # Switch to the formatted origin branch
    patch_repo.git.switch("-c", formatted_origin_branch, quiet=True)

    # Hydrogramify the code (without the changes applied)
    hydrogramify(patch_repo)

    # Fetch commits/branches to make them available for cherry-picking
    if cp_type in {"branch", "commit"}:
        try:
            patch_repo.git.fetch(HYDRO_ROOT_DIR, cp_data, quiet=True)
        except exc.GitCommandError:
            patch_repo.git.fetch(f"https://github.com/{ORIGIN_REPO}.git", cp_data, quiet=True)

    # Checkout the code
    checkout_code(patch_repo, cp_type, cp_data, target_branch)

    if cp_type == "branch":
        target_commit = patch_repo.git.log("-2", pretty="format:%H").split()[1]
    else:
        target_commit = "HEAD"

    # Get the commit message of the changes
    if cp_type == "pr":
        response = httpx.get(f"https://api.github.com/repos/{ORIGIN_REPO}/pulls/{cp_data}")
        if response.status_code == 200:
            changes_message = response.json()["title"]
        else:
            changes_message = patch_repo.git.log("-1", target_commit, pretty="format:%s")
    else:
        changes_message = patch_repo.git.log("-1", target_commit, pretty="format:%s")

    # Get the author of the changes
    changes_author = patch_repo.git.log("-1", target_commit, pretty="format:%an <%ae>")

    # Get the date of the changes
    changes_date = patch_repo.git.log("-1", target_commit, pretty="format:%aD")

    # Hydrogramify the code (with the changes applied)
    hydrogramify(patch_repo)

    # Create a patch between the two branches
    patch = create_patch(patch_repo, formatted_origin_branch, target_branch)

    # Apply the patch to the formatted branch
    apply_patch_to_formatted(patch_repo, formatted_origin_branch, patch)

    # Get the commit hash of the changes
    commit = patch_repo.git.log("-1", pretty="format:%H")

    # Fetch the commit from the temporary repository
    fetch_commit(hydro_repo, PATCH_DIR, commit)

    # Apply the patch to the Hydrogram repository
    apply_patch_to_hydrogram(hydro_repo, commit, changes_author, changes_date, changes_message)

    # Clean up
    cleanup(PATCH_DIR)


if __name__ == "__main__":
    main()
