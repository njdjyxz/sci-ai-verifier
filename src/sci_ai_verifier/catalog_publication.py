"""Draft GitHub proposals: the agent prepares and opens them, a person reviews and merges.

The pull request is the review request, not its result. The agent checks a bundle
mechanically, opens a draft PR, reads the review comments, and pushes revisions to
the same branch. Merging is the human decision and this module never performs it.
Retries are durable: a lost reply is reconciled instead of pushed twice.
"""

import os
import re
import shutil
from pathlib import Path

from .common import Fault, canonical, digest, utc_now
from .claude_runner import run_process
from .local_catalog import MAX_BUNDLE
from .mcp import parse_json
from .storage import atomic_write, no_links

BRANCH_PREFIX = "verifier"
ENVIRONMENT = {"PATH", "SYSTEMROOT", "WINDIR", "APPDATA", "LOCALAPPDATA", "USERPROFILE",
               "HOME", "TEMP", "TMP", "GH_TOKEN", "GITHUB_TOKEN"}


def load_proposal(bundle_path):
    """Read and shape-check one prepared file, returning its bytes, payload and identity."""
    path = no_links(bundle_path)
    if path.stat().st_size > MAX_BUNDLE:
        raise Fault("catalog_rejected", "Candidate bundle exceeds its byte limit.")
    raw = path.read_bytes()
    bundle = parse_json(raw)
    if not isinstance(bundle, dict):
        raise Fault("catalog_invalid", "Publish a prepared candidate export or catalog release.")
    if bundle.get("kind") == "local-catalog-release":
        from .catalog_release import validate
        validate(raw)
        identity = bundle["catalog_id"] + "-" + bundle["version"]
        return path, raw, bundle, True, identity, "catalog/releases/" + bundle["catalog_id"] + "/" + bundle["version"] + ".json"
    if bundle.get("kind") != "local-candidate-bundle":
        raise Fault("catalog_invalid", "Publish a prepared candidate export or catalog release.")
    # One proposal identity per candidate set, so a revision updates its own branch.
    identity = digest(canonical(sorted(bundle["candidate_refs"])))[:20]
    return path, raw, bundle, False, identity, "catalog/proposals/" + identity + ".json"


def body(bundle, release, key):
    if release:
        return ("Proposes local catalog `" + bundle["catalog_id"] + "` version `" + bundle["version"]
                + "`, exact SHA256 `" + key + "`.\n\n"
                "Prepared and mechanically checked by the verifier agent. Every candidate carries the "
                "agent's own provenance, scope, coverage, uncertainty and redistribution assessment, "
                "plus an approve-or-retire proposal. **Those are proposals, not review findings.**\n\n"
                "Please review each assessment, the retirement set, the runtime range and the predecessor "
                "pin, and leave review comments for anything that needs changing; the agent will push "
                "revisions to this branch. Catalog membership confers no scientific grade. Merging this "
                "PR is the decision to distribute these exact bytes.")
    return ("Proposes the candidate bundle `" + key + "` for review.\n\n"
            "Prepared and mechanically checked by the verifier agent: every expected answer is quoted "
            "exactly from its pinned reference bytes and every comparison control passes. The export "
            "excludes subject runs, workflow logs and operator settings. **Mechanical qualification is "
            "not scientific approval.**\n\n"
            "Please review applicability, oracle independence, controls, coverage, uncertainty and the "
            "recorded redistribution assessment, and leave review comments for anything that needs "
            "changing; the agent will push revisions to this branch. Merging this PR is the decision "
            "to accept the candidate into the catalog.")


def github(repository, cwd, process=None):
    """A bounded `gh api` caller for one repository. No shell, no interactive prompt."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise Fault("repository_invalid", "Specify the intended GitHub owner/repository.")
    executable = shutil.which("gh")
    if not executable or Path(executable).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        raise Fault("github_cli_unavailable", "Install and sign in to the native GitHub CLI before opt-in publication.")
    environment = {key: value for key, value in os.environ.items() if key.upper() in ENVIRONMENT}
    environment["GH_PROMPT_DISABLED"] = "1"

    def call(endpoint, payload=None, method=None):
        command = [executable, "api", "--hostname", "github.com", "repos/" + repository + "/" + endpoint]
        if payload is not None:
            command += ["--method", method or "POST", "--input", "-"]
        elif method:
            command += ["--method", method]
        code, out, _ = (process or run_process)(
            command, cwd=cwd, env=environment,
            prompt=canonical(payload).decode() if payload is not None else "",
            timeout=45, max_bytes=2 * 1024 * 1024)
        if code:
            raise Fault("publication_unavailable", "GitHub publication failed. The prepared bundle and "
                        "completed stages are retained; retry this file only.")
        return parse_json(out)

    return call


def publish(bundle_path, repository, *, process=None):
    """Open or revise one draft pull request for a prepared bundle or release."""
    path, raw, bundle, release, identity, target = load_proposal(bundle_path)
    key = digest(raw)
    branch = BRANCH_PREFIX + ("/catalog-release-" if release else "/candidate-") + identity
    state_path = path.with_name(path.name + ".publication.json")
    state = (parse_json(no_links(state_path).read_bytes()) if state_path.exists() else
             {"proposal_id": identity, "repository": repository, "branch": branch, "target_path": target,
              "bundle_sha256": key, "revisions": [], "created_at": utc_now()})
    if state["repository"] != repository or state["branch"] != branch:
        raise Fault("publication_changed", "This receipt belongs to another repository or proposal; "
                    "prepare a separate proposal file.")
    if state["bundle_sha256"] != key:
        # A revision addressing review comments: same branch and pull request, new commit.
        state["bundle_sha256"] = key
        state.pop("commit", None)
    elif state.get("pull_request_url") and state.get("commit"):
        return state
    api = github(repository, path.parent, process)

    def save():
        atomic_write(state_path, canonical(state))

    owner = repository.split("/")[0]
    head = None
    if state.get("branch_created"):
        # Matching-refs returns an empty list when a branch does not exist.
        refs = api("git/matching-refs/heads/" + branch)
        head = next((item["object"]["sha"] for item in refs if item["ref"] == "refs/heads/" + branch), None)
    if "commit" not in state:
        parent = head or api("git/ref/heads/main")["object"]["sha"]
        tree = api("git/trees", {"base_tree": api("git/commits/" + parent)["tree"]["sha"],
                                 "tree": [{"path": target, "mode": "100644", "type": "blob",
                                           "content": raw.decode("utf-8")}]})
        message = ("Revise " if head else "Propose ") + ("local catalog release " if release else
                                                         "local evaluator bundle ") + key[:12]
        state["commit"] = api("git/commits", {"message": message, "tree": tree["sha"], "parents": [parent]})["sha"]
        state["revisions"] = [*state["revisions"], {"bundle_sha256": key, "commit": state["commit"],
                                                    "created_at": utc_now()}]
        save()
    if not state.get("branch_created"):
        refs = api("git/matching-refs/heads/" + branch)
        exact = next((item for item in refs if item["ref"] == "refs/heads/" + branch), None)
        if exact and exact["object"]["sha"] != state["commit"]:
            raise Fault("publication_conflict", "That branch already exists and was not created by this "
                        "proposal; no branch was overwritten.")
        if not exact:
            api("git/refs", {"ref": "refs/heads/" + branch, "sha": state["commit"]})
        state["branch_created"] = True
        save()
    elif head is None:
        # The branch this proposal created is gone, which is what GitHub does after a
        # merge. Recreate it rather than patching a ref that no longer exists.
        api("git/refs", {"ref": "refs/heads/" + branch, "sha": state["commit"]})
        save()
    elif head != state["commit"]:
        api("git/refs/heads/" + branch, {"sha": state["commit"]}, method="PATCH")
        save()
    if not state.get("pull_request_url"):
        # A successful remote write with a lost response is reconciled before another write.
        pulls = api("pulls?state=all&head=" + owner + ":" + branch)
        if pulls:
            state["pull_request_url"] = pulls[0]["html_url"]
        else:
            state["pull_request_url"] = api("pulls", {
                "title": ("Review local catalog release " if release else "Review local evaluator bundle ")
                         + key[:12], "head": branch, "base": "main", "draft": True,
                "body": body(bundle, release, key)})["html_url"]
        save()
    return state


def review(bundle_path, repository, *, process=None):
    """Read the human review on a proposal so the agent can address it. Read-only."""
    path, _, _, _, identity, _ = load_proposal(bundle_path)
    state_path = path.with_name(path.name + ".publication.json")
    if not state_path.exists():
        raise Fault("publication_missing", "This proposal has not been submitted yet.")
    state = parse_json(no_links(state_path).read_bytes())
    if not state.get("pull_request_url"):
        raise Fault("publication_missing", "This proposal has no open pull request yet.")
    number = state["pull_request_url"].rsplit("/", 1)[-1]
    if not re.fullmatch(r"[0-9]{1,9}", number):
        raise Fault("publication_missing", "The recorded pull request URL is unusable.")
    api = github(repository, path.parent, process)
    pull = api("pulls/" + number)
    comments = [{"path": item.get("path"), "line": item.get("line"), "body": item.get("body", "")[:8000],
                 "author": (item.get("user") or {}).get("login")}
                for item in api("pulls/" + number + "/comments?per_page=100")[:100]]
    discussion = [{"body": item.get("body", "")[:8000], "author": (item.get("user") or {}).get("login")}
                  for item in api("issues/" + number + "/comments?per_page=100")[:100]]
    reviews = [{"state": item.get("state"), "body": item.get("body", "")[:8000],
                "author": (item.get("user") or {}).get("login")}
               for item in api("pulls/" + number + "/reviews?per_page=100")[:100]]
    return {"proposal_id": identity, "pull_request_url": state["pull_request_url"],
            "state": pull.get("state"), "draft": pull.get("draft"), "merged": pull.get("merged"),
            "mergeable_state": pull.get("mergeable_state"), "reviews": reviews,
            "inline_comments": comments, "discussion": discussion,
            "next_step": "Address the comments, re-export the bundle, and publish the same proposal "
                         "file again to push a revision. Merging remains the reviewer's decision."}
