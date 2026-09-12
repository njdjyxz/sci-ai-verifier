"""Print the exact reviewable local grading policy and documentary rubric."""
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.local_science import POLICY,POLICY_REF
from sci_ai_verifier.documentary import RUBRIC,RUBRIC_REF
if __name__=="__main__":
    print(json.dumps({"trial_policy":POLICY,"trial_policy_ref":POLICY_REF,"documentary_rubric":RUBRIC,"rubric_ref":RUBRIC_REF},indent=2))
