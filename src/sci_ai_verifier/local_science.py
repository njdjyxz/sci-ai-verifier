"""Total deterministic grading predicates and independent operator review pins."""

import re
from collections import Counter

from .common import Fault,canonical,digest

POLICY={"id":"all-trials-v1","minimum_cases":3,"ab_minimum_trials":3,
        "coverage":"all planned trials","invalid":"retained; no execution grade",
        "agreement":"unanimous scored status per case","verdict":"all pass; any fail; invalid inconclusive"}
POLICY_REF=digest(canonical(POLICY))


def fingerprint(candidate):
    if candidate["method"]=="python":
        return candidate["specification_ref"]
    return digest(canonical({key:candidate[key] for key in ("name","scope","method","limitations","cases","absolute_tolerance","method_version")}))


def validate_reviews(reviews):
    required={"candidate_fingerprint","scope","reviewer","reviewed_at","provenance","grades","independent",
              "scientific_basis","coverage","uncertainty","independence","trial_policy","minimum_trials",
              "source_digest","environment_digest","model_ids"}
    seen=set()
    for review in reviews:
        if (not isinstance(review,dict) or set(review)!=required
                or any(not isinstance(review[key],str) or not 1<=len(review[key])<=8000 for key in required-{"grades","independent","minimum_trials","model_ids"})
                or any(not re.fullmatch(r"[0-9a-f]{64}",review[key]) for key in ("candidate_fingerprint","source_digest","environment_digest"))
                or not isinstance(review["model_ids"],list) or not 1<=len(review["model_ids"])<=10
                or any(not isinstance(model,str) or not 1<=len(model)<=200 for model in review["model_ids"])
                or review["independent"] is not True or review["trial_policy"]!=POLICY["id"]
                or not isinstance(review["grades"],list) or not review["grades"] or any(not isinstance(grade,str) for grade in review["grades"]) or not set(review["grades"])<=set("ABC")
                or len(set(review["grades"]))!=len(review["grades"])
                or type(review["minimum_trials"]) is not int or not 1<=review["minimum_trials"]<=20):
            raise Fault("scientific_review_invalid","Scientific reviews must identify independent authority, exact candidate/scope and bounded approved grade policy.")
        key=(review["candidate_fingerprint"],review["scope"],review["source_digest"],review["environment_digest"])
        if key in seen:
            raise Fault("scientific_review_invalid","Conflicting duplicate review scopes are not permitted.")
        seen.add(key)


def environment_digest(settings,subject):
    from .scientific import implementation_bytes
    runner=subject["adapter_id"]
    if re.fullmatch(r"[0-9a-f]{64}",runner.rsplit("-",1)[-1]):
        runner=runner.rsplit("-",1)[0]
    return digest(canonical({"model_requested":subject["model_id"],"runner":runner,"runtime_digest":digest(implementation_bytes()),
                            "settings":{key:value for key,value in settings.items() if key not in {"scientific_reviews","documentary_review"}}}))


def audit(candidate,claim,settings,selection):
    candidate_id=fingerprint(candidate)
    validate_reviews(settings["scientific_reviews"])
    review=next((item for item in settings["scientific_reviews"] if item["candidate_fingerprint"]==candidate_id and item["scope"]==claim["scope"]
                 and item["source_digest"]==selection["source_digest"] and item["environment_digest"]==selection["environment_digest"]),None)
    problems=[]
    if len(candidate["cases"])<3:
        problems.append("insufficient_distinct_cases")
    if selection["trials_per_case"]*len(candidate["cases"])>settings["max_subject_calls"]:
        problems.append("plan_exceeds_call_budget")
    return {"kind":"local-plan-audit","candidate_fingerprint":candidate_id,"selection_digest":digest(canonical(selection)),
            "source_digest":selection["source_digest"],"environment_digest":selection["environment_digest"],"scope":claim["scope"],
            "policy":POLICY,"policy_ref":POLICY_REF,"review":review,"review_ref":digest(canonical(review)) if review else None,
            "mechanically_accepted":not problems,"problems":problems,
            "scientific_authorization":"independent_operator_review" if review else "absent"}


def decide(audit,observations,cases,trials,*,synthetic=False):
    planned=len(cases)*trials
    expected={(case["case_id"],trial) for case in cases for trial in range(1,trials+1)}
    obtained=[(row["case_id"],row["trial"]) for row in observations]
    if len(obtained)!=len(set(obtained)) or set(obtained)!=expected:
        raise Fault("incomplete_trial_set","Missing or duplicate trial observations cannot become a scientific verdict.")
    statuses=[row["comparison_status"] for row in observations]
    if not set(statuses)<={"pass","fail","invalid"}:
        raise Fault("score_invalid","Scored trials contain an unknown outcome.")
    counts=Counter(statuses)
    per_case=[]
    for case in cases:
        values=Counter(row["comparison_status"] for row in observations if row["case_id"]==case["case_id"])
        per_case.append({"case_id":case["case_id"],"planned":trials,"obtained":sum(values.values()),
                         "counts":dict(values),"agreement":max(values.values())/trials})
    review=audit["review"]
    model_match=bool(review) and all(sorted(row.get("model_ids",[]))==sorted(review["model_ids"]) for row in observations)
    base=bool(review) and model_match and not synthetic and not counts["invalid"] and len(cases)>=3 and all(row["agreement"]==1 for row in per_case)
    eligibility={grade:bool(base and grade in review["grades"] and trials>=review["minimum_trials"] and (grade=="C" or trials>=3)) for grade in "ABC"} if review else dict.fromkeys("ABC",False)
    grade=next((grade for grade in "ABC" if eligibility[grade]),None)
    verdict="inconclusive" if counts["invalid"] else "fail" if counts["fail"] else "pass"
    reasons=[]
    if not review: reasons.append("independent_scientific_review_absent")
    if review and not model_match: reasons.append("observed_model_not_independently_authorized")
    if synthetic: reasons.append("synthetic_observations")
    if counts["invalid"]: reasons.append("invalid_observations_retained")
    if any(row["agreement"]<1 for row in per_case): reasons.append("trial_agreement_below_policy")
    if review and trials<review["minimum_trials"]: reasons.append("reviewed_minimum_trials_not_met")
    if trials<3: reasons.append("single_or_two_model_trials_do_not_support_A_or_B")
    return {"scientific_status":verdict if grade else None,"evidence_grade":grade,"achieved_grade_ceiling":grade,
            "grade_policy_ref":audit["policy_ref"],"grade_eligibility":eligibility,"grade_limit_reasons":reasons,
            "next_target_grade":None if grade else "D","trial_counts":{"planned":planned,"attempted":planned,
            "obtained":len(observations),"evaluated":len(observations),"invalid":counts["invalid"],"missing":0},
            "case_agreement":per_case,"ai_involvement":{"orchestration":True,"evidence_generation":"planner selected cases; review records independence","verdict":False}}
