"""Exercise the installable payload through real stdio, independent of app/model."""

import ast
import hashlib
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import tomllib
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
        self.check_stdio_flow(sys.executable)

    def check_stdio_flow(self, interpreter):
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
                "${user_config.python_path}": interpreter,
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
                # One complete JSON text result, not a duplicated structuredContent copy.
                self.assertEqual([block["type"] for block in result["content"]], ["text"])
                self.assertNotIn("structuredContent", result)
                content = json.loads(result["content"][0]["text"])
                self.assertEqual(content["status"], "ok", content)
                self.assertIs(result["isError"], False)
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

    def test_wire_protocol_matches_the_written_mcp_requirements(self):
        """Drive the server from the specification's stated rules, not from mcp.py's shape.

        Each assertion names the requirement it encodes, so a mistake shared between
        `mcp.py` and a client written beside it does not pass unnoticed. An external
        client is still better evidence; set VERIFIER_EXTERNAL_MCP_CLIENT to record one.
        """
        self.assertIsNone(os.environ.get("VERIFIER_EXTERNAL_MCP_CLIENT"),
                          "An external client command is configured; record its result in "
                          "desktop/APP-ACCEPTANCE.md rather than relying on this stand-in.")
        sys.path.insert(0, str(ROOT / "src"))
        from sci_ai_verifier.agent import Runtime
        from sci_ai_verifier.mcp import Server
        with tempfile.TemporaryDirectory() as workspace:
            server = Server(Runtime(Path(workspace), ROOT / "examples/submissions",
                                    ROOT / "skills/scientific-verifier"))
            # Lifecycle: the server replies with the requested version when it supports it.
            opened = server.handle({"jsonrpc": "2.0", "id": "s1", "method": "initialize",
                                    "params": {"protocolVersion": "2024-11-05", "capabilities": {}}})
            self.assertEqual(opened["result"]["protocolVersion"], "2024-11-05")
            # JSON-RPC: the response echoes the request id, including a string id.
            self.assertEqual(opened["id"], "s1")
            self.assertNotIn("error", opened)
            # Lifecycle: an unsupported version is answered with one the server does support.
            fresh = Server(Runtime(Path(workspace), ROOT / "examples/submissions",
                                   ROOT / "skills/scientific-verifier"))
            offered = fresh.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                    "params": {"protocolVersion": "1900-01-01", "capabilities": {}}})
            self.assertIn(offered["result"]["protocolVersion"], ("2025-06-18", "2025-03-26", "2024-11-05"))
            # JSON-RPC: a notification receives no response at all.
            self.assertIsNone(server.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
            # JSON-RPC: an unknown method is -32601.
            self.assertEqual(server.handle({"jsonrpc": "2.0", "id": 2,
                                            "method": "nonexistent/method"})["error"]["code"], -32601)
            # Tools: every declared tool has a name, a description and an object inputSchema.
            for tool in server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/list"})["result"]["tools"]:
                self.assertTrue(tool["name"] and tool["description"])
                self.assertEqual(tool["inputSchema"]["type"], "object")
            # Tools: a tool-side failure is a result with isError true, not a JSON-RPC error.
            failed = server.handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
                "name": "resume_verifier_run", "arguments": {"run_id": "not-a-run"}}})
            self.assertNotIn("error", failed)
            self.assertIs(failed["result"]["isError"], True)
            self.assertEqual(json.loads(failed["result"]["content"][0]["text"])["status"], "retryable")
            # Tools: an unknown tool name is also a tool result, never a protocol error.
            unknown = server.handle({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                     "params": {"name": "no_such_tool", "arguments": {}}})
            self.assertIs(unknown["result"]["isError"], True)

    def test_runtime_syntax_is_valid_on_the_declared_minimum_python(self):
        minimum = (3, 11)
        self.assertEqual(tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
                         ["project"]["requires-python"], ">=%d.%d" % minimum)
        for path in sorted((ROOT / "src/sci_ai_verifier").glob("*.py")) + [ROOT / "desktop/server.py"]:
            with self.subTest(module=path.name):
                # Rejects syntax newer than 3.11. It cannot see newer stdlib APIs, so the
                # skipped interpreter run below is still the evidence that matters.
                ast.parse(path.read_text(encoding="utf-8"), filename=str(path),
                          feature_version=minimum)

    def test_stdio_flow_under_the_declared_minimum_interpreter(self):
        interpreter = None
        candidates = [os.environ.get("VERIFIER_PY311"), "python3.11"]
        if sys.version_info[:2] == (3, 11):
            candidates.insert(0, sys.executable)
        if os.name == "nt" and shutil.which("py"):
            found = subprocess.run(["py", "-0p"], capture_output=True, text=True)
            for line in found.stdout.splitlines():
                if line.strip().startswith("-V:3.11"):
                    candidates.append(line.split(maxsplit=1)[-1].strip(" *"))
        for candidate in candidates:
            resolved = shutil.which(candidate) if candidate else None
            if resolved:
                version = subprocess.run(
                    [resolved, "-I", "-c", "import sys; print('.'.join(map(str, sys.version_info[:2])))"],
                    capture_output=True, text=True, timeout=10)
                if version.returncode == 0 and version.stdout.strip() == "3.11":
                    interpreter = resolved
                    break
        if interpreter is None:
            self.skipTest("No Python 3.11 interpreter is available; "
                          "the 3.11 floor in pyproject.toml and manifest.json is unverified.")
        self.check_stdio_flow(interpreter)

    def test_manifest_declares_exactly_the_published_tools(self):
        sys.path.insert(0, str(ROOT / "src"))
        from sci_ai_verifier.tools import DEFINITIONS
        manifest = json.loads((ROOT / "desktop/manifest.json").read_bytes())
        self.assertEqual([tool["name"] for tool in manifest["tools"]],
                         [tool["name"] for tool in DEFINITIONS])
        # The tool array is fixed and reviewable; nothing appears at runtime.
        self.assertIs(manifest["tools_generated"], False)

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
