#!/usr/bin/env python3
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

import argparse
import hashlib
import logging
import re
import sys
from pathlib import Path
from typing import TypedDict

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Constants
API_SCHEMA_URL = "https://raw.githubusercontent.com/telegramdesktop/tdesktop/dev/Telegram/SourceFiles/mtproto/scheme/api.tl"

REPO_HOME = Path(__file__).parent.parent
API_DIR = REPO_HOME / "compiler" / "api"
SOURCE_DIR = API_DIR / "source"
MAIN_API_PATH = SOURCE_DIR / "main_api.tl"

LAYER_RE = re.compile(r"//\s*LAYER\s+(\d+)")

SCHEMA_HEADER = """// https://github.com/telegramdesktop/tdesktop/blob/dev/Telegram/SourceFiles/mtproto/scheme/api.tl

///////////////////////////////
///////// Main application API
///////////////////////////////

---types---

// boolFalse#bc799737 = Bool;  // Parsed manually
// boolTrue#997275b5 = Bool;  // Parsed manually

// true#3fedd339 = True;  // Not used

// vector#1cb5c415 {t:Type} # [ t ] = Vector t;  // Parsed manually

// error#c4b9f9bb code:int text:string = Error;  // Not used

// null#56730bcc = Null;  // Parsed manually
"""

BASIC_TYPES = [
    "boolFalse#bc799737 = Bool;",
    "boolTrue#997275b5 = Bool;",
    "true#3fedd339 = True;",
    "vector#1cb5c415 {t:Type} # [ t ] = Vector t;",
    "error#c4b9f9bb code:int text:string = Error;",
    "null#56730bcc = Null;",
]


class SchemaData(TypedDict):
    """Schema data returned from the Telegram API."""

    content: str
    hash: str
    layer: str


def get_current_schema_hash() -> str | None:
    """
    Get the hash of the current schema file if it exists.

    Returns:
        str | None: SHA256 hash of the current schema file or None if it doesn't exist
    """
    if not MAIN_API_PATH.exists():
        return None

    return hashlib.sha256(MAIN_API_PATH.read_bytes()).hexdigest()


def get_latest_schema() -> SchemaData | None:
    """
    Fetch the latest API schema from Telegram's repository.

    Returns:
        SchemaData | None: Dictionary containing the schema content, hash, and layer version
                          or None if fetching or processing fails
    """
    logger.info("Fetching latest API schema from Telegram repository")

    try:
        api_response = requests.get(API_SCHEMA_URL)
        api_response.raise_for_status()

        api_content = api_response.text

        # Extract layer version from the API content
        layer_match = LAYER_RE.search(api_content)
        layer_version = layer_match.group(1) if layer_match else "Unknown"

        # Process in new format mode
        functions_idx = api_content.find("---functions---")
        if functions_idx != -1:
            types_part = api_content[:functions_idx].strip()
            functions_part = api_content[functions_idx:]
        else:
            # Just treat everything as types since there's no clear separator
            types_part = api_content
            functions_part = ""

        # Remove basic types that are already in our header
        # But preserve empty lines to maintain block structure
        processed_types: list[str] = []

        for line in types_part.split("\n"):
            line_stripped = line.strip()

            # Keep empty lines
            if not line_stripped:
                processed_types.append("")
                continue

            # Skip basic types that are in our header
            if not any(
                line_stripped.startswith(basic_type.split("=")[0].strip())
                for basic_type in BASIC_TYPES
            ):
                processed_types.append(line)

        # Combine our header with processed schema - trim extra whitespace
        processed_types_content = "\n".join(processed_types).strip()

        if functions_part:
            schema_content = f"{SCHEMA_HEADER}\n{processed_types_content}\n\n{functions_part}"
        else:
            schema_content = f"{SCHEMA_HEADER}\n{processed_types_content}"

        schema_hash = hashlib.sha256(schema_content.encode()).hexdigest()

        return {"content": schema_content, "hash": schema_hash, "layer": layer_version}
    except requests.RequestException as e:
        logger.error("Error fetching schema: %s", e)
        return None
    except (ValueError, KeyError) as e:
        logger.error("Error processing schema: %s", e)
        return None


def update_schema(schema_data: SchemaData) -> bool:
    """
    Update the schema file with new content.

    Args:
        schema_data: Dictionary containing schema content, hash, and layer version

    Returns:
        bool: True if update was successful
    """
    logger.info("Updating schema to layer %s", schema_data["layer"])

    SOURCE_DIR.mkdir(parents=True, exist_ok=True)

    MAIN_API_PATH.write_text(schema_data["content"], encoding="utf-8")

    logger.info("Schema updated successfully to layer %s", schema_data["layer"])
    return True


def get_current_layer() -> str:
    """
    Get the layer version from the current schema file.

    Returns:
        str: Current layer version or "Unknown" if not found
    """
    if not MAIN_API_PATH.exists():
        return "Unknown"

    content = MAIN_API_PATH.read_text(encoding="utf-8")
    layer_match = LAYER_RE.search(content)
    return layer_match.group(1) if layer_match else "Unknown"


def main() -> int:
    """
    Main function to check for and apply schema updates.

    Returns:
        int: Exit code (0: update applied, 1: error, 2: no update needed)
    """
    parser = argparse.ArgumentParser(description="Check for updates to the Telegram API schema")
    parser.add_argument(
        "--force-update", action="store_true", help="Force update even if no changes detected"
    )
    args = parser.parse_args()

    current_hash = get_current_schema_hash()
    schema_data = get_latest_schema()

    if not schema_data:
        logger.error("Failed to fetch schema data")
        return 1

    if args.force_update or current_hash != schema_data["hash"]:
        if current_hash:
            logger.info(
                "Schema update detected! Current layer: %s → New layer: %s",
                get_current_layer(),
                schema_data["layer"],
            )
        else:
            logger.info("Initializing schema with layer %s", schema_data["layer"])

        update_schema(schema_data)
        return 0

    logger.info("No schema updates detected. Current layer: %s", get_current_layer())
    return 2


if __name__ == "__main__":
    sys.exit(main())
