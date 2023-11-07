#!/bin/env bash
set -e

# Config variables
ORIGIN_REPO="pyrogram/pyrogram"
ORIGIN_BRANCH="master"

RUFF_TOML=$(cat <<EOF
[tool.ruff]
line-length = 99
target-version = "py38"
select = [
    "I",    # isort
    "E",    # pycodestyle
    "W",    # pycodestyle
    "UP",   # pyupgrade
    "F",    # pyflakes
    "SIM",  # flake8-simplify
    "RET",  # flake8-return
    "C4",   # flake8-comprehensions
    "PTH",  # flake8-use-pathlib
    "PERF", # perflint
    "N",    # pep8-naming
    "RUF",  # ruff
    "G",    # flake8-logging-format
    "TID",  # flake8-tidy-imports
]
ignore = ["RUF001", "RUF002", "RUF003", "E203", "PERF203", "F401", "F403"]
preview = true

[tool.ruff.isort]
known-first-party = ["hydrogram"]
EOF
)

hydrogramify() {
    # Create a pyproject.toml file
    echo "$RUFF_TOML" > pyproject.toml

    # Rename everything from "pyrogram" to "hydrogram"
    echo "Renaming everything from \"pyrogram\" to \"hydrogram\"…"
    mv pyrogram hydrogram
    grep -rIl "pyrogram" --exclude-dir=.git . | xargs sed -i 's|pyrogram|hydrogram|g;s|Pyrogram|Hydrogram|g'

    # Format the code
    echo "Formatting code…"
    ruff check --quiet --fix --unsafe-fixes . > /dev/null 2>&1 || true
    ruff format --quiet .

    # Commit the changes
    git add -- . ':!pyproject.toml'
    git commit --quiet -m "Format code"
}

checkout_code() {
    if [ "$CP_TYPE" == "pr" ]; then
        echo "Checking out PR code…"

        git fetch --quiet origin "pull/$CP_DATA/head:$TARGET_BRANCH"
        git switch --quiet "$TARGET_BRANCH"
        git rebase --quiet "$ORIGIN_BRANCH"
    elif [ "$CP_TYPE" == "branch" ]; then
        echo "Checking out branch code…"

        git switch --quiet -c "$TARGET_BRANCH" "$ORIGIN_BRANCH"
        git fetch --quiet "$CWD" "$CP_DATA"
        git merge --quiet --no-edit --no-ff FETCH_HEAD > /dev/null
    elif [ "$CP_TYPE" == "commit" ]; then
        echo "Checking out commit code…"

        git switch --quiet -c "$TARGET_BRANCH" "$ORIGIN_BRANCH"
        git cherry-pick --quiet "$CP_DATA" > /dev/null
    fi
}

create_patch() {
    # Create a patch between the two branches
    echo "Creating patch and saving to /tmp/$TARGET_BRANCH.patch…"
    git diff "$FORMATTED_ORIGIN_BRANCH" "$TARGET_BRANCH" > "/tmp/$TARGET_BRANCH.patch"
}

apply_patch_to_formatted() {
    # Switch back to the $FORMATTED_ORIGIN_BRANCH branch
    git switch --quiet "$FORMATTED_ORIGIN_BRANCH"

    # Apply the patch to the formatted branch
    echo "Applying patch…"
    git apply "/tmp/$TARGET_BRANCH.patch"

    # Commit the changes
    git add -- . ':!pyproject.toml'
    git commit --quiet --allow-empty -m "patch"
}

fetch_commit() {
    # Fetch the commit from the temporary repository
    echo "Fetching commit…"
    git fetch --quiet "$TEMP_DIR" "$COMMIT"
}

apply_patch_to_hydrogram() {
    # Apply the patch to the Hydrogram repository
    echo "Applying commit…"
    applied_successfully=0
    git cherry-pick -X ignore-all-space --no-commit "$COMMIT" || applied_successfully=1

    if [ "$applied_successfully" == "0" ]; then
        echo -e "\nPatch applied successfully!"
        echo -e "Now you can commit the changes and push them to the repository with:"
    else
        echo -e "\nPatch applied with conflicts! Please resolve them and add the changes with:"
        echo -e "git add .\n"
        echo -e "If you would like to abort the cherry-pick, run:"
        echo -e "git reset --merge\n"

        echo -e "and then commit the changes with:"
    fi

    echo "git commit --all \\"
    echo "    --author='$CHANGES_AUTHOR' \\"
    echo "    --date='$CHANGES_DATE' \\"
    echo "    --message='$CHANGES_MESSAGE'"
}

cleanup() {
    # Clean up
    echo -e "\nCleaning up…"
    rm -rf "$TEMP_DIR"
}

main() {
    if { [ "$1" != "pr" ] && [ "$1" != "branch" ] && [ "$1" != "commit" ]; } || [ -z "$2" ]; then
        echo "Usage: $0 pr <PR number>"
        echo "       $0 branch <branch name>"
        echo "       $0 commit <commit hash>"
        exit 1
    fi

    CP_TYPE=$1
    CP_DATA=$2
    CWD=$(pwd)

    TARGET_BRANCH="$CP_TYPE-$CP_DATA"
    FORMATTED_ORIGIN_BRANCH="formatted-$ORIGIN_BRANCH"

    # Clone the Pyrogram repository into a temporary directory
    echo "Cloning Pyrogram repository…"
    TEMP_DIR=$(mktemp -d)
    git clone --quiet https://github.com/$ORIGIN_REPO.git "$TEMP_DIR"

    # Switch to the $FORMATTED_ORIGIN_BRANCH branch
    cd "$TEMP_DIR"
    git switch --quiet -c "$FORMATTED_ORIGIN_BRANCH"

    # Hydrogramify the code (without the changes applied)
    hydrogramify

    # Fetch commits/branches to make them available for cherry-picking
    if [ "$CP_TYPE" == "branch" ] || [ "$CP_TYPE" == "commit" ]; then
        git fetch --quiet "$CWD" "$CP_DATA" || git fetch --quiet https://github.com/$ORIGIN_REPO.git "$CP_DATA" || true
    fi

    # Checkout the code
    checkout_code

    if [ "$CP_TYPE" == "branch" ]; then
        TARGET_COMMIT=$(git log -2 --pretty=format:"%H" | sed -n '2 p')
    else
        TARGET_COMMIT=HEAD
    fi

    # Get the commit message of the changes
    if [ "$CP_TYPE" == "pr" ]; then
        CHANGES_MESSAGE=$(curl -s "https://api.github.com/repos/$ORIGIN_REPO/pulls/$CP_DATA" | jq -r '.title' || git log -1 --pretty=format:"%s" "$TARGET_COMMIT")
    else
        CHANGES_MESSAGE=$(git log -1 --pretty=format:"%s" "$TARGET_COMMIT")
    fi

    # Get the author of the changes
    CHANGES_AUTHOR=$(git log -1 --pretty=format:"%an <%ae>" "$TARGET_COMMIT")

    # Get the date of the changes
    CHANGES_DATE=$(git log -1 --pretty=format:"%aD" "$TARGET_COMMIT")

    # Hydrogramify the code (with the changes applied)
    hydrogramify

    # Create a patch between the two branches
    create_patch

    # Apply the patch to the formatted branch
    apply_patch_to_formatted

    # Get the commit hash of the changes
    COMMIT=$(git log -1 --pretty=format:"%H")

    cd "$CWD"

    # Fetch the commit from the temporary repository
    fetch_commit

    # Apply the patch to the Hydrogram repository
    apply_patch_to_hydrogram

    # Clean up
    cleanup
}

main "$@"
