"""Safety findings: plain facts about a skill's files, read and never run ("Safety findings" in local-contract.md).

They describe the skill as software. No grade, status or claim reads them.
"""

import ast
import re
from urllib.parse import urlsplit

from .common import fenced_blocks

POLICY = "local-safety-scan-1"
MAX_FINDINGS = 100
DETAIL_CHARS = 300
NETWORK_ROOTS = {"requests", "httpx", "aiohttp", "urllib3", "socket", "ftplib", "smtplib", "paramiko", "websocket",
                 "websockets", "pycurl"}
NETWORK_MODULES = NETWORK_ROOTS | {"urllib.request", "http.client"}
NETWORK_CALLS = {"urlopen", "urlretrieve", "get", "post", "put", "patch", "delete", "head", "request", "stream",
                 "create_connection", "HTTPConnection", "HTTPSConnection", "connect", "sendmail"}
PROCESS_CALLS = {"os.system", "os.popen", "os.execv", "os.execvp", "os.execl", "os.spawnv", "os.startfile"}
DYNAMIC_CALLS = {"eval", "exec", "compile"}
CREDENTIAL = re.compile(r"(?i)key|token|secret|passw|credential")
URL = re.compile(r"https?://[^\s'\"<>)\]]+")
DOWNLOAD_AND_RUN = re.compile(r"(?i)(curl|wget)\b[^\n|]*\|\s*(sudo\s+)?(ba|z|da)?sh\b|bash\s+<\(\s*(curl|wget)"
                              r"|iex\s*\(\s*(iwr|irm|invoke-webrequest)")
INSTALL_FROM_URL = re.compile(r"(?i)pip3?\s+install\s+[^\n]*(https?://|git\+)")
COMMENT = re.compile(r"<!--(.*?)-->", re.S)
TO_AGENTS = re.compile(r"(?i)\b(agents?|assistants?|AI|LLMs?|models?|verif\w*|reviewers?|claude|gpt)\b")
INVISIBLE = re.compile("[​-‏‪-‮⁠-⁤﻿]")
# A promise names what does not happen; "offline filters" in an EEG guide is not one.
NETWORK_PROMISE = re.compile(r"(?i)\b(makes? no network|no network (calls?|access|use|requests?|connections?)"
                             r"|never leaves? (your|the) (computer|machine)|stays? on your (computer|machine)"
                             r"|no data (is |are )?(sent|shared|uploaded)|does not (send|upload|transmit)\b"
                             r"|no telemetry|(works|runs) (fully )?offline)")
DYNAMIC_PROMISE = re.compile(r"(?i)\b(never uses?|does not use|no) `?(eval|exec)\b")
# What each promise is checked against: a fact of that kind in the bundled code contradicts it.
PROMISES = {"network promise": "network", "eval promise": "dynamic code"}


def scan(files):
    """`files` is the snapshot's text files as (path, text). Returns the record the report card carries."""
    findings = []
    for path, text in files:
        if path.endswith(".py"):
            findings += python_facts(text, path, instructions=False)
        elif path.lower().endswith((".md", ".markdown")):
            for start, info, body in fenced_blocks(text):
                if (info.split()[:1] or [""])[0].lower() in ("python", "py", "python3"):
                    findings += python_facts("\n".join(body), path, instructions=True, offset=start - 1)
        findings += text_facts(text, path)
    findings.sort(key=lambda item: (item["path"], item["line"], item["kind"]))
    contradictions = []
    for promise in (item for item in findings if item["kind"] in PROMISES):
        against = [item for item in findings if item["kind"] == PROMISES[promise["kind"]] and item["path"].endswith(".py")]
        if against:
            contradictions.append({"kind": promise["kind"], "promise": promise["detail"], "path": promise["path"],
                                   "line": promise["line"],
                                   "contradicted_by": [item["path"] + ":" + str(item["line"]) + " " + item["detail"]
                                                       for item in against[:5]]})
    return {"policy": POLICY, "files_read": len(files), "contradictions": contradictions,
            "findings": findings[:MAX_FINDINGS], "truncated": len(findings) > MAX_FINDINGS}


def fact(kind, path, line, detail):
    return {"kind": kind, "path": path, "line": line, "detail": " ".join(str(detail).split())[:DETAIL_CHARS]}


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return ""


def hosts(node):
    return sorted({urlsplit(url).hostname or url for child in ast.walk(node) if isinstance(child, ast.Constant)
                   and isinstance(child.value, str) for url in URL.findall(child.value)})


def python_facts(code, path, *, instructions, offset=0):
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError, RecursionError):
        return []
    network = "network in instructions" if instructions else "network"
    found, names, uses_network = [], {}, False
    for node in ast.walk(tree):
        line = offset + getattr(node, "lineno", 0)
        if isinstance(node, ast.Import):
            for alias in node.names:
                names[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
                if alias.name in NETWORK_MODULES or alias.name.split(".")[0] in NETWORK_ROOTS:
                    uses_network = True
                    found.append(fact(network, path, line, "imports " + alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            for alias in node.names:
                names[alias.asname or alias.name] = node.module + "." + alias.name
            if node.module in NETWORK_MODULES or node.module.split(".")[0] in NETWORK_ROOTS or (
                    node.module == "urllib" and any(alias.name == "request" for alias in node.names)):
                uses_network = True
                found.append(fact(network, path, line, "imports from " + node.module))
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            head = name.split(".")[0]
            full = names.get(head, head) + name[len(head):] if name else ""
            if name in DYNAMIC_CALLS:
                found.append(fact("dynamic code", path, line, name + "(…)"))
            elif full in ("__import__", "importlib.import_module") and node.args and not isinstance(node.args[0], ast.Constant):
                found.append(fact("dynamic code", path, line, full + " of a computed name"))
            elif full.startswith("subprocess.") or full in PROCESS_CALLS:
                command = node.args[0] if node.args else None
                shown = ast.unparse(command) if isinstance(command, (ast.Constant, ast.List, ast.Tuple)) else ""
                found.append(fact("runs commands", path, line, full + (" " + shown if shown else "")))
            elif full.split(".")[-1] in NETWORK_CALLS and (full.split(".")[0] in NETWORK_ROOTS or any(
                    full.startswith(module + ".") for module in NETWORK_MODULES)):
                uses_network = True
                named = hosts(node)
                found.append(fact(network, path, line, full + (" to " + ", ".join(named) if named else "")))
            elif full in ("os.environ.get", "os.getenv") and node.args and isinstance(node.args[0], ast.Constant) \
                    and isinstance(node.args[0].value, str) and CREDENTIAL.search(node.args[0].value):
                found.append(fact("reads a credential", path, line, node.args[0].value))
        elif isinstance(node, ast.Subscript) and dotted(node.value) == "os.environ" and isinstance(node.slice, ast.Constant) \
                and isinstance(node.slice.value, str) and CREDENTIAL.search(node.slice.value):
            found.append(fact("reads a credential", path, line, node.slice.value))
    if uses_network:
        named = hosts(tree)
        if named:
            found.append(fact(network, path, offset + 1, "names hosts " + ", ".join(named)))
    return found


def text_facts(text, path):
    found = []

    def line_of(index):
        return text.count("\n", 0, index) + 1

    def whole_line(match):
        start = text.rfind("\n", 0, match.start()) + 1
        end = text.find("\n", match.end())
        return text[start:end if end >= 0 else len(text)]

    for match in DOWNLOAD_AND_RUN.finditer(text):
        found.append(fact("download and run", path, line_of(match.start()), whole_line(match)))
    for match in INSTALL_FROM_URL.finditer(text):
        found.append(fact("install from a URL", path, line_of(match.start()), whole_line(match)))
    if not path.endswith(".py"):
        for match in COMMENT.finditer(text):
            body = match.group(1)
            found.append(fact("hidden comment to agents" if TO_AGENTS.search(body) else "hidden comment",
                              path, line_of(match.start()), body))
    for match in INVISIBLE.finditer(text):
        found.append(fact("invisible character", path, line_of(match.start()), "U+%04X" % ord(match.group(0))))
    for kind, pattern in (("network promise", NETWORK_PROMISE), ("eval promise", DYNAMIC_PROMISE)):
        for line in sorted({line_of(match.start()): match for match in pattern.finditer(text)}.items()):
            found.append(fact(kind, path, line[0], whole_line(line[1])))
    return found
