"""Build a source-complete local package without credentials or run artifacts."""

import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sci_ai_verifier import __version__
from sci_ai_verifier.ingest import SECRET_BYTES


def archive(path, files):
    """Write a deterministic zip: fixed timestamps and permissions, sorted names."""
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, data)
    return {"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size}


def main():
    files = {}
    directories = ("src", "skills", "registry", "catalog", "examples", "images", "scripts", "tests")
    for directory in directories:
        for path in sorted((ROOT / directory).rglob("*")):
            if path.is_file() and path.suffix in {".py", ".md", ".json", ".txt", ".toml", ""} and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = path.read_bytes().replace(b"\r\n", b"\n")
    for name in ("README.md", "INSTALL.md", "LOCAL-CONFIG.md", "DEVELOPMENT-PLAN.md", "DEVELOPMENT-LOG-ARCHIVE.md",
                 "CLAUDE.md", "pyproject.toml", ".gitattributes", ".gitignore"):
        files[name] = (ROOT / name).read_bytes().replace(b"\r\n", b"\n")
    if any(SECRET_BYTES.search(payload) for payload in files.values()):
        raise SystemExit("Credential-like bytes found; local package not built.")
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    result = archive(output / f"scientific-verifier-local-{__version__}.zip", files)
    (output / "local-checksums.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
