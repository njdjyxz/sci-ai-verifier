"""Exercise the installable payload through real stdio, independent of app/model."""

import hashlib
import json
import queue
import subprocess
import sys
import tempfile
import threading
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class DesktopPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT / "scripts/build_desktop.py")],
                       cwd=ROOT, capture_output=True, check=True)

    def test_extracted_package_runs_full_stdio_flow(self):
        parent = ROOT / ".verifier" / "package-tests"
        parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=parent, prefix="desktop-") as temporary:
            base = Path(temporary)
            package = base / "package with spaces"
            with zipfile.ZipFile(ROOT / "dist/scientific-verifier-0.2.0.mcpb") as archive:
                self.assertIsNone(archive.testzip())
                for name in archive.namelist():
                    self.assertTrue((package / name).resolve().is_relative_to(package.resolve()))
                archive.extractall(package)
            manifest = json.loads((package / "manifest.json").read_bytes())
            values = {
                "${__dirname}": str(package),
                "${user_config.python_path}": sys.executable,
                "${user_config.data_directory}": str(base / "data"),
                "${user_config.submission_directory}": str(ROOT / "examples/submissions"),
            }
            def expand(value):
                for key, replacement in values.items():
                    value = value.replace(key, replacement)
                self.assertNotIn("${", value)
                return value
            config = manifest["server"]["mcp_config"]
            command = [expand(config["command"]), *map(expand, config["args"])]
            process = subprocess.Popen(command, cwd=base, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            responses = queue.Queue()
            reader = threading.Thread(target=lambda: self.read_lines(process.stdout, responses), daemon=True)
            reader.start()
            sequence = 0
            def request(method, params=None, notification=False):
                nonlocal sequence
                sequence += 1
                frame = {"jsonrpc": "2.0", "method": method}
                if not notification:
                    frame["id"] = sequence
                if params is not None:
                    frame["params"] = params
                process.stdin.write(json.dumps(frame).encode() + b"\n")
                process.stdin.flush()
                if notification:
                    return
                response = json.loads(responses.get(timeout=20))
                self.assertEqual(response["id"], sequence)
                self.assertNotIn("error", response, response)
                return response["result"]
            def call(name, arguments):
                result = request("tools/call", {"name": name, "arguments": arguments})
                content = json.loads(result["content"][0]["text"])
                self.assertEqual(content, result["structuredContent"])
                self.assertEqual(content["status"], "ok", content)
                return content["data"]
            try:
                initialized = request("initialize", {
                    "protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "scripted-package-acceptance", "version": "1"},
                })
                self.assertEqual(initialized["serverInfo"]["version"], "0.2.0")
                request("notifications/initialized", notification=True)
                listed = request("tools/list")
                self.assertEqual(len(listed["tools"]), 7)
                source = str(ROOT / "examples/submissions/reference-claim")
                created = call("start_verifier_run", {"source_path": source, "model_label": "scripted-no-model"})
                loaded = call("load_submitted_skill", {
                    "run_id": created["run_id"], "state_token": created["state_token"], "source_path": source,
                })
                parent_args = {"run_id": loaded["run_id"], "snapshot_id": loaded["snapshot"]["id"],
                               "snapshot_digest": loaded["snapshot"]["digest"]}
                read = call("read_snapshot_file", {
                    **parent_args, "state_token": loaded["state_token"], "path": "references/mass.md",
                })
                quote = "The skill calculates a molecule's monoisotopic mass from its molecular formula."
                finished = call("commit_claim_manifest", {
                    **parent_args, "state_token": read["state_token"], "claims": [{
                        "statement": quote, "scope": "Not specified", "expected_behavior": "Calculate mass.",
                        "source_path": "references/mass.md", "source_quote": quote, "report_note": "",
                    }],
                })
                self.assertEqual(finished["run_state"], "stage2_complete")
                self.assertFalse(finished["verification_complete"])
                data = json.loads(Path(finished["manifest_path"]).read_bytes())
                self.assertEqual(data["count"], 1)
                # Ensure no checkout source path is embedded into the executable bundle.
                self.assertTrue(Path(finished["manifest_path"]).is_relative_to(base / "data"))
            finally:
                process.stdin.close()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)
                reader.join(timeout=5)
                stderr = process.stderr.read()
                process.stdout.close()
                process.stderr.close()
            self.assertEqual(process.returncode, 0, stderr.decode(errors="replace"))
            self.assertEqual(stderr, b"")

    @staticmethod
    def read_lines(stream, destination):
        for line in iter(stream.readline, b""):
            destination.put(line)

    def test_archives_are_reproducible_and_skill_has_correct_root(self):
        before = json.loads((ROOT / "dist/checksums.json").read_bytes())
        subprocess.run([sys.executable, str(ROOT / "scripts/build_desktop.py")],
                       cwd=ROOT, capture_output=True, check=True)
        after = json.loads((ROOT / "dist/checksums.json").read_bytes())
        self.assertEqual(before, after)
        for record in after:
            path = ROOT / "dist" / record["file"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])
        with zipfile.ZipFile(ROOT / "dist/scientific-verifier-skill-0.2.0.zip") as archive:
            names = archive.namelist()
            self.assertIn("scientific-verifier/SKILL.md", names)
            self.assertTrue(all(n.startswith("scientific-verifier/") for n in names))
            self.assertTrue(all(n.endswith(".md") for n in names))


if __name__ == "__main__":
    unittest.main()
