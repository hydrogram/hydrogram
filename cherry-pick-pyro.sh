#!/bin/env bash
set -e

# Config variables

# The Pyrogram repository to pull from
ORIGIN_REPO="pyrogram/pyrogram"
# The branch to pull from
ORIGIN_BRANCH="master"


FORMATTED_ORIGIN_BRANCH="formatted-$ORIGIN_BRANCH"

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


# Clone the Pyrogram repository into a temporary directory
echo "Cloning Pyrogram repository…"
TEMP_DIR=$(mktemp -d)
git clone --quiet https://github.com/$ORIGIN_REPO.git "$TEMP_DIR"

# Switch to the $FORMATTED_ORIGIN_BRANCH branch
cd "$TEMP_DIR"
git switch --quiet -c "$FORMATTED_ORIGIN_BRANCH"

# Format the code
echo "Formatting $ORIGIN_BRANCH code…"
ruff format --quiet .

# Commit the changes
git commit --quiet -am "Format code"

# Fetch commits/branches to make them available for cherry-picking
if [ "$CP_TYPE" == "branch" ] || [ "$CP_TYPE" == "commit" ]; then
    git fetch --quiet "$CWD" "$CP_DATA" || git fetch --quiet https://github.com/$ORIGIN_REPO.git "$CP_DATA" || true
fi # PR

# Checkout the code
if [ "$CP_TYPE" == "pr" ]; then
    echo "Checking out PR code…"

    git fetch --quiet origin "pull/$CP_DATA/head:$TARGET_BRANCH"
    git switch --quiet "$TARGET_BRANCH"
elif [ "$CP_TYPE" == "branch" ]; then
    echo "Checking out branch code…"

    git switch --quiet -c "$TARGET_BRANCH" "$ORIGIN_BRANCH"
    git cherry-pick --quiet "$CP_DATA" > /dev/null 2>&1
elif [ "$CP_TYPE" == "commit" ]; then
    echo "Checking out commit code…"

    git switch --quiet -c "$TARGET_BRANCH" "$ORIGIN_BRANCH"
    git cherry-pick --quiet "$CP_DATA" > /dev/null 2>&1
fi

# Get the commit message of the changes
if [ "$CP_TYPE" == "pr" ]; then
    CHANGES_MESSAGE=$(curl -s "https://api.github.com/repos/$ORIGIN_REPO/pulls/$CP_DATA" | jq -r '.title' || git log -1 --pretty=format:"%s" "$TARGET_BRANCH")
else
    CHANGES_MESSAGE=$(git log -1 --pretty=format:"%s" "$TARGET_BRANCH")
fi

# Get the author of the changes
CHANGES_AUTHOR=$(git log -1 --pretty=format:"%an <%ae>" "$TARGET_BRANCH")

# Get the date of the changes
CHANGES_DATE=$(git log -1 --pretty=format:"%aD" "$TARGET_BRANCH")

# Format the code
echo "Formatting code…"
ruff format --quiet .

# Commit the changes
git commit --quiet --allow-empty -am "Format code"

# Create a patch between the two branches
echo "Creating patch and saving to /tmp/$TARGET_BRANCH.patch…"
git diff "$FORMATTED_ORIGIN_BRANCH" "$TARGET_BRANCH" | sed 's|pyrogram|hydrogram|g;s|Pyrogram|Hydrogram|g' > "/tmp/$TARGET_BRANCH.patch"

# Apply the patch to the Hydrogram repository
echo "Applying patch…"
cd "$CWD"
applied_successfully=0
git apply "/tmp/$TARGET_BRANCH.patch" || applied_successfully=1

if [ "$applied_successfully" == "0" ]; then
    echo -e "\nPatch applied successfully!"
    echo -e "Now you can commit the changes and push them to the repository with:\n"
else
    echo -e "\nPatch applied with conflicts! Please resolve them and add the changes with:"
    echo -e "git add .\n"

    echo -e "and then commit the changes with:"
fi

echo "git commit --all \\"
echo "    --author='$CHANGES_AUTHOR' \\"
echo "    --date='$CHANGES_DATE' \\"
echo "    --message='$CHANGES_MESSAGE'"

# Clean up
echo -e "\nCleaning up…"
rm -rf "$TEMP_DIR"
