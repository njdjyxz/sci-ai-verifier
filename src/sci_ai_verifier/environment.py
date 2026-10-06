"""The packages a skill declares, installed before its run into an image for its subject trials only.

"Skill environment" in local-contract.md owns this mechanism, and "Packages a skill declares or imports" in
resource-policy.md owns the trust decision. `_build` below holds the only container of a
verification that has a network. Setup calls it after the model probe and before the run or its
planner exists; no tool reaches it, and nothing a model writes can add a package to it.
"""

import ast
import json
import re
import shlex
import sys
import tomllib
from urllib.parse import urlsplit
from uuid import uuid4

from . import __version__
from .common import Fault, canonical, digest, fenced_blocks, utc_now
from .execution_control import CURRENT
from .ingest import snapshot
from .local_candidates import safe_payload
from .sandbox import DockerSandbox
from .storage import Store

POLICY = "skill-environment-v1"
LABEL = "scientific-verifier.managed=true"
KEY_LABEL = "scientific-verifier.environment"
RECORD_LABEL = "scientific-verifier.environment-record"
WHEELS = "/sci-verifier-wheels"
MAX_REQUIREMENTS = 100
RESOLVE_TIMEOUT_SECONDS = 900
INSTALL_TIMEOUT_SECONDS = 900
MANIFEST_TIMEOUT_SECONDS = 120
# pip keeps each file it downloads in its temporary directory until it exits; that directory
# is on the volume, but pip itself and a large wheel's hashing still need more than a trial.
BUILD_MEMORY_MIB = 2048
PASS_THROUGH = {"verification_cancelled", "verification_timeout"}
INSTALLERS = {"pip", "setuptools", "wheel", "uv"}
REASONS = {"direct_reference", "editable_install", "environment_marker", "index_option", "installer_package",
           "invalid_pyproject", "invalid_requirement", "local_path", "requirements_file_outside_snapshot",
           "shell_syntax", "too_many_requirements", "unparseable_command", "unsupported_option"}
HARMLESS_OPTIONS = {"-U", "--upgrade", "-q", "-qq", "-qqq", "--quiet", "-v", "--verbose", "--no-cache-dir",
                    "--disable-pip-version-check", "--no-input", "--user", "--system", "--force-reinstall",
                    "--no-warn-script-location", "--prefer-binary"}
INDEX_OPTIONS = {"-i", "--index-url", "--extra-index-url", "-f", "--find-links", "--trusted-host",
                 "--index", "--default-index"}
INSTALL_PREFIXES = (["pip", "install"], ["pip3", "install"], ["python", "-m", "pip", "install"],
                    ["python3", "-m", "pip", "install"], ["py", "-m", "pip", "install"],
                    ["uv", "pip", "install"], ["%pip", "install"], ["!pip", "install"])
SPECIFIER = r"(?:===|==|!=|<=|>=|~=|<|>)\s*[A-Za-z0-9.*+!_-]+"
REQUIREMENT = re.compile(
    r"(?P<name>[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)\s*"
    r"(?:\[\s*(?P<extras>[A-Za-z0-9._-]+(?:\s*,\s*[A-Za-z0-9._-]+)*)\s*\])?\s*"
    r"(?P<spec>" + SPECIFIER + r"(?:\s*,\s*" + SPECIFIER + r")*)?")
WHEEL = re.compile(r"(?P<name>[A-Za-z0-9](?:[A-Za-z0-9._]*[A-Za-z0-9])?)-(?P<version>[A-Za-z0-9.!+_]+)"
                   r"(?:-\d[A-Za-z0-9_.]*)?-[A-Za-z0-9_.]+-[A-Za-z0-9_.]+-[A-Za-z0-9_.]+\.whl")
IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}")
SAFE_NAME = re.compile(r"[a-z0-9](?:[a-z0-9-]{0,98}[a-z0-9])?")
SAFE_VERSION = re.compile(r"[A-Za-z0-9.!+_-]{1,64}")
# The reviewed table of "Packages a skill declares or imports" in resource-policy.md, which owns it:
# the distribution a skill's undeclared import of each module is installed as. A module outside it
# is reported, never guessed, so a skill cannot make the verifier install a name of its choosing.
IMPORT_DISTRIBUTIONS = {
    "numpy": "numpy", "scipy": "scipy", "pandas": "pandas", "matplotlib": "matplotlib", "seaborn": "seaborn",
    "sklearn": "scikit-learn", "skimage": "scikit-image", "statsmodels": "statsmodels", "sympy": "sympy",
    "networkx": "networkx", "PIL": "pillow", "cv2": "opencv-python-headless", "yaml": "pyyaml",
    "Bio": "biopython", "rdkit": "rdkit", "lifelines": "lifelines", "sksurv": "scikit-survival",
    "openpyxl": "openpyxl", "h5py": "h5py", "pyarrow": "pyarrow", "xarray": "xarray", "anndata": "anndata",
    "scanpy": "scanpy", "joblib": "joblib", "requests": "requests", "tqdm": "tqdm"}
# The same section's reviewed table of commands: the distribution that provides each command a skill's
# shell code blocks run. ToolUniverse's `tu` computes its dose-response tools locally, so it runs offline.
COMMAND_DISTRIBUTIONS = {"tu": "tooluniverse"}
SHELL_INFO = {"", "bash", "sh", "shell", "zsh", "console"}

# The fixed programs the operator's image runs. Their digests are part of the cache key, so a
# change to either one rebuilds every environment rather than reusing one it did not make.
RESOLVE = r'''
import hashlib, json, os, subprocess, sys
index, dest, deadline = sys.argv[1:4]
os.makedirs(os.path.join(dest, ".tmp"), exist_ok=True)
try:
    done = subprocess.run([sys.executable, "-m", "pip", "download", "--isolated", "--no-input",
                           "--disable-pip-version-check", "--no-cache-dir", "--only-binary=:all:",
                           "--index-url", index, "--dest", dest, "--", *sys.argv[4:]],
                          capture_output=True, text=True, timeout=float(deadline))
except subprocess.TimeoutExpired:
    print(json.dumps({"error": "pip download reached its deadline"}))
    sys.exit(0)
if done.returncode:
    print(json.dumps({"error": (done.stderr or done.stdout)[-3000:]}))
    sys.exit(0)
wheels = []
for name in sorted(os.listdir(dest)):
    path = os.path.join(dest, name)
    if name == ".tmp" or not os.path.isfile(path):
        continue
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(block)
    wheels.append({"file": name, "sha256": hasher.hexdigest(), "bytes": os.path.getsize(path)})
print(json.dumps({"wheels": wheels}))
'''
INSTALL = r'''
import subprocess, sys
with open("/tmp/requirements.lock", "w") as handle:
    handle.write(sys.stdin.read())
done = subprocess.run([sys.executable, "-m", "pip", "install", "--isolated", "--no-input",
                       "--disable-pip-version-check", "--no-cache-dir", "--no-index", "--find-links",
                       sys.argv[1], "--only-binary=:all:", "--require-hashes", "-r", "/tmp/requirements.lock"],
                      capture_output=True, text=True)
if done.returncode:
    sys.stderr.write("pip install failed: " + (done.stderr or done.stdout)[-3000:])
    sys.exit(3)
check = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
if check.returncode:
    sys.stderr.write("pip check found conflicts: " + (check.stdout or check.stderr)[-3000:])
    sys.exit(4)
'''
MANIFEST = r'''
import importlib.metadata, importlib.util, json, shutil, sys
names, commands = json.loads(sys.argv[1]), json.loads(sys.argv[2])
found = sorted({(item.metadata["Name"] or "", item.version) for item in importlib.metadata.distributions()})
missing = sorted(name for name in names if name not in sys.stdlib_module_names and importlib.util.find_spec(name) is None)
print(json.dumps({"python": sys.version.split()[0], "distributions": [list(item) for item in found],
                  "imports_unavailable": missing,
                  "commands_unavailable": sorted(name for name in commands if shutil.which(name) is None)}))
'''
SCRIPT_DIGESTS = {"resolve": digest(RESOLVE.encode("utf-8")), "install": digest(INSTALL.encode("utf-8"))}


def normalized(name):
    """A project name as PEP 503 compares it."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_requirement(text):
    """(requirement, None) for a plain PEP 508 requirement, else (None, reason code)."""
    text = text.strip()
    if not text or len(text) > 200 or not text.isascii():
        return None, "invalid_requirement"
    if "://" in text or "@" in text:
        return None, "direct_reference"
    if ";" in text:
        return None, "environment_marker"
    if text[0] in "./~\\" or "/" in text or "\\" in text or text.lower().endswith((".whl", ".zip", ".tar.gz", ".tgz")):
        return None, "local_path"
    match = REQUIREMENT.fullmatch(text)
    if not match:
        return None, "invalid_requirement"
    name = normalized(match.group("name"))
    if name in INSTALLERS:
        return None, "installer_package"
    extras = sorted(normalized(item) for item in re.split(r"\s*,\s*", match.group("extras"))) if match.group("extras") else []
    specifiers = sorted(re.sub(r"\s+", "", match.group("spec")).split(",")) if match.group("spec") else []
    return {"requirement": name + ("[" + ",".join(extras) + "]" if extras else "") + ",".join(specifiers),
            "name": name}, None


def logical_lines(first, lines):
    """Lines joined across trailing backslashes, each with the number of its first physical line."""
    pending, begin = "", None
    for offset, line in enumerate(lines):
        begin = first + offset if begin is None else begin
        if line.rstrip().endswith("\\"):
            pending += line.rstrip()[:-1] + " "
            continue
        yield begin, pending + line
        pending, begin = "", None
    if begin is not None:
        yield begin, pending


def shell_commands(line):
    """The simple commands on one shell line, split at `&&`, `||`, `;`, `|` and `&`."""
    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    commands, current = [], []
    for word in lexer:
        if word and set(word) <= set(";&|"):
            commands.append(current)
            current = []
        else:
            current.append(word)
    return commands + [current]


class Declarations:
    """What a snapshot declares, found only in the snapshot's own bytes."""

    def __init__(self, files):
        self.files = {path for path, _ in files}
        self.requirements, self.rejected, self.notes = {}, [], []
        for path, text in files:
            name = path.rsplit("/", 1)[-1].lower()
            if path.lower().endswith(".md"):
                self.markdown(path, text)
            elif re.fullmatch(r"requirements[^/]*\.txt", name):
                self.requirements_file(path, text)
            elif name == "pyproject.toml":
                self.pyproject(path, text)

    def reject(self, source, text, reason):
        self.rejected.append({"source": source, "text": text.strip()[:300], "reason": reason})

    def accept(self, source, text):
        requirement, reason = parse_requirement(text)
        if reason:
            return reason
        entry = self.requirements.get(requirement["requirement"])
        if entry is None:
            if len(self.requirements) >= MAX_REQUIREMENTS:
                return "too_many_requirements"
            entry = self.requirements[requirement["requirement"]] = {**requirement, "sources": []}
        if source not in entry["sources"]:
            entry["sources"].append(source)
        return None

    def inside(self, relative, near):
        """Whether a `-r` path names a snapshot file, from the skill root or the declaring file."""
        base = near.rsplit("/", 1)[0] + "/" if "/" in near else ""
        return any(re.sub(r"^\./", "", candidate) in self.files for candidate in (relative, base + relative))

    def markdown(self, path, text):
        for first, _, body in fenced_blocks(text):
            for number, line in logical_lines(first, body):
                source = path + ":" + str(number)
                line = re.sub(r"^\s*\$\s+", "", line)
                if "install" not in line:
                    continue
                try:
                    commands = shell_commands(line)
                except ValueError:
                    if re.search(r"\bpip3?\s+install\b", line):
                        self.reject(source, line, "unparseable_command")
                    continue
                for words in commands:
                    arguments = next((words[len(prefix):] for prefix in INSTALL_PREFIXES
                                      if words[:len(prefix)] == prefix), None)
                    if arguments is not None:
                        self.command(source, " ".join(words), arguments, path)

    def command(self, source, text, arguments, path):
        """One install command. Anything but plain requirements and harmless flags rejects it whole."""
        found, index = [], 0
        while index < len(arguments):
            word = arguments[index]
            if word in ("-r", "--requirement") or word.startswith("--requirement="):
                target = word.split("=", 1)[1] if "=" in word else (arguments[index + 1] if index + 1 < len(arguments) else "")
                index += 1 if "=" in word else 2
                if self.inside(target, path):
                    self.notes.append({"source": source, "note": "requirements_file_read_separately"})
                    continue
                return self.reject(source, text, "requirements_file_outside_snapshot")
            if word.startswith("-"):
                if word in HARMLESS_OPTIONS:
                    index += 1
                    continue
                option = word.split("=", 1)[0]
                return self.reject(source, text, "editable_install" if option in ("-e", "--editable")
                                   else "index_option" if option in INDEX_OPTIONS else "unsupported_option")
            # shlex returns unquoted shell punctuation as tokens of its own; a quoted
            # requirement such as "numpy>=2.0" keeps its letters and stays one token.
            if word and set(word) <= set("()<>"):
                return self.reject(source, text, "shell_syntax")
            requirement, reason = parse_requirement(word)
            if reason:
                return self.reject(source, text, reason)
            found.append(word)
            index += 1
        for word in found:
            reason = self.accept(source, word)
            if reason:
                self.reject(source, word, reason)

    def requirements_file(self, path, text):
        for number, line in logical_lines(1, text.split("\n")):
            source = path + ":" + str(number)
            line = re.split(r"(?:^|\s)#", line, maxsplit=1)[0].strip()
            if not line:
                continue
            if re.search(r"(?:^|\s)--hash[=\s]", line):
                self.notes.append({"source": source, "note": "hash_dropped"})
                line = re.sub(r"\s*--hash[=\s]\S+", "", line).strip()
            if line.startswith("-"):
                words = line.split()
                option = words[0].split("=", 1)[0]
                if option in ("-r", "--requirement"):
                    target = words[0].split("=", 1)[1] if "=" in words[0] else (words[1] if len(words) > 1 else "")
                    if self.inside(target, path):
                        self.notes.append({"source": source, "note": "requirements_file_read_separately"})
                    else:
                        self.reject(source, line, "requirements_file_outside_snapshot")
                    continue
                self.reject(source, line, "editable_install" if option in ("-e", "--editable")
                            else "index_option" if option in INDEX_OPTIONS else "unsupported_option")
                continue
            reason = self.accept(source, line)
            if reason:
                self.reject(source, line, reason)

    def pyproject(self, path, text):
        try:
            data = tomllib.loads(text)
        except (tomllib.TOMLDecodeError, ValueError, RecursionError):
            return self.reject(path + ":1", "", "invalid_pyproject")
        project = data.get("project")
        dependencies = project.get("dependencies", []) if isinstance(project, dict) else []
        if not isinstance(dependencies, list):
            return self.reject(path + ":1", "", "invalid_pyproject")
        lines = text.split("\n")
        for item in dependencies:
            if not isinstance(item, str):
                self.reject(path + ":1", "", "invalid_pyproject")
                continue
            number = next((index + 1 for index, line in enumerate(lines) if item in line), 1)
            reason = self.accept(path + ":" + str(number), item)
            if reason:
                self.reject(path + ":" + str(number), item, reason)

    def record(self):
        return {"requirements": sorted(self.requirements.values(), key=lambda item: item["requirement"]),
                "rejected": self.rejected, "notes": self.notes}


def imported_modules(files):
    """Top-level modules the skill's code imports, minus its own; checked for availability, never installed."""
    own, names = set(), set()
    for path, _ in files:
        if path.endswith(".py"):
            parts = path.split("/")
            own.update([parts[-1][:-3], *parts[:-1]])

    def collect(text):
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError, RecursionError):
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names.add(node.module.split(".")[0])

    for path, text in files:
        if path.endswith(".py"):
            collect(text)
        elif path.lower().endswith(".md"):
            for _, info, body in fenced_blocks(text):
                if info.split()[:1] and info.split()[0].lower() in ("python", "py", "python3"):
                    collect("\n".join(body))
    return sorted(name for name in names - own - set(sys.stdlib_module_names) - {"__future__"}
                  if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,99}", name))[:200]


def run_commands(files):
    """The listed commands the skill's Markdown runs: the first word of a simple command in a shell block."""
    found = set()
    for path, text in files:
        if not path.lower().endswith(".md"):
            continue
        for first, info, body in fenced_blocks(text):
            if (info.split()[:1] or [""])[0].lower() not in SHELL_INFO:
                continue
            for _, line in logical_lines(first, body):
                line = re.sub(r"^\s*\$\s+", "", line)
                try:
                    commands = shell_commands(line)
                except ValueError:
                    commands = [line.split()]  # An unclosed quote, such as JSON continued on the next line.
                found.update(words[0] for words in commands if words and words[0] in COMMAND_DISTRIBUTIONS)
    return sorted(found)


def implied_requirements(record):
    """The requirements the skill's undeclared imports and listed commands add, by the reviewed tables."""
    declared = {item["name"] for item in record["requirements"]}
    found = []
    wanted = [(IMPORT_DISTRIBUTIONS.get(module), "import " + module) for module in record["imports"]]
    wanted += [(COMMAND_DISTRIBUTIONS[command], "command " + command) for command in record.get("commands") or []]
    for name, source in wanted:
        if name and normalized(name) not in declared and normalized(name) not in {item["name"] for item in found}:
            found.append({"requirement": normalized(name), "name": normalized(name), "sources": [source]})
    return found


def unavailable(message):
    return Fault("skill_environment_unavailable", message)


def finishing():
    control = CURRENT.get()
    if control:
        control.finishing = True


def remove(docker, args, log=None):
    """Best-effort removal that still happens after a cancellation or the attempt deadline."""
    for attempt in (1, 2):
        try:
            docker.invoke(args, timeout=60)
            return
        except Fault as error:
            if error.code in PASS_THROUGH and attempt == 1:
                finishing()
                continue
            if log:
                log.emit("environment_cleanup_incomplete", operation=args[:2], code=error.code)
            return


def manifest(docker, image, imports, settings, *, required, log=None, commands=()):
    """What the image reports about itself: installed distributions, unavailable imports and commands.

    Untrusted: an installed package can alter what Python reports. It goes to the record only.
    """
    name = "sci-verifier-manifest-" + uuid4().hex[:12]
    try:
        code, out, err = docker.invoke(
            ["run", "--rm", "--pull", "never", "--name", name, "--label", LABEL, "--network", "none",
             "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
             "--user", "65534:65534", "--memory", str(settings["memory_mib"]) + "m",
             "--memory-swap", str(settings["memory_mib"]) + "m", "--cpus", str(settings["cpus"]),
             "--pids-limit", str(settings["pids_limit"]), "--tmpfs", "/tmp:rw,nosuid,nodev,size=32m,mode=1777",
             "--entrypoint", "python3", image, "-I", "-c", MANIFEST, json.dumps(imports), json.dumps(list(commands))],
            timeout=MANIFEST_TIMEOUT_SECONDS, max_bytes=2 * 1024 * 1024, capture_output=False)
    except Fault as error:
        if error.code in PASS_THROUGH:
            finishing()
            remove(docker, ["rm", "--force", name], log)
            raise
        code, out, err = 1, b"", str(error).encode()
    remove(docker, ["rm", "--force", name], log)
    try:
        report = json.loads(out)
        distributions = [[str(item[0])[:100], str(item[1])[:64]] for item in report["distributions"][:5000]
                         if isinstance(item, list) and len(item) == 2]
        missing = [item for item in report["imports_unavailable"] if item in imports]
        absent = [item for item in report.get("commands_unavailable") or [] if item in commands]
        python = str(report["python"])[:32]
        if code:
            raise ValueError()
    except (ValueError, KeyError, TypeError, UnicodeError):
        if required:
            raise unavailable("The built image could not report its installed packages"
                              + (": " + err.decode("utf-8", "replace")[-500:] if err else ".")) from None
        return {"reported_by_image": True, "error": "The image could not report its packages."}
    return {"reported_by_image": True, "python": python, "distributions": distributions,
            "imports_unavailable": missing, "commands_unavailable": absent}


def lock_installed(report, lock):
    """Whether the image reports every locked wheel at its locked version."""
    def same(first, second):
        return first.lower().replace("_", "-") == second.lower().replace("_", "-")
    installed = {normalized(name): version for name, version in report.get("distributions", [])}
    return all(entry["name"] in installed and same(installed[entry["name"]], entry["version"])
               for entry in lock["entries"])


def within_caps(lock, settings):
    return (len(lock["entries"]) <= settings["max_packages"]
            and sum(entry["bytes"] for entry in lock["entries"]) <= settings["max_package_bytes"])


def wheels_lock(result, settings):
    """The host's own check of what the resolver reports, then the hash lock it will install."""
    try:
        wheels = result["wheels"]
        if not isinstance(wheels, list) or not wheels:
            raise ValueError()
        entries, seen = [], set()
        for item in wheels:
            match = WHEEL.fullmatch(item["file"])
            if (not match or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) or type(item["bytes"]) is not int
                    or item["bytes"] < 0):
                raise ValueError()
            name = normalized(match.group("name"))
            if name in seen:
                raise ValueError()
            seen.add(name)
            entries.append({"name": name, "version": match.group("version"), "file": item["file"],
                            "sha256": item["sha256"], "bytes": item["bytes"]})
    except (ValueError, KeyError, TypeError):
        raise unavailable("The resolver reported something other than distinct, well-formed wheels.") from None
    entries.sort(key=lambda entry: entry["name"])
    lock = {"entries": entries}
    if not within_caps(lock, settings):
        raise unavailable(f"The skill's packages come to {len(entries)} wheels and "
                          f"{sum(entry['bytes'] for entry in entries)} bytes, over max_packages "
                          f"{settings['max_packages']} or max_package_bytes {settings['max_package_bytes']}.")
    text = "".join(f"{entry['name']}=={entry['version']} --hash=sha256:{entry['sha256']}\n" for entry in entries)
    lock["digest"] = digest(text.encode("utf-8"))
    return lock, text


def base_config(docker, image):
    """The environment base's image ID and config: a Linux image with no entrypoint.

    The installer runs under the base's own entrypoint so that the commit keeps it: Docker
    ignores `--change "ENTRYPOINT []"`, and the first live build kept the installer's.
    """
    code, out, _ = docker.invoke(["image", "inspect", image], capture_output=False)
    try:
        info = json.loads(out)[0]
        config = info.get("Config") or {}
        valid = not code and info["Os"] == "linux" and bool(IMAGE_ID.fullmatch(info["Id"]))
    except (ValueError, KeyError, IndexError, TypeError, UnicodeError, AttributeError):
        valid = False
    if not valid:
        raise unavailable("environment_base_image is not an installed Linux image. Pull a plain Python image, such "
                          "as python:3.12-slim, and pin its ID.")
    if config.get("Entrypoint"):
        raise unavailable("environment_base_image has an entrypoint; pin a plain Python image without one.")
    return info["Id"], config


def _build(docker, store, record, settings, log):
    """Resolve with a network, install without one, commit. The only networked container is here."""
    base, config = base_config(docker, settings["environment_base_image"])
    requirements = [item["requirement"] for item in record["requirements"]]
    key = digest(canonical({"policy": POLICY, "scripts": SCRIPT_DIGESTS, "base_image": base,
                            "index": settings["package_index"], "requirements": requirements}))
    record.update(base_image=base, build_key=key)
    # A tag of its own: the image lives for this verification only, and another one building the
    # same requirements at the same time must not move it.
    suffix = uuid4().hex[:12]
    tag = "sci-verifier-env:" + suffix
    volume, resolver, installer = ("sci-verifier-" + kind + "-" + suffix for kind in ("wheels", "resolve", "install"))
    limits = ["--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--user", "0:0",
              "--memory", str(BUILD_MEMORY_MIB) + "m", "--memory-swap", str(BUILD_MEMORY_MIB) + "m",
              "--cpus", str(settings["cpus"]), "--pids-limit", str(settings["pids_limit"])]
    try:
        code, _, err = docker.invoke(["volume", "create", "--label", LABEL, volume], timeout=60)
        if code:
            raise unavailable("Docker could not create the package volume: " + err.decode("utf-8", "replace")[-300:])
        # The resolver: the plain base running pip download for wheels only. No package code
        # runs here, and no container after this one has a network.
        code, out, err = docker.invoke(
            ["run", "--rm", "--pull", "never", "--name", resolver, "--label", LABEL, "--network", "bridge",
             "--read-only", *limits, "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m,mode=1777",
             "--mount", f"type=volume,source={volume},target={WHEELS}", "-e", "HOME=/tmp",
             "-e", f"TMPDIR={WHEELS}/.tmp", "--entrypoint", "python3", base, "-I", "-c", RESOLVE,
             settings["package_index"], WHEELS, str(RESOLVE_TIMEOUT_SECONDS), *requirements],
            timeout=RESOLVE_TIMEOUT_SECONDS + 60, max_bytes=1024 * 1024)
        try:
            result = json.loads(out)
        except (ValueError, UnicodeError):
            result = {"error": err.decode("utf-8", "replace")[-1000:] or "The resolver produced no report."}
        if code or "error" in result:
            raise unavailable("Resolving the skill's packages from " + settings["package_index"] + " failed: "
                              + str(result.get("error", ""))[-1500:])
        lock, text = wheels_lock(result, settings)
        build = {"policy": POLICY, "build_key": key, "scripts": SCRIPT_DIGESTS, "base_image": base,
                 "index": settings["package_index"], "requirements": requirements, "lock": lock,
                 "built_at": utc_now(), "implementation_version": __version__}
        ref = store.put_json(build)
        # No --entrypoint here: the command runs under the base's own (empty) entrypoint, which the
        # commit then keeps.
        code, _, err = docker.invoke(
            ["run", "-i", "--pull", "never", "--name", installer, "--label", LABEL, "--network", "none", *limits,
             "--tmpfs", "/tmp:rw,nosuid,nodev,size=256m,mode=1777",
             "--mount", f"type=volume,source={volume},target={WHEELS},readonly",
             base, "python3", "-I", "-c", INSTALL, WHEELS],
            timeout=INSTALL_TIMEOUT_SECONDS, prompt=text, max_bytes=1024 * 1024)
        if code:
            raise unavailable("Installing the skill's packages failed: " + err.decode("utf-8", "replace")[-1500:]
                              + " Fix the skill's pins, or set package_index to null to run on sandbox_image.")
        changes = ["--change", "USER " + (config.get("User") or "root"),
                   "--change", f"LABEL {KEY_LABEL}={key}", "--change", f"LABEL {RECORD_LABEL}={ref}"]
        if config.get("Cmd"):
            changes = ["--change", "CMD " + json.dumps(config["Cmd"])] + changes
        code, out, err = docker.invoke(["commit", *changes, installer, tag], timeout=300)
        image = out.decode("utf-8", "replace").strip()
        if code or not IMAGE_ID.fullmatch(image):
            raise unavailable("Docker could not commit the skill environment: " + err.decode("utf-8", "replace")[-300:])
        try:
            report = manifest(docker, image, record["imports"], settings, required=True, log=log,
                              commands=record.get("commands") or [])
            if not lock_installed(report, lock):
                raise unavailable("The built image does not report every locked package as installed.")
        except BaseException:
            remove(docker, ["image", "rm", "--force", image], log)  # a failed build leaves no image
            raise
        record.update(status="built", image_id=image, build_record_ref=ref, lock=lock, manifest=report)
    except Fault as error:
        if error.code in PASS_THROUGH:
            finishing()
        raise
    finally:
        for args in (["rm", "--force", resolver], ["rm", "--force", installer], ["volume", "rm", "--force", volume]):
            remove(docker, args, log)


def sweep_environments(docker, log=None):
    """Remove environment images a killed verification left behind, once they are a day old.

    A verification removes its own image when it ends; only a process killed before that
    leaves one. A younger image may belong to a verification still running.
    """
    code, _, err = docker.invoke(["image", "prune", "--all", "--force", "--filter", "label=" + KEY_LABEL,
                                  "--filter", "until=24h"], timeout=120)
    if code and log:
        log.emit("environment_sweep_incomplete", stderr=err.decode("utf-8", "replace")[-300:])


def remove_environment(record, settings, *, workspace, log=None, process=None):
    """Remove the image one verification built, however that verification ended."""
    if not record or record.get("status") != "built":
        return
    finishing()  # the verification is over; a cancellation must not stop its cleanup
    try:
        docker = DockerSandbox(workspace, settings, log=log, process=process)
        docker.preflight()
    except Fault as error:
        if log:
            log.emit("environment_cleanup_incomplete", operation=["image", "rm"], code=error.code)
        return
    remove(docker, ["image", "rm", "--force", record["image_id"]], log)


def prepare_environment(source, source_root, settings, *, workspace, limits, log=None, process=None):
    """The record of "Skill environment"; its `image_id` is the image subject trials will use."""
    docker = DockerSandbox(workspace, settings, log=log, process=process)
    operator = docker.preflight()["image_id"]
    sweep_environments(docker, log)
    record = {"policy": POLICY, "status": None, "source_path": str(source), "snapshot_digest": None,
              "operator_image": operator, "base_image": None, "image_id": operator,
              "index": settings["package_index"], "requirements": [], "rejected": [], "notes": [], "imports": [],
              "commands": [],
              "manifest": None, "operator_manifest": None}
    store = Store(workspace)
    state = {"source_path": str(source), "source_root": str(source_root), "limits": limits, "run_id": None,
             "updated_at": utc_now(), "implementation_version": __version__}
    try:
        taken, _ = snapshot(store, state)
    except (Fault, OSError) as error:
        if getattr(error, "code", None) in PASS_THROUGH:
            raise
        # The planner's load_submitted_skill meets the same problem and journals it as usual.
        record.update(status="source_unavailable", reason=getattr(error, "code", "source_unreadable"))
        return finish(record, log)
    record["snapshot_digest"] = taken["digest"]
    # What a task design's generator and solver can use ("The reference solution" in local-tasks.md).
    record["operator_manifest"] = manifest(docker, operator, [], settings, required=False, log=log)
    files = [(entry["path"], store.get(entry["digest"]).decode("utf-8"))
             for entry in taken["files"] if entry["encoding"] == "utf-8"]
    record.update(Declarations(files).record(), imports=imported_modules(files), commands=run_commands(files))
    implied = implied_requirements(record)
    if not record["requirements"] and (record["imports"] or record["commands"]):
        # Nothing declared: the operator's image serves unless it lacks a listed module the skill imports
        # or a listed command it runs.
        record["manifest"] = manifest(docker, operator, record["imports"], settings, required=False, log=log,
                                      commands=record["commands"])
        lacking = [module for module in record["manifest"].get("imports_unavailable") or []
                   if module in IMPORT_DISTRIBUTIONS]
        lacking += [command for command in record["manifest"].get("commands_unavailable") or []
                    if command in COMMAND_DISTRIBUTIONS]
        if not lacking:
            implied = []
    record["requirements"] = record["requirements"] + implied
    if record["requirements"] and settings["package_index"]:
        _build(docker, store, record, settings, log)
        return finish(record, log)
    record["status"] = ("disabled" if record["requirements"] else "all_rejected" if record["rejected"]
                        else "not_needed")
    if (record["imports"] or record["commands"]) and record["manifest"] is None:
        record["manifest"] = manifest(docker, operator, record["imports"], settings, required=False, log=log,
                                      commands=record["commands"])
    return finish(record, log)


def finish(record, log):
    safe_payload(record)
    if log:
        log.emit("environment_prepared", status=record["status"], image_id=record["image_id"],
                 requirements=len(record["requirements"]), rejected=len(record["rejected"]),
                 packages=len(record.get("lock", {}).get("entries", [])))
    return record


def planner_block(record):
    """The planner's pinned block, rendered only from values the verifier checked itself.

    Skill text never enters an instruction block: paths, rejected commands and the image's own
    report stay in the record, which the `environment` context section returns as data.
    """
    def image(value):
        return value if isinstance(value, str) and IMAGE_ID.fullmatch(value) else "(unrecorded)"

    status, operator = record["status"], image(record["operator_image"])
    lines = ["Subject environment for this run. It was fixed before the run began, and nothing can be "
             "installed during the run.", "Status: " + status + "."]
    if status == "built":
        host = urlsplit(record["index"]).hostname or "the configured index"
        entries = record["lock"]["entries"]
        shown = [entry["name"] + " " + entry["version"] for entry in entries
                 if SAFE_NAME.fullmatch(entry["name"]) and SAFE_VERSION.fullmatch(entry["version"])][:300]
        lines.append(f"Subject trials run in image {image(record['image_id'])}: the plain Python base "
                     f"{image(record['base_image'])} plus {len(entries)} wheels from {host}, installed from a hash "
                     "lock with no network, and nothing else from the operator's image: " + ", ".join(shown)
                     + (f", and {len(entries) - len(shown)} more" if len(shown) < len(entries) else "") + ".")
    else:
        lines.append(f"Subject trials run in the operator's image {operator}.")
        lines.append({"disabled": f"The skill needs {len(record['requirements'])} package requirements, but no "
                                  "package index is configured, so none was installed.",
                      "all_rejected": "Every package declaration in the skill was rejected, so none was installed.",
                      "not_needed": "The skill declares no packages to install.",
                      "source_unavailable": "Setup could not read the skill, so nothing was installed; "
                                            "load_submitted_skill reports why."}[status])
    reasons = sorted({item["reason"] for item in record["rejected"]} & REASONS)
    imported = [item["name"] for item in record["requirements"] if from_import(item)]
    commanded = [item["name"] for item in record["requirements"] if from_command(item)]
    lines.append(f"Declarations: {len(record['requirements']) - len(imported) - len(commanded)} accepted, "
                 f"{len(record['rejected'])} rejected" + (" (" + ", ".join(reasons) + ")" if reasons else "")
                 + (f"; added from the skill's imports: {', '.join(name for name in imported if SAFE_NAME.fullmatch(name))}"
                    if imported else "")
                 + (f"; added for the commands it runs: {', '.join(n for n in commanded if SAFE_NAME.fullmatch(n))}"
                    if commanded else "") + ".")
    lines.append("Task generators, reference solutions and scoring run in the operator's image, without the skill's "
                 "packages.")
    report = record.get("operator_manifest") or {}
    packages = sorted({str(name).lower() + " " + str(version) for name, version in report.get("distributions") or []
                       if SAFE_NAME.fullmatch(str(name).lower()) and SAFE_VERSION.fullmatch(str(version))})
    if packages:
        lines.append("The operator's image " + operator + " reports Python " + str(report.get("python", "?"))[:32]
                     + " with " + ", ".join(packages[:300]) + "; it is the operator's own pinned image.")
    lines.append("The environment section of get_verifier_context lists where each requirement was declared, the "
                 "rejected declarations, and the packages and imports the image reports about itself. That report "
                 "is untrusted, since an installed package could alter it.")
    return "\n".join(lines)[:12000]


def from_import(requirement):
    """True for a requirement the reviewed table added for an undeclared import."""
    return any(str(source).startswith("import ") for source in requirement.get("sources") or [])


def from_command(requirement):
    """True for a requirement the reviewed table added for a command the skill runs."""
    return any(str(source).startswith("command ") for source in requirement.get("sources") or [])


def report_line(summary):
    """report-card.md's Environment line, in plain text; the caller escapes it."""
    status = summary["status"]
    if status == "built":
        text = (f"Environment: {status}. Subject trials ran in {summary['image_id']}, the plain Python base "
                f"{summary['base_image']} plus {summary['packages']} wheels from {summary['index']} (lock "
                f"{summary.get('lock_digest')}), for {summary['requirements']} requirements, "
                f"{summary.get('from_imports', 0)} of them added from the skill's imports and "
                f"{summary.get('from_commands', 0)} for the commands it runs, and "
                f"{summary['rejected']} rejected; the image was removed after the run. Task generators, reference "
                f"solutions and scoring used the operator's image {summary['operator_image']}.")
    else:
        text = (f"Environment: {status}. Subject trials ran in the operator's image {summary['operator_image']}. "
                f"The skill declared {summary['requirements']} installable requirements and "
                f"{summary['rejected']} rejected ones" + ("; no package index was configured" if status == "disabled"
                                                          else "") + ".")
    missing = summary.get("imports_unavailable_reported_by_image")
    if missing:
        text += " Imports the image reported as unavailable (its own report, untrusted): " + ", ".join(missing) + "."
    absent = summary.get("commands_unavailable_reported_by_image")
    if absent:
        text += " Commands the image reported as unavailable (its own report, untrusted): " + ", ".join(absent) + "."
    return text


def report_summary(record):
    """The report card's `environment` summary and the setup log's preflight entry."""
    summary = {"status": record["status"], "image_id": record["image_id"], "operator_image": record["operator_image"],
               "base_image": record["base_image"], "index": record["index"], "requirements": len(record["requirements"]),
               "from_imports": sum(from_import(item) for item in record["requirements"]),
               "from_commands": sum(from_command(item) for item in record["requirements"]),
               "rejected": len(record["rejected"]), "packages": len(record.get("lock", {}).get("entries", []))}
    if record.get("lock"):
        summary["lock_digest"] = record["lock"]["digest"]
    if isinstance(record.get("manifest"), dict) and "imports_unavailable" in record["manifest"]:
        summary["imports_unavailable_reported_by_image"] = record["manifest"]["imports_unavailable"]
    if isinstance(record.get("manifest"), dict) and record["manifest"].get("commands_unavailable"):
        summary["commands_unavailable_reported_by_image"] = record["manifest"]["commands_unavailable"]
    return summary
