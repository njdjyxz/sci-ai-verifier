"""Generated scoring programs: container-only controls and pinned specifications."""

import base64
import tempfile
from pathlib import Path

from .common import Fault,canonical,digest
from .local_candidates import safe_payload
from .mcp import parse_json
from .sandbox import DockerSandbox
from .storage import atomic_write

METHOD_VERSION="local-python-comparison-1"


def validate_spec(spec,references):
    required={"name","scope","method","code","limitations","cases","controls","absolute_tolerance","relative_tolerance"}
    if not isinstance(spec,dict) or set(spec)!=required or spec["method"]!="python" or len(canonical(spec))>200000:
        raise Fault("evaluator_spec_invalid","Use the documented bounded Python evaluator specification.")
    safe_payload(spec)
    if any(not isinstance(spec[key],str) or not 1<=len(spec[key])<=32000 for key in ("name","scope","code","limitations")):
        raise Fault("evaluator_spec_invalid","Evaluator text fields must be bounded and nonempty.")
    from .local_candidates import number
    try:
        if any(number(spec[key])<0 for key in ("absolute_tolerance","relative_tolerance")):
            raise ValueError()
    except (ValueError,TypeError):
        raise Fault("evaluator_spec_invalid","Tolerances must be nonnegative bounded decimal strings.") from None
    cases=spec["cases"]
    if not isinstance(cases,list) or not 3<=len(cases)<=100:
        raise Fault("evaluator_spec_invalid","Provide 3 to 100 distinct source-backed cases.")
    ids,inputs=set(),set()
    for case in cases:
        if (not isinstance(case,dict) or set(case)!={"case_id","input","expected","reference_ref","source_quote","applicability"}
                or any(not isinstance(value,str) or not 1<=len(value)<=8000 for value in case.values())
                or case["case_id"] in ids or case["input"] in inputs):
            raise Fault("evaluator_spec_invalid","Cases need unique IDs/inputs and bounded fields.")
        ref=references.get(case["reference_ref"])
        if not ref or case["source_quote"] not in ref.get("text","") or case["expected"].strip() not in case["source_quote"]:
            raise Fault("evaluator_reference_invalid","Expected answers must be traceable to exact imported reference quotes.")
        ids.add(case["case_id"])
        inputs.add(case["input"])
    controls=spec["controls"]
    groups={"positive","negative","boundary","invalid","held_out"}
    if not isinstance(controls,list) or not 5<=len(controls)<=100:
        raise Fault("evaluator_controls_invalid","Provide bounded positive, negative, boundary, invalid and held-out controls.")
    for control in controls:
        if (not isinstance(control,dict) or set(control)!={"case_id","actual","expected_status","group"}
                or any(not isinstance(value,str) for value in control.values())
                or control["case_id"] not in ids or control["expected_status"] not in {"pass","fail","invalid"}
                or control["group"] not in groups or not isinstance(control["actual"],str) or len(control["actual"])>16000):
            raise Fault("evaluator_controls_invalid","Each control needs a known case, bounded observation and expected status.")
    if ({control["group"] for control in controls}!=groups or
            not {"pass","fail","invalid"}<={control["expected_status"] for control in controls}):
        raise Fault("evaluator_controls_invalid","All control classes and all possible statuses must be tested.")
    return spec


def score(spec,case,actual,settings,*,log=None,sandbox_factory=DockerSandbox,artifacts=None):
    if not settings.get("sandbox_image"):
        raise Fault("sandbox_configuration_required","Python evaluators require a pinned computational environment.")
    with tempfile.TemporaryDirectory(prefix="sci-verifier-evaluator-") as temporary:
        source=Path(temporary)
        atomic_write(source/"evaluator.py",spec["code"].encode("utf-8"))
        from .ingest import valid_relative
        artifact_manifest=[]
        total=0
        for item in artifacts or []:
            if not valid_relative(item["path"]):
                raise Fault("artifact_invalid","Evaluator artifacts need valid relative paths.")
            raw=base64.b64decode(item["base64"],validate=True)
            total+=len(raw)
            if total>settings["max_artifact_bytes"] or len(raw)>settings["max_file_bytes"] or len(artifact_manifest)>=settings["max_artifacts"]:
                raise Fault("artifact_limit","Evaluator artifact inputs exceed configured limits.")
            atomic_write(source/"observed"/item["path"],raw)
            artifact_manifest.append({"path":item["path"],"sha256":digest(raw),"bytes":len(raw)})
        packet={"input":case["input"],"actual":actual,"expected":case["expected"],
                "absolute_tolerance":spec["absolute_tolerance"],"relative_tolerance":spec["relative_tolerance"],
                "artifacts":artifact_manifest,"artifact_root":"/work/observed"}
        with sandbox_factory(source,settings,timeout=45,log=log) as sandbox:
            result=sandbox.command("python3 -I /work/evaluator.py",stdin=canonical(packet).decode(),timeout=30)
            try:
                value=parse_json(result["stdout"])
                if result["exit_code"] or not isinstance(value,dict) or set(value)!={"status"} or value["status"] not in {"pass","fail","invalid"}:
                    raise ValueError()
            except (ValueError,TypeError,UnicodeError,RecursionError):
                raise Fault("evaluator_failed","The scoring program must return one JSON object containing status pass, fail or invalid.") from None
            return {"status":value["status"],"code_sha256":digest(spec["code"].encode()),"image_id":sandbox.image,
                    "packet_sha256":digest(canonical(packet))}


def qualify(spec,references,settings,*,log=None,scorer=None):
    validate_spec(spec,references)
    receipts=[]
    cases={case["case_id"]:case for case in spec["cases"]}
    for control in spec["controls"]:
        result=(scorer or score)(spec,cases[control["case_id"]],control["actual"],settings,log=log)
        receipts.append({**control,"result":result,"passed":result["status"]==control["expected_status"]})
    qualified=all(item["passed"] for item in receipts)
    return {**spec,"schema_version":1,"method_version":METHOD_VERSION,"status":"qualified_local" if qualified else "rejected",
            "specification_ref":digest(canonical(spec)),"controls_receipts":receipts,
            "scientific_approval":"provisional","qualification_limitations":[
                "Generated scoring code passed specified mechanical controls only." if qualified else "Generated scoring code failed a specified control.",
                "The planner selected cases and controls; held-out labels alone do not prove scientific independence.",
                "Scientific grading requires an independent operator-supplied review bound to this exact specification and scope."]}


def specification(candidate):
    keys=("name","scope","method","code","limitations","cases","controls","absolute_tolerance","relative_tolerance")
    return {key:candidate[key] for key in keys}
