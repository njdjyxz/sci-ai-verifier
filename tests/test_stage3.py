"""Routing acceptance uses synthetic approvals, never scientific validation."""

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import test_stage2 as stage2
from test_stage2 import INSTRUCTIONS, ROOT
from sci_ai_verifier.agent import Runtime
from sci_ai_verifier.catalog import (
    ASSETS, MAX_BYTES, NoRedirect, fetch_release, manifest_for, read_release, verify,
)
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.storage import Store, atomic_write

SCOPE = "neutral CHNOPS formulas"


def fixture_assets():
    common = {"version": "test-1", "provenance": "Synthetic test approval, not scientific review"}
    claim_type = {**common, "id": "formula.mass", "status": "approved", "name": "Formula mass",
                  "definition": "Calculate a specified isotopic mass from atom counts.", "inputs": "formula",
                  "outputs": "mass", "boundaries": "Explicit isotope convention and scope required."}
    execution = {"input_interface": "formula-v1", "output_interface": "mass-v1",
                 "configuration_contract": "bounded-fixture-v1", "scoring_contract": "fixture-score-v1",
                 "aggregation_contract": "fixture-all-v1", "trial_grade_policy": "fixture-policy-v1"}
    evaluator = {**common, **execution, "id": "mass.evaluator", "status": "validated",
                 "claim_type_ids": ["formula.mass"], "scopes": [SCOPE], "grades": ["A", "B", "C"],
                 "limitations": ["Synthetic lookup fixture"], "resources": []}
    documentary = {**common, "id": "mass.documentary", "status": "approved",
                   "claim_type_ids": ["formula.mass"], "scopes": [SCOPE], "grades": ["D"],
                   "rubric": "fixture-rubric-v1", "assessor_contract": "independent-human-fixture",
                   "limitations": ["Synthetic documentary fixture"], "resources": []}
    runner = {**common, **execution, "id": "formula.runner", "status": "validated"}
    return {"claim_types": {"schema_version": 1, "revision": 1, "claim_types": [claim_type]},
            "evaluators": {"schema_version": 2, "revision": 1, "evaluators": [evaluator],
                           "harnesses": [documentary]},
            "subject_runners": {"schema_version": 1, "revision": 1, "subject_runners": [runner]}}


def write_release(directory, assets=None, version="fixture-1"):
    assets = fixture_assets() if assets is None else assets
    raw = {name: canonical(value) for name, value in assets.items()}
    manifest = canonical(manifest_for(raw, version, "Synthetic acceptance fixtures; no scientific approval"))
    atomic_write(directory / "manifest.json", manifest)
    for name, value in raw.items():
        atomic_write(directory / (name + ".json"), value)
    return manifest, raw


class Stage3Tests(unittest.TestCase):
    start = stage2.Stage2Tests.start
    call = stage2.Stage2Tests.call
    load = stage2.Stage2Tests.load
    parent_args = stage2.Stage2Tests.parent_args

    def setUp(self):
        parent = ROOT / ".verifier" / "test-work"
        parent.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix="stage3-", dir=parent)
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.sources = self.base / "sources"
        self.skill = self.sources / "skill"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text(
            "The skill computes mass for neutral CHNOPS formulas.\nThe skill validates formula syntax.\n",
            encoding="utf-8")
        self.release = self.base / "release"
        write_release(self.release)
        self.runtime = Runtime(self.base / "data", self.sources, INSTRUCTIONS, profile="stage3",
                               release_directory=self.release)

    def extracted(self, count=1, scope=SCOPE):
        loaded = self.load()
        quotes = ["The skill computes mass for neutral CHNOPS formulas.", "The skill validates formula syntax."]
        claims = [{"statement": quote, "scope": scope, "expected_behavior": "Not specified",
                   "source_path": "SKILL.md", "source_quote": quote, "report_note": ""}
                  for quote in quotes[:count]]
        result = self.call(loaded, "commit_claim_manifest", **self.parent_args(loaded), claims=claims)
        self.assertEqual(result["status"], "ok", result)
        return result["data"]

    def indexed(self, count=1, scope=SCOPE):
        extracted = self.extracted(count, scope)
        result = self.call(extracted, "list_claim_types")
        self.assertEqual(result["status"], "ok", result)
        return result["data"], extracted["manifest"]

    def assigned(self, count=1, scope=SCOPE):
        indexed, manifest = self.indexed(count, scope)
        items = [{"claim_id": claim["claim_id"], "claim_type_id": "formula.mass", "proposal": {},
                  "report_note": "synthetic routing acceptance"} for claim in manifest["claims"]]
        result = self.call(indexed, "commit_claim_type_assignments", manifest_id=manifest["id"],
                           index_digest=indexed["index_digest"], assignments=items)
        self.assertEqual(result["status"], "ok", result)
        return result["data"], manifest

    def selection(self, state, route, scope=SCOPE):
        return self.call(state, "find_registered_evaluators", claim_id=route["claim_id"],
                         route_id=route["route_id"], scope=scope, intended_grade="A")

    def test_submission_to_pinned_selection_and_recovery(self):
        state, manifest = self.assigned()
        result = self.selection(state, state["routing"]["routes"][0])
        self.assertEqual(result["status"], "ok", result)
        data = result["data"]
        self.assertEqual(data["outcome"], "registered_evaluator_available")
        self.assertEqual(data["run_state"], "stage3_complete")
        self.assertFalse(data["verification_complete"])
        self.assertEqual(data["next_legal_tools"], [])
        self.assertEqual(data["selection"]["matches"][0]["subject_runner"]["id"], "formula.runner")
        directory = self.runtime.store.run_dir(data["run_id"])
        for name in ("routing.json", "catalog-lock.json"):
            (directory / name).unlink()
        resumed = self.runtime.call("resume_verifier_run", {"run_id": data["run_id"]})
        self.assertEqual(resumed["data"]["routing"]["selections"][0], data["selection"])
        self.assertTrue((directory / "routing.json").is_file())
        self.assertTrue((directory / "catalog-lock.json").is_file())
        self.assertNotIn("evidence_grade", data["selection"])
        self.assertFalse(list(directory.glob("*report*")))

    def test_zero_claims_close_without_lookup(self):
        data = self.extracted(0)
        self.assertEqual(data["run_state"], "stage3_complete")
        self.assertEqual(data["next_legal_tools"], [])
        self.assertFalse(data["verification_complete"])

    def test_assignments_require_index_delivery(self):
        data = self.extracted()
        result = self.call(data, "commit_claim_type_assignments", manifest_id=data["manifest"]["id"],
                           index_digest="0" * 64, assignments=[])
        self.assertEqual(result["error"]["code"], "index_not_read")

    def test_assignment_failures_do_not_partially_commit(self):
        for failure in ("missing", "duplicate", "unknown", "stale", "incomplete_proposal"):
            with self.subTest(failure=failure):
                data, manifest = self.indexed()
                args = {"manifest_id": manifest["id"], "index_digest": data["index_digest"],
                        "assignments": [{"claim_id": manifest["claims"][0]["claim_id"],
                                         "claim_type_id": "formula.mass", "proposal": {}, "report_note": ""}]}
                if failure == "missing":
                    args["assignments"] = []
                elif failure == "duplicate":
                    args["assignments"] *= 2
                elif failure == "unknown":
                    args["assignments"][0]["claim_type_id"] = "unknown"
                elif failure == "stale":
                    args["index_digest"] = "0" * 64
                else:
                    args["assignments"][0].update(claim_type_id="", proposal={"name": "incomplete"})
                result = self.call(data, "commit_claim_type_assignments", **args)
                self.assertEqual(result["status"], "retryable", result)
                state, _ = self.runtime.store.read(data["run_id"])
                self.assertEqual(state["run_state"], "claims_ready")
                self.assertEqual(self.runtime.store.get_json(state["routing_ref"])["routes"], [])

    def test_proposals_stay_local_and_do_not_authorize_capabilities(self):
        data, manifest = self.indexed()
        proposal = dict.fromkeys(("name", "definition", "inputs", "outputs", "boundaries"), "new type")
        result = self.call(data, "commit_claim_type_assignments", manifest_id=manifest["id"],
                           index_digest=data["index_digest"], assignments=[{
                               "claim_id": manifest["claims"][0]["claim_id"], "claim_type_id": "",
                               "proposal": proposal, "report_note": ""}])
        state = result["data"]
        selected = self.selection(state, state["routing"]["routes"][0])
        self.assertEqual(selected["data"]["outcome"], "implementation_required")
        projected = self.runtime.store.root / "registry" / "claim-types" / f'{data["run_id"]}.json'
        self.assertEqual(json.loads(projected.read_bytes())["claim_types"][0]["status"], "provisional")
        next_data, _ = self.indexed()
        self.assertEqual(len(next_data["claim_types"]), 1)

    def test_strongest_grade_and_registered_preference(self):
        assets = fixture_assets()
        generic = deepcopy(assets["evaluators"]["evaluators"][0])
        generic.update(id="generic.mass", status="approved")
        assets["evaluators"]["harnesses"].append(generic)
        write_release(self.release, assets)
        state, _ = self.assigned()
        selected = self.selection(state, state["routing"]["routes"][0])["data"]
        self.assertEqual(selected["selection"]["matches"][0]["capability"]["id"], "mass.evaluator")
        assets["evaluators"]["evaluators"][0]["grades"] = ["B", "C"]
        write_release(self.release, assets)
        state, _ = self.assigned()
        selected = self.selection(state, state["routing"]["routes"][0])["data"]
        self.assertEqual(selected["outcome"], "generic_harness_available")
        self.assertEqual(selected["selection"]["resolved_grade"], "A")

    def test_documentary_fallback_never_requires_runner(self):
        assets = fixture_assets()
        assets["subject_runners"]["subject_runners"] = []
        write_release(self.release, assets)
        state, _ = self.assigned()
        data = self.selection(state, state["routing"]["routes"][0])["data"]
        self.assertEqual(data["outcome"], "lower_grade_available")
        self.assertEqual(data["selection"]["resolved_grade"], "D")
        self.assertEqual(data["selection"]["matches"][0]["subject_runner"], "not_applicable")

    def test_lower_execution_grade_and_interface_mismatch(self):
        assets = fixture_assets()
        assets["evaluators"]["evaluators"][0]["grades"] = ["B", "C"]
        write_release(self.release, assets)
        state, _ = self.assigned()
        selected = self.selection(state, state["routing"]["routes"][0])["data"]
        self.assertEqual(selected["outcome"], "lower_grade_available")
        self.assertEqual(selected["selection"]["resolved_grade"], "B")
        assets["subject_runners"]["subject_runners"][0]["output_interface"] = "other-output"
        write_release(self.release, assets)
        state, _ = self.assigned()
        selected = self.selection(state, state["routing"]["routes"][0])["data"]
        self.assertEqual(selected["selection"]["resolved_grade"], "D")

    def test_large_pair_cross_product_is_bounded_and_ordered(self):
        assets = fixture_assets()
        original = assets["subject_runners"]["subject_runners"][0]
        assets["subject_runners"]["subject_runners"] = [
            {**original, "id": f"runner-{i:03}"} for i in reversed(range(25))]
        write_release(self.release, assets)
        state, _ = self.assigned()
        selected = self.selection(state, state["routing"]["routes"][0])["data"]["selection"]
        self.assertEqual(selected["compatible_pair_count"], 25)
        self.assertTrue(selected["matches_truncated"])
        self.assertEqual(len(selected["matches"]), 16)
        self.assertEqual(selected["matches"][0]["subject_runner"]["id"], "runner-000")
        self.assertEqual(len(selected["capability_contracts"]), 1)

    def test_incompatible_release_records_failure_before_source_loading(self):
        manifest = json.loads((self.release / "manifest.json").read_bytes())
        manifest["runtime_interface"] = 99
        atomic_write(self.release / "manifest.json", canonical(manifest))
        result = self.runtime.call("start_verifier_run", {"source_path": str(self.skill)})
        self.assertEqual(result["error"]["code"], "catalog_incompatible")
        state, _ = self.runtime.store.read(result["error"]["run_id"])
        self.assertEqual(state["run_state"], "incomplete")
        self.assertIsNone(state["source_ref"])
        self.assertIsNotNone(result["error"]["operational_outcome_id"])

    def test_configured_catalog_is_pinned_without_network_and_never_silently_replaced(self):
        manifest, raw = write_release(self.release)
        def transport(path, commit, timeout):
            return manifest if path == "manifest.json" else raw[path.removesuffix(".json")]
        expected = digest(manifest)
        fetch_release(self.runtime.store, "a" * 40, expected, transport=transport)
        self.runtime = Runtime(self.base / "data", self.sources, INSTRUCTIONS, profile="stage3")
        with patch("sci_ai_verifier.catalog.download", side_effect=AssertionError("tool must not download")):
            state, _ = self.assigned()
        cached = self.runtime.store.root / "catalogs" / expected
        (cached / "manifest.json").unlink()
        selected = self.selection(state, state["routing"]["routes"][0])["data"]
        self.assertEqual(selected["outcome"], "registered_evaluator_available")
        new = self.runtime.call("start_verifier_run", {"source_path": str(self.skill)})
        self.assertEqual(new["error"]["code"], "catalog_unavailable")

    def test_type_mismatch_does_not_match_identical_scope(self):
        assets = fixture_assets()
        other = {**assets["claim_types"]["claim_types"][0], "id": "other.type"}
        assets["claim_types"]["claim_types"].append(other)
        for capability in [*assets["evaluators"]["evaluators"], *assets["evaluators"]["harnesses"]]:
            capability["claim_type_ids"] = ["other.type"]
        write_release(self.release, assets)
        state, _ = self.assigned()
        result = self.selection(state, state["routing"]["routes"][0])
        self.assertEqual(result["data"]["outcome"], "implementation_required")

    def test_no_runner_and_no_implementation_have_distinct_outcomes(self):
        for expected in ("subject_runner_unavailable", "implementation_required"):
            with self.subTest(expected=expected):
                assets = fixture_assets()
                assets["subject_runners"]["subject_runners"] = []
                assets["evaluators"]["harnesses"] = []
                if expected == "implementation_required":
                    assets["evaluators"]["evaluators"] = []
                write_release(self.release, assets)
                state, _ = self.assigned(2)
                first, second = state["routing"]["routes"]
                data = self.selection(state, first)["data"]
                self.assertEqual(data["outcome"], expected)
                self.assertEqual(data["run_state"], "active")
                self.assertEqual(data["claim_states"][second["claim_id"]], "capability_selection")
                outcome_id = data["selection"]["operational_outcome_id"]
                outcome = json.loads((self.runtime.store.run_dir(data["run_id"]) /
                                      "operational-outcomes" / (outcome_id + ".json")).read_bytes())
                self.assertIsNone(outcome["scientific_status"])
                self.assertIsNone(outcome["evidence_grade"])
                self.assertEqual(outcome["scope"], "claim")
                final = self.selection(data, second)["data"]
                self.assertEqual(final["run_state"], "stage3_complete")

    def test_scope_is_not_widened_and_provisional_entries_are_skipped(self):
        state, _ = self.assigned(scope="Not specified")
        route = state["routing"]["routes"][0]
        wrong = self.selection(state, route)
        self.assertEqual(wrong["error"]["code"], "selection_parameters_changed")
        selected = self.selection(wrong["error"], route, "Not specified")
        self.assertEqual(selected["data"]["outcome"], "implementation_required")
        assets = fixture_assets()
        for entry in [*assets["evaluators"]["evaluators"], *assets["evaluators"]["harnesses"]]:
            entry["status"] = "provisional"
        write_release(self.release, assets)
        state, _ = self.assigned()
        self.assertEqual(self.selection(state, state["routing"]["routes"][0])["data"]["outcome"],
                         "implementation_required")

    def test_repeat_selection_and_stale_token_are_illegal(self):
        state, _ = self.assigned(2)
        first, second = state["routing"]["routes"]
        data = self.selection(state, first)["data"]
        rejected = self.selection(data, first)
        self.assertEqual(rejected["error"]["code"], "illegal_transition")
        stale = self.selection(data, second)
        self.assertEqual(stale["error"]["code"], "illegal_transition")

    def test_release_and_source_updates_cannot_change_active_run(self):
        state, _ = self.assigned()
        (self.skill / "SKILL.md").write_text("changed", encoding="utf-8")
        (self.release / "evaluators.json").write_text("corrupt", encoding="utf-8")
        resumed = self.runtime.call("resume_verifier_run", {"run_id": state["run_id"]})["data"]
        selected = self.selection(resumed, state["routing"]["routes"][0])["data"]
        self.assertEqual(selected["outcome"], "registered_evaluator_available")
        failed = self.runtime.call("start_verifier_run", {"source_path": str(self.skill)})
        self.assertEqual(failed["status"], "fatal")
        self.assertEqual(failed["error"]["code"], "catalog_integrity")
        self.assertIsNotNone(failed["error"]["operational_outcome_id"])

    def test_stage3_context_includes_routing_and_grounding(self):
        data = self.start()
        blocks = {item["identity"]: item["content"] for item in data["context_blocks"]}
        self.assertIn("## Stage 3 profile", blocks["references/workflow.md"])
        self.assertIn("## Routing tools", blocks["references/tool-contracts.md"])
        self.assertIn("## Routing artifact", blocks["references/artifact-contracts.md"])
        self.assertIn("Do not add isotope conventions", blocks["SKILL.md"])
        self.assertLess(len(canonical(data)), 145000)

    def test_stage2_run_can_resume_in_stage3_host_without_migration(self):
        self.runtime = Runtime(self.base / "data", self.sources, INSTRUCTIONS)
        state = self.extracted()
        # Reproduce the prior writer's committed shape, including its recorded version.
        directory = self.runtime.store.run_dir(state["run_id"])
        previous = None
        for path in sorted((directory / "events").glob("*.json")):
            event = json.loads(path.read_bytes())
            event.pop("digest")
            event["state_after"]["implementation_version"] = "0.2.0"
            event["implementation_version"] = "0.2.0"
            event["previous_digest"] = previous
            event["digest"] = digest(canonical(event))
            previous = event["digest"]
            atomic_write(path, canonical(event))
        prior_bytes = {p: p.read_bytes() for p in (directory / "events").glob("*.json")}
        host = Runtime(self.base / "data", self.sources, INSTRUCTIONS, profile="stage3",
                       release_directory=self.release)
        result = host.call("resume_verifier_run", {"run_id": state["run_id"]})
        self.assertEqual(result["data"]["run_state"], "stage2_complete")
        self.assertEqual(result["data"]["profile"], "stage2")
        self.assertEqual(prior_bytes, {p: p.read_bytes() for p in prior_bytes})


class CatalogTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=ROOT / ".verifier", prefix="catalog-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.manifest, self.raw = write_release(self.base / "release")
        self.store = Store(self.base / "data")
        self.expected = digest(self.manifest)
        self.commit = "a" * 40

    def transport(self, path, commit, timeout):
        self.assertEqual(commit, self.commit)
        self.assertLessEqual(timeout, 10)
        return self.manifest if path == "manifest.json" else self.raw[path.removesuffix(".json")]

    def test_exact_download_and_verified_offline_activation(self):
        selection = fetch_release(self.store, self.commit, self.expected, transport=self.transport)
        self.assertEqual(selection["manifest_sha256"], self.expected)
        with patch("sci_ai_verifier.catalog.download", side_effect=AssertionError("offline network")):
            offline = fetch_release(self.store, self.commit, self.expected, offline=True)
        self.assertEqual(selection, offline)

    def test_unavailable_or_corrupt_download_preserves_selection(self):
        fetch_release(self.store, self.commit, self.expected, transport=self.transport)
        config = self.store.root / "catalog-selection.json"
        before = config.read_bytes()
        for transport in (lambda *a: b"wrong", lambda *a: (_ for _ in ()).throw(OSError("unavailable"))):
            with self.assertRaises(Fault):
                fetch_release(self.store, self.commit, self.expected, transport=transport)
            self.assertEqual(config.read_bytes(), before)

    def test_offline_requires_exact_complete_uncorrupted_cache(self):
        with self.assertRaises(Fault) as caught:
            fetch_release(self.store, self.commit, self.expected, offline=True)
        self.assertEqual(caught.exception.code, "catalog_unavailable")
        fetch_release(self.store, self.commit, self.expected, transport=self.transport)
        with self.assertRaises(Fault):
            fetch_release(self.store, "b" * 40, self.expected, offline=True)
        cached = self.store.root / "catalogs" / self.expected / "evaluators.json"
        cached.write_bytes(b"changed")
        with self.assertRaises(Fault) as caught:
            fetch_release(self.store, self.commit, self.expected, offline=True)
        self.assertEqual(caught.exception.code, "catalog_integrity")

    def test_rejects_schema_interface_digest_and_path_changes(self):
        for field, value in (("schema_version", True), ("runtime_interface", 9), ("skill_interface", 0)):
            manifest = json.loads(self.manifest)
            manifest[field] = value
            with self.assertRaises(Fault) as caught:
                verify(canonical(manifest), self.raw)
            self.assertEqual(caught.exception.code, "catalog_incompatible")
        for path in ("../escape.json", "https://other.example/a", "C:/outside.json"):
            manifest = json.loads(self.manifest)
            manifest["assets"]["claim_types"]["path"] = path
            with self.assertRaises(Fault):
                verify(canonical(manifest), self.raw)
        with self.assertRaises(Fault):
            verify(self.manifest, self.raw, "0" * 64)

    def test_rejects_duplicates_unknown_references_and_malformed_assets(self):
        for failure in ("duplicate", "unknown_type", "bad_resource", "boolean_revision", "bad_schema", "long_id"):
            assets = fixture_assets()
            if failure == "duplicate":
                assets["claim_types"]["claim_types"] *= 2
            elif failure == "unknown_type":
                assets["evaluators"]["evaluators"][0]["claim_type_ids"] = ["unknown"]
            elif failure == "bad_resource":
                assets["evaluators"]["evaluators"][0]["resources"] = [{"id": "data", "version": "1", "sha256": "bad"}]
            elif failure == "boolean_revision":
                assets["claim_types"]["revision"] = True
            elif failure == "long_id":
                assets["claim_types"]["claim_types"][0]["id"] = "x" * 161
            else:
                assets["evaluators"]["schema_version"] = 9
            manifest, raw = write_release(self.base / failure, assets)
            with self.assertRaises(Fault):
                verify(manifest, raw)

    def test_nonfinite_duplicate_keys_oversize_and_mutable_refs_rejected(self):
        from sci_ai_verifier.catalog import decode
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":1e999}', b" " * (MAX_BYTES + 1), b"[" * 2000):
            with self.assertRaises(Fault):
                decode(raw)
        with self.assertRaises(Fault):
            decode(b"[" * 33 + b"0" + b"]" * 33)
        for commit in ("main", "v1", "../escape", "b" * 41):
            with self.assertRaises(Fault):
                fetch_release(self.store, commit, self.expected, transport=self.transport)
        from urllib.error import URLError
        with self.assertRaises(URLError):
            NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://other.example")

    def test_expired_download_budget_never_activates(self):
        with patch("sci_ai_verifier.catalog.time.monotonic", side_effect=[0, 0, 31]):
            with self.assertRaises(Fault) as caught:
                fetch_release(self.store, self.commit, self.expected, transport=self.transport)
        self.assertEqual(caught.exception.code, "catalog_unavailable")
        self.assertFalse((self.store.root / "catalog-selection.json").exists())


if __name__ == "__main__":
    unittest.main()
