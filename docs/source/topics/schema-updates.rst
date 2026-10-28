Updating the MTProto Schema
===========================

Raw protocol support and the Client API
---------------------------------------

``hydrogram.raw.all.layer`` identifies the application API layer generated from
``compiler/api/source/main_api.tl``. Raw constructors and functions are available
through ``hydrogram.raw`` and :meth:`~hydrogram.Client.invoke`. A layer upgrade
does not automatically add Client methods, public object fields, or parsers for
all new Telegram features. New high-level features need their own implementation
and tests.

The layer 223 to 232 update preserves the existing poll and keyboard interfaces.
Poll creation uses input answers and integer quiz-answer indices; received poll
option identifiers remain opaque bytes. Poll questions and answers are exposed
as strings. Partial vote results are matched by option identifier. Existing
keyboards use Telegram's new button-type wrappers internally. Successful chat
joins unwrap the new response and cache its peers. Joins requiring interactive
bot verification raise ``NotAcceptable`` with instructions to complete the
verification in an official Telegram client.

Optional raw vectors distinguish an absent field (``None``) from a present empty
vector (``[]``). Applications consuming raw objects must handle both. High-level
parsers normalize absent vectors as needed. This distinction is necessary to
serialize shared flag groups such as a quiz solution and its empty entity vector.

Sources and the current audit
-----------------------------

The previous checkout declared layer 223 and recorded only a mutable Desktop
``dev`` URL. The updater fetched without a timeout, wrote before validation, and
reported no change as exit 2; the workflow's fail-fast shell could stop before
handling that status. CI attempted to stage ignored generated files and force-push
an update branch without import, wire, compatibility, or determinism checks.
The raw compiler retained reference maps between runs, and error generation used
filesystem enumeration order. These behaviors are replaced by the checks below.

On 2026-10-28, the latest downloaded Telegram Desktop schema declared layer 232:

* `Telegram Desktop api.tl at f985723b552b30fe1c17d377d57f44e61a15a8c4
  <https://github.com/telegramdesktop/tdesktop/blob/f985723b552b30fe1c17d377d57f44e61a15a8c4/Telegram/SourceFiles/mtproto/scheme/api.tl>`_.
* `TDLib telegram_api.tl at 4c6377aa7386c39217878a9a56d581922ad37ca4
  <https://github.com/tdlib/td/blob/4c6377aa7386c39217878a9a56d581922ad37ca4/td/generate/scheme/telegram_api.tl>`_.

All 2,578 shared upstream declarations agree. TDLib has additional primitive,
legacy, configuration, and invocation-prefix declarations; Desktop additionally
includes ``null``. The Telegram `schema page <https://core.telegram.org/schema>`_
still advertised layer 225 when checked, while individual poll documentation pages
already described the updated poll signatures. The updater therefore resolves
Desktop's ``dev`` branch and compares its immutable schema with TDLib, rather than
hardcoding a target or relying on the website's displayed layer alone.

The application schema adds 294 declarations, removes 18, and changes 73 relative
to this checkout's layer 223. Changes include polls, keyboards, join responses,
rich messages, communities, wallet operations, and additional flags. These counts
exclude manually handled basic declarations. New feature families have raw
support; they do not imply equivalent high-level coverage.

``compiler/api/source/provenance.json`` records source commit IDs, download URLs,
SHA-256 checksums of the original files, the normalized local checksum, and the
cross-source comparison. The local adapter comments out basic constructors that
Hydrogram implements by hand and keeps one types/functions section. Generated
Python files and exceptions remain ignored by Git and are always regenerated
from compiler inputs. No generated code from other client forks is used.

The audit also compared ``auth_key.tl`` and ``sys_msgs.tl`` with Desktop's
``mtproto.tl`` at the same revision. Shared wire declarations are unchanged;
Hydrogram intentionally uses binary ``bytes`` for DH payloads that Desktop labels
``string`` (identical TL wire encoding), and retains its manual container, salt,
RPC-result, and gzip handlers. The generator now preserves the bare vector encoding used by
configuration responses. These transport schemas were not replaced with the
application schema.

Checking and applying updates
-----------------------------

Install the locked development environment with ``uv sync --locked --all-extras --dev``
and work from the repository root.
First inspect ``git status --short`` and preserve any local compiler input edits.
The check is read-only by default:

.. code-block:: console

    uv run --locked python dev_tools/check_api_schema_updates.py \
        --report /tmp/schema-update.md --json-report /tmp/schema-update.json

Exit codes are **0** for current inputs, **2** for drift (including same-layer
constructor or signature changes), and **1** for errors or source disagreements.
This replaces the old updater's implicit writes and inverted no-change status.
``make check-api-schema`` uses the same read-only check; make reports a nonzero
exit when drift is present.

The report lists added, removed, and changed declarations with complete before
and after signatures, immutable provenance, and a pinned adoption command.
Review IDs, flags, required parameters, argument types, and return types. Search
handwritten callers and parsers before adopting removals or changed signatures.
Apply with the exact revisions from that report:

.. code-block:: console

    uv run --locked python dev_tools/check_api_schema_updates.py --apply \
        --revision DESKTOP_COMMIT --tdlib-revision TDLIB_COMMIT \
        --report /tmp/schema-update.md

``--apply`` returns **0** on success or no change, and **1** on failure. It first
validates in a temporary copy of the current compiler, library, and tests. Only a
successful candidate replaces the schema and provenance inputs. Invalid schemas,
missing layers, duplicate IDs, changed manual primitives, layer downgrades,
TDLib disagreements, generation failures, and failing tests block adoption.
No validation bypass or force-update option is provided. ``make update-api-schema``
selects and validates the latest mutually verified upstream schema.

If a candidate fails, inputs stay unchanged and the report explains the failure;
the workflow log contains test details. Make the necessary compiler or caller
changes, add regression tests, and rerun the pinned command. For extensive work,
use a disposable checkout to develop against the candidate schema, retaining the
report's exact revisions and checksums. Do not accept a partial upgrade that
breaks existing parsers. Document any unsupported high-level feature explicitly.

Regenerate the working checkout and validate it offline:

.. code-block:: console

    uv run --locked make api
    uv run --locked make validate-api-schema
    uv run --locked ruff check .
    uv run --locked ruff format --check .
    uv run --locked make docs
    git diff --check

Validation regenerates raw bindings and errors twice in one Python process,
then again in a fresh process with a different hash seed, comparing every
output Python file and path. It imports generated modules and runs the complete
offline test suite. Tests cover every schema constructor and function with
optional fields absent and present, wire serialization/deserialization, explicit
empty vectors, registry coverage, handwritten references and call signatures,
and affected high-level parsers. Generation subprocesses have a 120-second limit,
and the test subprocess has a 300-second limit; timeouts block adoption. Tests
also verify the byte layout of bare transport vectors. These checks do not replace authenticated
integration testing against Telegram; no credentials are needed by the offline
suite.

RPC errors and documentation
----------------------------

RPC error definitions in ``compiler/errors/source/*.tsv`` are independently
curated. Telegram's TL schemas contain no complete error catalogue, and documented
errors are not strictly layer-versioned. Review the official
`error documentation <https://core.telegram.org/api/errors>`_ and each affected
method's error table. Add verified entries to the appropriate status-code TSV,
preserve existing definitions, and regenerate with ``make api``. The poll audit
added ``POLL_COUNTRY_RESTRICTED`` and ``POLL_MEMBER_RESTRICTED`` (406); the existing
``REVOTE_NOT_ALLOWED`` (400) entry was retained. Regression tests verify dispatch.

``compiler/api/docs.json`` is a separately maintained description cache, not a
protocol source. This update selectively refreshed eight poll-related entries
from official pages whose signatures exactly matched the pinned schema. Existing
unaffected entries were preserved. The poll-voter page claimed mutual exclusion
for two fields sharing one flag; that contradictory phrase was omitted. No full
scrape was adopted: some newer pages, including keyboard and join-webview pages,
were unavailable. Undocumented new raw fields retain generic descriptions.

When using ``make generate-docs-json``, first save an exact copy of the existing
JSON outside the checkout. A successful scraper exit can still contain missing
pages or descriptions. Compare keys, nonempty descriptions, and parameter names
against both the old cache and target signatures. Restore the saved file on
unreviewed content losses, or merge only individually verified entries, then
regenerate bindings and build the documentation.

Known high-level gaps predating this upgrade
--------------------------------------------

The static caller audit found these references already absent from the layer 223
schema. They are explicitly tracked as a baseline in ``tests/test_raw_schema.py``
and remain separate maintenance work:

* Forum-topic methods reference ``channels.EditForumTopic``,
  ``channels.CreateForumTopic``, ``channels.DeleteTopicHistory``,
  ``channels.GetForumTopics``, and ``channels.GetForumTopicsByID``; the raw schema
  exposes their equivalents in ``messages`` with ``peer`` parameters.
* Ownership transfer references the absent ``channels.EditCreator``.
* The chat-background parser annotation spells ``WallPaper`` as ``Wallpaper``.

The baseline permits only those existing references. Newly missing raw references
or incompatible direct call signatures fail validation. It does not claim complete
semantic coverage of every high-level method or raw feature.

A Python 3.11 run with only ``--dev`` dependencies stalled in the existing
reconnect-test fixture and was interrupted. Validation passes with the locked
``--all-extras`` environment used by the test matrix and schema workflow; the
default-event-loop reconnect issue remains outside this schema update.

CI reports and review
---------------------

``.github/workflows/check_api_updates.yml`` runs every twelve hours, on demand,
and for changes to pipeline inputs. It validates checked-in generation offline,
checks live drift, and validates any candidate using the revisions captured in
its JSON report. Drift fails the job to request maintainer review. The job summary
and ``mtproto-schema-report`` artifact contain Markdown and JSON reports; a
candidate patch is included only after validation succeeds. Failed candidates
still produce reports and retain their validation logs. The workflow uses read-only
repository permissions and does not create branches, commits, or pull requests.

Review the schema, provenance, affected callers, documentation, and tests together.
Add a ``news/<identifier>.misc.rst`` fragment. Generated modules must not be staged.
Commit or publish only after review; an upstream layer number alone is not evidence
that a candidate is compatible.
