---
name: hydrogram-audit-bot-api
description: Compare Hydrogram with the Telegram Bot API and investigate missing methods, objects, or fields when auditing Bot API feature coverage.
---

# Audit Bot API coverage

Produce an evidence-based comparison of Bot API features and Hydrogram's public API.
Follow `AGENTS.md` and `CONTRIBUTING.md`; run commands from the repository root.
This workflow analyzes coverage. Implement features or change the comparison tool only
when the user asks for those changes.

## Collect the comparison

- Establish the requested scope: a full audit, a Bot API release, or particular features.
  Use the current official documentation when no version is specified. For a historical
  release, use matching documentation; the script fetches the live page only.
- Inspect the current `// LAYER` in `compiler/api/source/main_api.tl` and the comparison
  logic and `ignored_items` in `dev_tools/compare_to_bot_api.py`.
- Ensure generated bindings exist before importing Hydrogram. If they are missing or
  stale, run `uv run make api`; use the dependency setup in `CONTRIBUTING.md` if needed.
  An audit does not require updating the schema to a newer layer.
- Run `uv run make compare-bot-api`. It fetches the live Bot API documentation and prints
  a Markdown comparison of method names, object names, and constructor parameters.
  Check that the output contains plausible methods and objects. Fetch or parsing errors
  and empty results do not establish that a feature is unsupported.

Use [the official Bot API documentation](https://core.telegram.org/bots/api) to verify
feature semantics and the release/date being compared. If live access fails, explain the
limitation and use explicitly identified local or supplied evidence where available;
do not present an incomplete run as a current full audit.

## Investigate findings

The report is a list of candidates, not a compatibility test. For findings within the
requested scope, trace the relevant public methods in `hydrogram/methods/`, object
constructors and parsers in `hydrogram/types/`, and local API documentation in
`docs/source/`. Check raw schema definitions when MTProto support is relevant.

Classify each investigated finding as:

- **Confirmed gap:** the Bot API behavior has no equivalent public implementation.
- **Equivalent support:** Hydrogram exposes the behavior through a different name,
  argument, object shape, or method. Cite the actual implementation.
- **Intentional difference:** the Bot API mechanism does not apply to the MTProto client,
  such as HTTP webhooks or Bot API polling. Verify existing exclusions before proposing one.
- **Layer dependency:** the local MTProto schema lacks a definition needed for the feature.
  Identify the missing definition and supporting evidence; do not infer a required layer
  solely from a Bot API version number.
- **Unverified:** available evidence does not establish support or absence.

Check both directions: matching names and arguments do not prove equivalent behavior,
permissions, defaults, parsing, or bot-account availability. Raw bindings alone do not
prove high-level support. Aliases such as `message_id` / `id` and `from` / `from_user`
can explain apparent gaps; inspect the code before applying an alias or exclusion.

The script's percentages measure name/parameter matching, not functional coverage.
Ignored items still contribute to its current totals, so avoid presenting its numbers as
validated support percentages. Do not modify exclusions merely to improve the score.

## Report the audit

State the Bot API version/date checked, local MTProto layer, command outcome, and scope
actually investigated. Present a table with the Bot API feature, classification,
Hydrogram equivalent or missing behavior, and evidence. Link official documentation and
relevant local source files. Separate uninvestigated script findings from confirmed gaps.

For confirmed gaps, describe a concrete next step and any schema prerequisite. If useful,
prioritize by user impact and implementation dependencies. Do not automatically upgrade
the layer, implement features, or create GitHub issues as part of the audit.
