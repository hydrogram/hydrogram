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

import json
import subprocess
from unittest.mock import Mock

import pytest
import requests

from dev_tools import check_api_schema_updates as updater

BASICS = """boolFalse#bc799737 = Bool;
boolTrue#997275b5 = Bool;
true#3fedd339 = True;
vector#1cb5c415 {t:Type} # [ t ] = Vector t;
error#c4b9f9bb code:int text:string = Error;
null#56730bcc = Null;
"""


def upstream(layer=100, declaration="example#1234 value:int = Example;"):
    return (
        f"{BASICS}\n{declaration}\n---functions---\ngetExample#5678 = Example;\n// LAYER {layer}\n"
    )


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    monkeypatch.setattr(updater, "REPO_HOME", tmp_path)
    path = tmp_path / updater.SCHEMA_PATH
    path.parent.mkdir(parents=True)
    path.write_text(updater.normalize_schema(upstream()))
    (tmp_path / updater.PROVENANCE_PATH).write_text(
        json.dumps({"layer": 100, "normalized_sha256": updater.sha256(path.read_bytes())})
    )
    monkeypatch.setattr(updater, "validate_candidate", Mock())
    return tmp_path


def mock_sources(monkeypatch, desktop, tdlib=None):
    def fetch(repo, path, revision):
        content = desktop if repo == updater.DESKTOP_REPO else (tdlib or desktop)
        return content, {
            "repository": repo,
            "path": path,
            "revision": "a" * 40,
            "url": f"https://raw.githubusercontent.com/{repo}/{'a' * 40}/{path}",
            "sha256": updater.sha256(content.encode()),
        }

    monkeypatch.setattr(updater, "fetch_source", fetch)


def test_check_is_read_only_and_detects_same_layer_signature_drift(checkout, monkeypatch):
    path = checkout / updater.SCHEMA_PATH
    before = path.read_bytes()
    mock_sources(monkeypatch, upstream(declaration="example#1234 value:long = Example;"))
    report = checkout / "report.md"
    assert updater.main(["--report", str(report)]) == 2
    assert path.read_bytes() == before
    assert "Changed (1)" in report.read_text()
    assert "value:long" in report.read_text()
    updater.validate_candidate.assert_not_called()


def test_current_returns_success(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream())
    assert updater.main([]) == 0


def test_metadata_only_revision_does_not_cause_drift(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream())
    assert updater.main(["--apply"]) == 0
    updater.validate_candidate.assert_called_once_with(checkout, {})


def test_apply_validates_candidate_before_replacing_inputs(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream(101))
    path = checkout / updater.SCHEMA_PATH

    def validate(repo, replacements):
        assert updater.get_layer(path.read_text()) == 100
        assert updater.get_layer(replacements[updater.SCHEMA_PATH]) == 101

    monkeypatch.setattr(updater, "validate_candidate", validate)
    assert updater.main(["--apply"]) == 0
    updater.check_provenance(checkout)
    assert updater.get_layer(path.read_text()) == 101


def test_validation_failure_preserves_both_inputs(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream(101))
    before = {
        path: (checkout / path).read_bytes()
        for path in (updater.SCHEMA_PATH, updater.PROVENANCE_PATH)
    }
    updater.validate_candidate.side_effect = subprocess.CalledProcessError(1, ["pytest"])
    assert updater.main(["--apply"]) == 1
    for path, content in before.items():
        assert (checkout / path).read_bytes() == content


@pytest.mark.parametrize(
    "candidate", [upstream(99), upstream().replace("// LAYER 100", ""), "<html>unavailable</html>"]
)
def test_rejects_downgrades_and_malformed_responses(checkout, monkeypatch, candidate):
    mock_sources(monkeypatch, candidate)
    assert updater.main(["--apply"]) == 1
    updater.validate_candidate.assert_not_called()


def test_disagreement_blocks_adoption_and_is_reported(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream(101), upstream(101, "example#1234 value:bytes = Example;"))
    report = checkout / "report.md"
    assert updater.main(["--apply", "--report", str(report)]) == 1
    assert "disagreements: ['example']" in report.read_text()
    updater.validate_candidate.assert_not_called()


def test_missing_tdlib_declaration_blocks_adoption(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream(101), upstream(101, "another#4567 = Example;"))
    assert updater.main(["--apply"]) == 1
    updater.validate_candidate.assert_not_called()


def test_network_failure_preserves_inputs(checkout, monkeypatch):
    fetch = Mock(side_effect=requests.Timeout("upstream timed out"))
    monkeypatch.setattr(updater, "fetch_source", fetch)
    assert updater.main(["--apply"]) == 1
    assert updater.get_layer((checkout / updater.SCHEMA_PATH).read_text()) == 100


def test_offline_validation_never_fetches(checkout, monkeypatch):
    fetch = Mock(side_effect=AssertionError("offline validation accessed the network"))
    monkeypatch.setattr(updater, "fetch_source", fetch)
    assert updater.main(["--validate"]) == 0
    fetch.assert_not_called()
    updater.validate_candidate.assert_called_once_with(checkout, {})


def test_changed_local_schema_fails_provenance_validation(checkout):
    (checkout / updater.SCHEMA_PATH).write_text(updater.normalize_schema(upstream(101)))
    assert updater.main(["--validate"]) == 1
    updater.validate_candidate.assert_not_called()


@pytest.mark.parametrize(
    "suffix", ["example#1234 value:int = Example;", "another#1234 = Example;"]
)
def test_duplicate_names_and_ids_are_rejected(suffix):
    with pytest.raises(ValueError, match="Duplicate"):
        updater.normalize_schema(upstream(declaration=f"example#1234 = Example;\n{suffix}"))


def test_normalization_keeps_one_section_and_comments_only_manual_types():
    schema = updater.normalize_schema("---types---\n" + upstream())
    assert schema.count("---types---") == 1
    assert schema.endswith("// LAYER 100\n")
    assert "boolTrue" not in updater.definitions(schema)
    assert updater.normalize_schema("---types---\n" + upstream()) == schema


def test_fetch_uses_immutable_commit_and_timeout(monkeypatch):
    commit = "b" * 40
    metadata = Mock()
    metadata.json.return_value = {"sha": commit}
    content = Mock(content=upstream().encode())
    get = Mock(side_effect=[metadata, content])
    monkeypatch.setattr(updater.requests, "get", get)
    schema, source = updater.fetch_source(updater.DESKTOP_REPO, updater.DESKTOP_PATH, "dev")
    assert schema == upstream()
    assert source["revision"] == commit
    assert f"/{commit}/" in get.call_args_list[1].args[0]
    assert all(call.kwargs["timeout"] == 30 for call in get.call_args_list)


def test_changed_manual_primitive_is_rejected():
    with pytest.raises(ValueError, match="basic types changed"):
        updater.normalize_schema(upstream().replace("boolTrue#997275b5", "boolTrue#997275b6"))


def test_validation_timeout_preserves_inputs(checkout, monkeypatch):
    mock_sources(monkeypatch, upstream(101))
    updater.validate_candidate.side_effect = subprocess.TimeoutExpired("pytest", 300)
    assert updater.main(["--apply"]) == 1
    assert updater.get_layer((checkout / updater.SCHEMA_PATH).read_text()) == 100
