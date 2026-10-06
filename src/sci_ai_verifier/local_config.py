"""Operator configuration; models cannot expand permissions or select host code."""

import re
from copy import deepcopy
from pathlib import Path
from urllib.parse import urlsplit

from .common import Fault, canonical, digest
from .storage import no_links

DEFAULTS = {"schema_version": 1, "sandbox_image": None, "docker_executable": "docker",
            "memory_mib": 512, "cpus": 1, "pids_limit": 64,
            "workspace_mib": 128, "max_file_bytes": 4*1024*1024,
            "max_artifact_bytes": 16*1024*1024, "max_artifacts": 200,
            "trial_count": 3, "max_subject_calls": 128,
            # A task runs the skill on its files and writes a results file ("Tasks" in local-tasks.md);
            # 120 s fitted a question's answer and is too short for that.
            "subject_timeout_seconds": 600, "allowed_reference_hosts": [],
            "allowed_subject_hosts": [], "external_tools": {}, "resources": {},
            "documentary_assessment": True, "catalogs": [], "minimum_grade": None,
            "package_index": None, "environment_base_image": None,
            "max_package_bytes": 1024*1024*1024, "max_packages": 200}


def valid_package_index(value):
    """An operator-chosen HTTPS index with nothing a URL could smuggle: no credentials,
    query, fragment, whitespace or control characters."""
    if not isinstance(value, str) or not 9 <= len(value) <= 2048 or re.search(r"[\x00-\x20\x7f]", value):
        return False
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return False
    return (parts.scheme == "https" and bool(parts.hostname) and parts.username is None
            and parts.password is None and not parts.query and not parts.fragment
            and port in (None, 443) and bool(re.fullmatch(r"[A-Za-z0-9.-]+", parts.hostname)))


def load_configuration(path=None):
    settings = deepcopy(DEFAULTS)
    if path is not None:
        try:
            file = no_links(path)
            if file.stat().st_size > 65536:
                raise ValueError()
            from .mcp import parse_json
            supplied = parse_json(file.read_bytes())
            if not isinstance(supplied, dict):
                raise ValueError()
        except (OSError, ValueError, UnicodeError, RecursionError):
            raise Fault("configuration_invalid", "Local settings must be a bounded JSON object.") from None
        unknown = sorted(set(supplied) - set(DEFAULTS))
        if unknown:
            # Name the keys: a settings file written by an older build carries the two
            # removed review keys, and a generic rejection gives the operator nothing.
            retired = sorted({"scientific_reviews", "documentary_review"} & set(unknown))
            detail = (" " + " and ".join(retired) + " no longer exist: grades are settled by the "
                      "evidence and an independent critique, so remove those keys." if retired else "")
            raise Fault("configuration_invalid",
                        "Unsupported local settings key(s): " + ", ".join(unknown) + "." + detail)
        settings.update(supplied)
    if settings["schema_version"] != 1:
        raise Fault("configuration_invalid", "Unsupported local configuration version.")
    bounds = {"memory_mib": (128,32768), "cpus": (1,32), "pids_limit": (16,1024),
              "workspace_mib": (16,4096), "max_file_bytes": (1024,64*1024*1024),
              "max_artifact_bytes": (1024,256*1024*1024), "max_artifacts": (1,1000),
              # Floor of three, not one: the rubric permits a single trial only against a
              # deterministic subject with a fixed entry point, and this profile's subject
              # is always a fresh model session. A lone sample cannot tell a skill that is
              # right from one that is sometimes right, so n=1 is never legitimate here.
              "trial_count": (3,20), "max_subject_calls": (1,10000),
              "subject_timeout_seconds": (1,3600),
              "max_package_bytes": (1024*1024,8*1024*1024*1024), "max_packages": (1,2000)}
    for key, (minimum, maximum) in bounds.items():
        if type(settings[key]) is not int or not minimum <= settings[key] <= maximum:
            raise Fault("configuration_invalid", f"{key} must be between {minimum} and {maximum}.")
    for key in ("sandbox_image", "environment_base_image"):
        image = settings[key]
        if image is not None and (not isinstance(image,str) or not re.fullmatch(r"(?:[A-Za-z0-9._:/-]+@)?sha256:[0-9a-f]{64}",image)):
            raise Fault("configuration_invalid", f"Pin {key} to an installed sha256 image ID or repository digest.")
    if not isinstance(settings["docker_executable"], str) or not settings["docker_executable"]:
        raise Fault("configuration_invalid", "Choose the installed Docker executable.")
    for key in ("allowed_reference_hosts","allowed_subject_hosts"):
        hosts = settings[key]
        if not isinstance(hosts,list) or len(hosts)>100 or any(not isinstance(host,str) or not re.fullmatch(r"[A-Za-z0-9.-]+",host) for host in hosts):
            raise Fault("configuration_invalid", "Resource hosts must be a bounded list of exact DNS names.")
    if not isinstance(settings["external_tools"],dict) or len(settings["external_tools"])>20:
        raise Fault("configuration_invalid", "External tools must be a bounded operator-defined mapping.")
    for name,tool in settings["external_tools"].items():
        required={"executable","sha256","arguments","description","credential_env","read_only"}
        if (not re.fullmatch(r"[a-z][a-z0-9_]{0,39}",name) or not isinstance(tool,dict) or set(tool)!=required
                or not isinstance(tool["executable"],str) or not Path(tool["executable"]).is_absolute()
                or not re.fullmatch(r"[0-9a-f]{64}",str(tool["sha256"]))
                or not isinstance(tool["arguments"],list) or len(tool["arguments"])>20
                or any(not isinstance(arg,str) or len(arg)>2000 for arg in tool["arguments"])
                or not isinstance(tool["description"],str) or not 1<=len(tool["description"])<=2000
                or not isinstance(tool["credential_env"],list) or len(tool["credential_env"])>10
                or any(not isinstance(env,str) or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,99}",env) or env in {"CLAUDE_CODE_OAUTH_TOKEN","ANTHROPIC_API_KEY","PATH","PYTHONPATH","NODE_OPTIONS"} for env in tool["credential_env"])
                or tool["read_only"] is not True):
            raise Fault("configuration_invalid", "App adapters must be pinned read-only native programs with fixed arguments and named credential environment variables.")
    if not isinstance(settings["resources"],dict) or len(settings["resources"])>100:
        raise Fault("configuration_invalid", "Resources must be an operator-selected mapping.")
    for name,resource in settings["resources"].items():
        if (not re.fullmatch(r"[a-z][a-z0-9_]{0,79}",name) or not isinstance(resource,dict)
                or set(resource)!={"path","sha256","version","license","units","description"}
                or any(not isinstance(value,str) or len(value)>4000 for value in resource.values())
                or not Path(resource["path"]).is_absolute() or not re.fullmatch(r"[0-9a-f]{64}",resource["sha256"])):
            raise Fault("configuration_invalid", "Resources require an absolute path, digest, version, license, units and description.")
    if type(settings["documentary_assessment"]) is not bool:
        raise Fault("configuration_invalid","documentary_assessment must be true or false.")
    if settings["minimum_grade"] is not None and (not isinstance(settings["minimum_grade"],str) or settings["minimum_grade"] not in ("A","B","C","D")):
        raise Fault("configuration_invalid","minimum_grade must be A, B, C, D or null.")
    if not isinstance(settings["catalogs"],list) or len(settings["catalogs"])>20:
        raise Fault("configuration_invalid","Catalogs must be a bounded list of pinned bundles.")
    for catalog in settings["catalogs"]:
        if (not isinstance(catalog,dict) or set(catalog)!={"location","sha256"}
                or not isinstance(catalog["location"],str) or len(catalog["location"])>4096
                or not (catalog["location"].startswith("https://") or Path(catalog["location"]).is_absolute())
                or not re.fullmatch(r"[0-9a-f]{64}",str(catalog["sha256"]))):
            raise Fault("configuration_invalid","Each catalog needs an absolute file path or HTTPS URL and exact SHA256.")
    if settings["package_index"] is not None and not valid_package_index(settings["package_index"]):
        raise Fault("configuration_invalid", "package_index must be null or an https:// index URL without "
                    "credentials, query or fragment.")
    if settings["package_index"] is not None and settings["environment_base_image"] is None:
        # Skill environments start from a plain base, never from sandbox_image and its tools.
        raise Fault("configuration_invalid", "package_index needs environment_base_image: the pinned ID of a "
                    "plain Python image, such as python:3.12-slim, that skill environments start from.")
    return settings


def configuration_digest(settings):
    return digest(canonical(settings))


def source_limits(settings):
    """The snapshot limits the local profile takes from its settings. Setup's snapshot and the
    planner's `load_submitted_skill` use the same ones, so they reach the same digest."""
    return {"max_file_bytes": settings["max_file_bytes"], "max_total_bytes": settings["max_artifact_bytes"],
            "max_files": settings["max_artifacts"]}
