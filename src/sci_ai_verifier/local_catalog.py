"""Portable candidate bundles: exact pins, offline reuse and explicit exports."""

import base64
from pathlib import Path

from .common import Fault,canonical,digest,utc_now
from .ingest import SECRET_BYTES
from .local_candidates import fetch_bytes,qualify,save_candidate,METHOD_VERSION
from .storage import atomic_write,no_links
from .mcp import parse_json

MAX_BUNDLE=16*1024*1024


def export_bundle(store,candidate_refs,*,authorization):
    if not isinstance(authorization,str) or not 20<=len(authorization)<=4000:
        raise Fault("publication_authorization_required","Record explicit permission to redistribute these candidates and every included reference.")
    if not 1<=len(candidate_refs)<=100 or len(set(candidate_refs))!=len(candidate_refs):
        raise Fault("catalog_invalid","Export 1 to 100 unique candidate references.")
    objects={}
    for key in candidate_refs:
        candidate=store.get_json(key)
        if candidate.get("status")!="qualified_local":
            raise Fault("candidate_not_qualified","Only mechanically qualified candidates can be proposed.")
        objects[key]=base64.b64encode(store.get(key)).decode()
        for case in candidate["cases"]:
            ref=case["reference_ref"]
            resource=store.get_json(ref)
            # Imports never export an operator filesystem path or observed subject evidence.
            if "path" in resource or not resource.get("license"):
                raise Fault("publication_private_metadata","Reference metadata has a private path or missing license; prepare a shareable reference first.")
            objects[ref]=base64.b64encode(store.get(ref)).decode()
            objects[resource["raw_ref"]]=base64.b64encode(store.get(resource["raw_ref"])).decode()
    bundle={"schema_version":1,"kind":"local-candidate-bundle","candidate_refs":candidate_refs,"objects":objects,
            "authorization":authorization,"scientific_approval":"not_conferred","created_at":utc_now()}
    raw=canonical(bundle)
    if len(raw)>MAX_BUNDLE or SECRET_BYTES.search(raw):
        raise Fault("catalog_rejected","Candidate bundle exceeds its limit or contains credential-like material.")
    for encoded in objects.values():
        if SECRET_BYTES.search(base64.b64decode(encoded)):
            raise Fault("secret_material","Credential-like reference bytes cannot be exported.")
    return raw


def import_bundle(store,raw,settings,*,log=None):
    if len(raw)>MAX_BUNDLE:
        raise Fault("catalog_rejected","Candidate bundle exceeds its byte limit.")
    try:
        bundle=parse_json(raw)
        if (not isinstance(bundle,dict) or set(bundle)!={"schema_version","kind","candidate_refs","objects","authorization","scientific_approval","created_at"}
                or bundle["schema_version"]!=1 or bundle["kind"]!="local-candidate-bundle"
                or bundle["scientific_approval"]!="not_conferred"
                or not isinstance(bundle["authorization"],str) or not 20<=len(bundle["authorization"])<=4000
                or not isinstance(bundle["candidate_refs"],list) or not 1<=len(bundle["candidate_refs"])<=100
                or any(not isinstance(key,str) for key in bundle["candidate_refs"])
                or len(set(bundle["candidate_refs"]))!=len(bundle["candidate_refs"])
                or not isinstance(bundle["objects"],dict) or len(bundle["objects"])>1000):
            raise ValueError()
        objects={key:base64.b64decode(encoded,validate=True) for key,encoded in bundle["objects"].items()}
        if any(digest(data)!=key or SECRET_BYTES.search(data) for key,data in objects.items()):
            raise ValueError()
        candidates=[]
        qualifications=[]
        used=set(bundle["candidate_refs"])
        for key in bundle["candidate_refs"]:
            candidate=parse_json(objects[key])
            refs={}
            for case in candidate["cases"]:
                ref=case["reference_ref"]
                resource=parse_json(objects[ref])
                used.update((ref,resource["raw_ref"]))
                if resource["raw_ref"] not in objects or "path" in resource:
                    raise ValueError()
                from .local_candidates import PageText
                source_bytes=objects[resource["raw_ref"]]
                if resource.get("text"):
                    original=source_bytes.decode("utf-8-sig")
                    parser=PageText()
                    parser.feed(original)
                    if resource["text"] not in {original,original[:128000],"\n".join(parser.parts)}:
                        raise ValueError()
                refs[ref]=resource
            if candidate["method_version"]==METHOD_VERSION:
                check=qualify({field:candidate[field] for field in ("name","scope","method","limitations","cases")},refs)
            else:
                from .local_evaluators import qualify as qualify_python,specification,METHOD_VERSION as PYTHON_VERSION
                if candidate["method_version"]!=PYTHON_VERSION:
                    raise ValueError()
                check=qualify_python(specification(candidate),refs,settings,log=log)
                if candidate["specification_ref"]!=check["specification_ref"]:
                    raise ValueError()
            if check["status"]!="qualified_local" or candidate["status"]!="qualified_local":
                raise ValueError()
            # Recompute mechanics; never install scientific approval from a downloaded assertion.
            if candidate.get("scientific_approval")!="provisional":
                raise ValueError()
            candidates.append(candidate)
            qualifications.append(check)
        if set(objects)!=used:
            raise ValueError()
    except (KeyError,ValueError,TypeError,UnicodeError,RecursionError):
        raise Fault("catalog_invalid","Bundle structure, content digests, provenance or qualification failed.") from None
    for data in objects.values():
        store.put(data)
    for candidate in candidates:
        save_candidate(store,candidate)
    receipt={"bundle_sha256":digest(raw),"candidate_refs":bundle["candidate_refs"],"scientific_approval_imported":False,
             "requalification_refs":[store.put_json(check) for check in qualifications]}
    if log:
        log.emit("catalog_imported",**receipt)
    return receipt


def sync_catalogs(store,settings,*,log=None):
    receipts=[]
    releases={}
    for catalog in settings["catalogs"]:
        from .execution_control import checkpoint
        checkpoint()
        cache=no_links(store.root/"catalog-cache"/(catalog["sha256"]+".json"))
        if cache.exists():
            raw=cache.read_bytes()
        elif catalog["location"].startswith("https://"):
            raw,_=fetch_bytes(catalog["location"],max_bytes=MAX_BUNDLE)
        else:
            file=no_links(catalog["location"])
            if file.stat().st_size>MAX_BUNDLE:
                raise Fault("catalog_rejected","Configured candidate bundle exceeds its size limit.")
            raw=file.read_bytes()
        if digest(raw)!=catalog["sha256"]:
            raise Fault("catalog_changed","Candidate bundle differs from its configured digest.")
        payload=parse_json(raw)
        if isinstance(payload,dict) and payload.get("kind")=="local-catalog-release":
            from .catalog_release import install,validate
            release=validate(raw)
            if release["catalog_id"] in releases and releases[release["catalog_id"]]!=catalog["sha256"]:
                raise Fault("catalog_release_conflict","Configure only one exact release of each catalog for a new run.")
            releases[release["catalog_id"]]=catalog["sha256"]
            receipt=install(store,raw,settings,log=log)
        else:
            receipt=import_bundle(store,raw,settings,log=log)
        receipt["catalog_object_ref"]=store.put(raw)
        receipts.append(receipt)
        atomic_write(cache,raw)
    return receipts
