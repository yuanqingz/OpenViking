# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0

import pytest

from benchmark.vectordb_perf import run as benchmark


def query(index: int) -> benchmark.QueryCase:
    return benchmark.QueryCase(
        query_id=f"q{index}",
        vector=[float(index), 0.0],
        filter_path=f"viking://resources/bench/d{index}",
    )


class FakeBackend:
    def __init__(self) -> None:
        self.calls = 0

    async def search_in_tenant(self, **_kwargs):
        self.calls += 1
        return [{"id": f"result-{self.calls}"}]


async def test_run_search_with_warmup_separates_measured_events():
    backend = FakeBackend()

    warmup, measured, errors, quality = await benchmark.run_search_with_warmup(
        backend=backend,
        ctx=object(),
        phase="vector_search",
        queries=[query(0), query(1), query(2)],
        top_k=1,
        concurrency=2,
        warmup_queries=2,
        filtered=False,
    )

    assert backend.calls == 5
    assert [event.phase for event in warmup] == [
        "vector_search_cold",
        "vector_search_warmup",
    ]
    assert [event.phase for event in measured] == ["vector_search"] * 3
    assert errors == []
    assert quality["queries_with_ground_truth"] == 0


async def test_run_search_with_warmup_can_be_disabled():
    backend = FakeBackend()

    warmup, measured, errors, _ = await benchmark.run_search_with_warmup(
        backend=backend,
        ctx=object(),
        phase="filtered_vector_search",
        queries=[query(0), query(1)],
        top_k=1,
        concurrency=1,
        warmup_queries=0,
        filtered=False,
    )

    assert warmup == []
    assert len(measured) == 2
    assert backend.calls == 2
    assert errors == []


def test_parse_args_supports_profile_and_explicit_warmup_queries(tmp_path):
    standard = benchmark.parse_args(
        ["--profile", "standard", "--output-dir", str(tmp_path / "standard")]
    )
    disabled = benchmark.parse_args(
        ["--warmup-queries", "0", "--output-dir", str(tmp_path / "disabled")]
    )

    assert standard.warmup_queries == 5
    assert disabled.warmup_queries == 0


def test_filter_scope_sample_reports_actual_not_requested_selectivity():
    sample = benchmark.build_filter_scope_sample(
        filter_path="viking://resources/bench/synthetic/d0_0/d1_0",
        eligible_count=156,
        total_count=10_000,
        requested_selectivity=0.05,
    )

    assert sample["requested_selectivity"] == 0.05
    assert sample["actual_selectivity"] == 0.0156


def test_dependency_light_context_schema_has_required_vector_and_filter_fields():
    schema = benchmark.build_schema("context", 1024)
    fields = {field["FieldName"]: field for field in schema["Fields"]}

    assert schema["CollectionName"] == "context"
    assert fields["vector"] == {"FieldName": "vector", "FieldType": "vector", "Dim": 1024}
    assert fields["uri"]["FieldType"] == "path"
    assert {"uri", "account_id", "owner_user_id"}.issubset(schema["ScalarIndex"])


def test_vectordb_config_payload_ignores_unrelated_model_config(tmp_path):
    payload = benchmark.vectordb_config_payload(
        {
            "storage": {
                "workspace": str(tmp_path / "data"),
                "vectordb": {
                    "backend": "cuvs",
                    "name": "benchmark",
                    "cuvs": {"algorithm": "brute_force"},
                },
            },
            "embedding": {"dense": {"provider": "not-installed-for-this-benchmark"}},
            "vlm": {"provider": "not-installed-for-this-benchmark"},
        }
    )

    assert payload == {
        "backend": "cuvs",
        "name": "benchmark",
        "cuvs": {"algorithm": "brute_force"},
        "path": str((tmp_path / "data").resolve()),
    }


def test_vectordb_config_payload_rejects_non_object_storage():
    with pytest.raises(ValueError, match="storage config must be an object"):
        benchmark.vectordb_config_payload({"storage": []})
