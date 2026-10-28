---
name: hydrogram-update-api
description: Update Hydrogram's Telegram MTProto API schema and regenerate bindings when upgrading the API layer or applying upstream schema changes.
---

# Update the MTProto API

Deliver a reviewed schema update with regenerated bindings, compatible existing callers,
and validation results. Run commands from the repository root and follow `AGENTS.md` and
`CONTRIBUTING.md`. Use the existing tools under `dev_tools/`; no new helper is needed.

## Establish the target

- Inspect `git status --short` and the current `// LAYER` in
  `compiler/api/source/main_api.tl`. Preserve existing local edits; if that schema is
  already modified, inspect its diff before allowing an updater to overwrite it.
- Honor a requested layer or upstream revision. With no specified target, use the latest
  schema from Telegram Desktop's `dev` branch, as configured in
  `dev_tools/check_api_schema_updates.py`.
- For a pinned target, obtain the schema from the matching upstream revision and retain
  its provenance. The updater always fetches `dev`; it cannot select an older layer.
  Preserve the local header and manually handled basic types when adapting pinned input.

## Update and review the schema

For the latest upstream schema, run:

```bash
uv run make check-api-schema
```

The script writes `compiler/api/source/main_api.tl`; it is not a read-only check.
Exit codes are **0** for an applied update, **2** for no change, and **1** for a fetch
or processing error. Treat 2 as a successful no-op. Do not force an update to work around
an error. If unchanged, report that result without inventing a release fragment or edits;
continue with documentation refresh only if the user requested it independently.

Review the schema diff even when the layer number is unchanged. Identify added, removed,
and changed constructors and methods, including IDs, argument types, flags, and return
types. Verify that the target layer is present and the schema sections and manually
handled basic types remain valid. Change other schemas under `compiler/api/source/` only
when the upstream change requires it.

Use [Corefork API documentation](https://corefork.telegram.org/api) and
[MTProto documentation](https://corefork.telegram.org/mtproto) for protocol semantics;
check that examples and fields apply to the target layer.

## Refresh raw API descriptions when needed

Evaluate a documentation refresh when the schema adds or renames types, constructors,
methods, or parameters, or when the user explicitly requests updated API documentation.
For parameter removals or other signature changes, check whether existing descriptions
became stale. Skip the scrape when the existing descriptions still fit the target schema;
a layer-number or constructor-ID change alone does not require fetching every page.

`uv run make generate-docs-json` reads the updated local `main_api.tl`, fetches Corefork
pages for its objects, and replaces `compiler/api/docs.json`. The compiler uses this JSON
for raw binding docstrings. `uv run make docs` instead generates Sphinx reference pages
and builds HTML; it does not refresh the JSON. The scraper fetches current pages, so
verify descriptions against the target schema, especially for a pinned older layer.

When refreshing, use this order: update schema, collect and validate the JSON, regenerate
bindings, then build the documentation.

1. Before running the generator, save an exact copy of the existing JSON outside the
   checkout in a temporary location. Preserve any uncommitted edits in that copy; do not
   rely on `git restore` or the version in HEAD. If no JSON exists, record that fact.
2. Run `uv run make generate-docs-json` from the repository root and capture its output.
   It fetches all objects, not only changed ones. HTTP errors, missing page content,
   missing descriptions, and missing parameter sections can leave incomplete results
   **even with exit code zero and a `Done!` message**.
3. Parse the candidate JSON and check its `type`, `constructor`, and `method` mappings.
   Compare keys with those expected from the updated schema using the generator's
   `parse_tl_file` naming rules. Compare entries, nonempty descriptions, and documented
   parameter names with the saved JSON and target signatures. Inspect affected objects
   and unexpected losses; do not require parameter tables for parameterless objects.
   Distinguish legitimate removals or renames from failed requests or parsing changes.
4. Accept only reviewed documentation changes. If the fetch fails, truncates the JSON,
   or drops valid content, restore the exact saved copy. If partial results are useful,
   retain only individually verified updates merged into that copy, preserving unaffected
   documentation and local edits. With no previous file, keep an incomplete candidate
   outside the checkout rather than adopting it as a successful refresh. Report any
   remaining missing documentation; do not invent descriptions or retry indefinitely.

## Regenerate and adapt existing callers

```bash
uv run make api
```

If dependencies are missing, use the setup commands in `CONTRIBUTING.md`.
Fix generation problems in compiler inputs or templates. Generated bindings and RPC
exceptions are ignored by Git; do not patch or force-add them.

Search `hydrogram/` for uses of changed raw constructors, methods, and fields. Adapt
existing serialization, parsing, and invocation paths where the new schema breaks them.
Keep unrelated new high-level features outside this update unless requested. Add focused
regression tests for behavior changed in handwritten code.

Regenerate bindings again after any later compiler input or documentation JSON changes.

## Validate and report

- Confirm `hydrogram.raw.all.layer` matches the target and that Hydrogram imports.
  Exercise relevant generated signatures or serialization when the schema changes require it.
- Run focused tests for adapted callers, then `uv run pytest tests`.
- Run the repository Ruff checks if Python sources changed. Build with `uv run make docs`
  when handwritten documentation or API documentation generation changed.
- For an actual update, add `news/<issue-or-pr>.misc.rst` describing the layer/schema
  change, following the repository's fragment naming convention. Update user-facing docs
  if public behavior changed.
- Review the final diff and `git diff --check`. Report the old and new layer, upstream
  source/revision when known, significant schema changes, caller adaptations, and checks
  passed or blocked. State whether the documentation JSON was refreshed, skipped, or
  restored, and list unresolved scrape failures or missing descriptions. Distinguish schema
  support from new high-level API coverage.

Commit, push, or open a pull request only when requested by the user.
