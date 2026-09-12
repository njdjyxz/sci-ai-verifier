"""Create private operator settings from an already-installed image; no installs."""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from sci_ai_verifier.common import Fault,canonical
from sci_ai_verifier.local_config import load_configuration
from sci_ai_verifier.storage import atomic_write,no_links


def main():
    parser=argparse.ArgumentParser(description="Pin an installed Linux image for local skill execution")
    parser.add_argument("--image",required=True,help="Installed image name; saved settings use its immutable digest")
    parser.add_argument("--workspace",type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    output=no_links(args.output or args.workspace/".verifier/local-settings.json")
    try:
        if output.exists():
            raise Fault("settings_exist","Settings already exist. Edit them deliberately or choose --output for a separate configuration.")
        docker=shutil.which("docker")
        if not docker:
            raise Fault("sandbox_unavailable","Install and start Docker Desktop with Linux containers first.")
        result=subprocess.run([docker,"image","inspect",args.image],capture_output=True,timeout=20,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform=="win32" else 0)
        if result.returncode or len(result.stdout)>1024*1024:
            raise Fault("sandbox_image_unavailable","Download or build the image first; this helper never pulls or builds images.")
        item=json.loads(result.stdout)[0]
        if item["Os"]!="linux":
            raise Fault("sandbox_image_invalid","Choose a Linux image containing Python 3, /bin/sh and cp.")
        settings=load_configuration()
        settings["sandbox_image"]=item["Id"]
        settings["docker_executable"]=docker
        from sci_ai_verifier.sandbox import DockerSandbox
        # This checks the selected local endpoint and exact image; no container starts.
        DockerSandbox(args.workspace,settings).preflight()
        atomic_write(output,canonical(settings))
        print(json.dumps({"settings_path":str(output),"image_id":settings["sandbox_image"],"live_execution_tested":False},indent=2))
    except (Fault,OSError,ValueError,KeyError,IndexError,subprocess.TimeoutExpired) as error:
        print(str(error),file=sys.stderr)
        raise SystemExit(2) from None


if __name__=="__main__":
    main()
