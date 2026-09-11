"""Build deterministic, dependency-free MCPB and skill ZIP packages."""

import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "dist"


def archive(path, files):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, data)
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def main():
    OUTPUT.mkdir(exist_ok=True)
    files = {}
    for directory in ("src/sci_ai_verifier", "skills/scientific-verifier", "registry"):
        for path in sorted((ROOT / directory).rglob("*")):
            if path.suffix in {".py", ".md", ".json"} and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes().replace(b"\r\n", b"\n")
    files["server.py"] = (ROOT / "desktop/server.py").read_bytes().replace(b"\r\n", b"\n")
    for name in ("INSTALL.md", "STAGE3-INSTALL.md", "VERIFICATION-INSTALL.md", "DEMO-INSTALL.md", "APP-ACCEPTANCE.md"):
        data = (ROOT / "desktop" / name).read_bytes().replace(b"\r\n", b"\n")
        files[name] = data
        (OUTPUT / name).write_bytes(data)
    manifest = json.loads((ROOT / "desktop/manifest.json").read_text(encoding="utf-8"))
    files["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    version = manifest["version"]
    results = [archive(OUTPUT / f"scientific-verifier-{version}.mcpb", files)]
    skill_files = {key.removeprefix("skills/"): data for key, data in files.items()
                   if key.startswith("skills/")}
    results.append(archive(OUTPUT / f"scientific-verifier-skill-{version}.zip", skill_files))
    config = {"mcpServers": {"scientific-verifier": {
        "command": sys.executable,
        "args": ["-I", "-B", str(ROOT / "desktop/server.py"), "serve",
                 "--workspace", str(ROOT), "--source-root", str(ROOT / "examples/submissions"),
                 "--instructions", str(ROOT / "skills/scientific-verifier")],
    }}}
    (OUTPUT / "claude_desktop_config.example.json").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    (OUTPUT / "checksums.json").write_text(json.dumps(results, indent=2) + "\n",
                                          encoding="utf-8", newline="\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
