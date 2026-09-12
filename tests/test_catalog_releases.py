"""Release gates and immutable inventory, using synthetic review records only."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
import test_local as fixture
from sci_ai_verifier.catalog_release import build, install, validate
from sci_ai_verifier.common import Fault, canonical, digest
from sci_ai_verifier.local_catalog import export_bundle, sync_catalogs
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.local import pin_candidate, retired_candidates
from sci_ai_verifier.storage import Store


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.h=fixture.LocalTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.key=self.h.ready()
        self.raw=export_bundle(self.h.runtime.store,[self.key],authorization="Synthetic fixture redistribution permission, not a real review.")
        self.settings=load_configuration()
        self.store=Store(self.h.base/"release-consumer")
        self.metadata={"catalog_id":"synthetic-fixture","version":"1.0.0","minimum_runtime":"0.7.0","maximum_runtime_exclusive":"0.8.0"}
        self.review={"candidate_ref":self.key,"decision":"approved_for_catalog","reviewer":"Synthetic fixture",
                     "reviewed_at":"2026-09-12","provenance":"Unit test only, no scientific authority.","independent":True,
                     "scope":"Fixture scope","coverage":"Fixture cases","uncertainty":"Not real evidence","redistribution":"Synthetic permitted bytes"}

    def release(self,**kwargs):
        return build(self.store,self.raw,self.settings,self.metadata,[self.review],approved=True,**kwargs)

    def test_promotion_requires_explicit_action_and_complete_independent_review(self):
        with self.assertRaises(Fault):
            build(self.store,self.raw,self.settings,self.metadata,[self.review])
        for reviews in ([],[self.review,self.review],[{**self.review,"independent":False}],[{**self.review,"candidate_ref":[]} ]):
            with self.assertRaises(Fault):
                build(self.store,self.raw,self.settings,self.metadata,reviews,approved=True)
        receipt=install(self.store,self.release(),self.settings)
        self.assertEqual(receipt["candidate_refs"],[self.key])
        self.assertFalse(receipt["scientific_approval_imported"])
        self.assertEqual(self.store.get_json(receipt["requalification_refs"][0])["status"],"qualified_local")

    def test_changed_bundle_and_incompatible_runtime_fail(self):
        release=json.loads(self.release())
        release["bundle"]["authorization"]="Changed permission after review."
        with self.assertRaises(Fault):
            validate(canonical(release))
        release=json.loads(self.release())
        release["minimum_runtime"]="0.8.0"
        release["maximum_runtime_exclusive"]="0.9.0"
        with self.assertRaises(Fault) as caught:
            install(self.store,canonical(release),self.settings)
        self.assertEqual(caught.exception.code,"catalog_incompatible")

    def test_update_requires_increasing_version_and_retains_previous_inventory(self):
        first=self.release()
        with self.assertRaises(Fault):
            self.release(previous_raw=first)
        self.metadata["version"]="1.1.0"
        self.review["decision"]="retired"
        second=self.release(previous_raw=first)
        self.assertEqual(validate(second)["previous_release_sha256"],digest(first))
        self.assertEqual(install(self.store,second,self.settings)["retired_candidate_refs"],[self.key])
        self.metadata["catalog_id"]="another-catalog"
        with self.assertRaises(Fault):
            self.release(previous_raw=first)

    def test_offline_exact_cache_retirement_and_existing_run_pins(self):
        first=self.release()
        path=self.h.base/"catalog.json"
        path.write_bytes(first)
        self.settings["catalogs"]=[{"location":str(path),"sha256":digest(first)}]
        first_receipts=sync_catalogs(self.store,self.settings)
        old={"local_catalog_ref":self.store.put_json(first_receipts),"objects":[]}
        self.metadata["version"]="1.1.0"
        self.review["decision"]="retired"
        second=self.release(previous_raw=first)
        path.write_bytes(second)
        self.settings["catalogs"][0]["sha256"]=digest(second)
        receipts=sync_catalogs(self.store,self.settings)
        current={"local_catalog_ref":self.store.put_json(receipts),"objects":[]}
        path.unlink()
        with patch("sci_ai_verifier.local_catalog.fetch_bytes",side_effect=AssertionError("Offline cache must not fetch")):
            offline=sync_catalogs(self.store,self.settings)
            self.assertEqual(offline[0]["release_sha256"],receipts[0]["release_sha256"])
            self.assertEqual(offline[0]["retired_candidate_refs"],[self.key])
            self.assertEqual(self.store.get_json(offline[0]["requalification_refs"][0])["status"],"qualified_local")
        self.assertEqual(retired_candidates(self.store,old),set())
        self.assertEqual(retired_candidates(self.store,current),{self.key})
        pin_candidate(self.store,old,self.key)
        with self.assertRaises(Fault) as caught:
            pin_candidate(self.store,current,self.key)
        self.assertEqual(caught.exception.code,"candidate_retired")

    def test_conflicting_configured_releases_fail(self):
        first=self.release()
        a=self.h.base/"a.json"
        a.write_bytes(first)
        self.metadata["version"]="1.1.0"
        second=self.release(previous_raw=first)
        b=self.h.base/"b.json"
        b.write_bytes(second)
        self.settings["catalogs"]=[{"location":str(a),"sha256":digest(first)},{"location":str(b),"sha256":digest(second)}]
        with self.assertRaises(Fault) as caught:
            sync_catalogs(self.store,self.settings)
        self.assertEqual(caught.exception.code,"catalog_release_conflict")


if __name__=="__main__":
    unittest.main()
