"""Readable failure evidence without changing the authoritative run state."""

from html import escape

from .common import canonical,utc_now
from .storage import atomic_write


def write_partial_report(store,run_id,code):
    state,_=store.read(run_id)
    claims=[]
    for claim_id,work in state.get("local_work",{}).items():
        records={field:store.get_json(work[field]) for field in ("result_ref","outcome_ref","comparison_ref") if work.get(field)}
        claims.append({"claim_id":claim_id,"state":state["claim_states"][claim_id],"records":records})
    document={"run_id":run_id,"verification_complete":False,"error_code":code,"claims":claims,
              "journal_revision":state["revision"],"generated_at":utc_now(),
              "note":"Partial diagnostic report. Scientific records above retain their original meaning; unfinished claims have no new verdict. Inspect subject-runs for requests interrupted before a journal commit."}
    directory=store.run_dir(run_id)
    atomic_write(directory/"partial-report.json",canonical(document))
    lines=["# Incomplete verification","","Run: "+run_id,"","Stopped: "+escape(code),"",document["note"],""]
    for claim in claims:
        lines += ["- "+escape(claim["claim_id"])+": "+escape(claim["state"])]
    atomic_write(directory/"partial-report.md",("\n".join(lines)+"\n").encode())
    return {"partial_json_path":str(directory/"partial-report.json"),"partial_markdown_path":str(directory/"partial-report.md")}
