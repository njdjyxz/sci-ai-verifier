# Version 0.4.0: complete fixture workflow and reports

This describes the stricter chemical profile. The current 0.5.0 package defaults to the [general safe-skill demo](DEMO-INSTALL.md); use `--profile verification` explicitly to run this chemical workflow. Install the current 0.5.0 archives rather than the superseded versioned files below.

The implementation can be tested before a live scientific skill is connected. This version adds planning, resource locks, bundle validation, audit, configurable subject observations and final reports. The chosen execution mode is synthetic fixtures; no API key or paid subject call is required.

## Build and run the local demo

From the repository directory:

```powershell
python -m unittest discover -s tests -v
python scripts/run_fixture_demo.py
python scripts/run_fixture_demo.py --variant wrong
python scripts/run_fixture_demo.py --variant invalid
python scripts/build_desktop.py
```

Each demo creates a new directory under `.verifier/fixture-demos/` and prints paths to its reports, synthetic catalog and subject fixture. Open the returned `report_markdown` file first. Correct observations yield a synthetic pass/C; a wrong mass yields fail/C; malformed observations produce a retained sample and an `assessor_unavailable` outcome with no grade. These test the verifier, not a live skill.

The demo exercises routing, target planning, resource search/lock, bundle construction/validation, run-local registration, a new registered plan revision, audit, two observations per case, per-trial scoring, result commitment and reporting. Fixture answer files stay outside the submitted directory. The suite separately checks interruption, cancellation, stale authority, mixed claims and recovery.

## Install the current extension

Install `dist/scientific-verifier-0.4.0.mcpb` and replace the uploaded skill with `dist/scientific-verifier-skill-0.4.0.zip`. Use the same Python, submission folder and result folder settings described in [the original installation guide](INSTALL.md). Enable the extension and start a fresh Claude Desktop Chat. Updating source code or rebuilding archives alone does not replace the installed extension.

The default reviewed catalog remains empty. **Verify this skill: <path inside your submission folder>** should end with a report accounting for unavailable evaluators. A zero-claim submission also produces a report. It must not claim scientific success from an empty catalog. This tests the ordinary app path without treating synthetic approvals as production authority.

## Optional app fixture configuration

The local demo creates `claude_desktop_fixture_config.example.json`. It uses the source launcher and points to that demo's exact synthetic catalog and subject file. This is a reviewable manual example, not an installed setting. The fixture launcher has explicit `--profile verification`, `--catalog` and `--subject-fixture` options. Use a separate test data directory/server entry, enable only the intended verifier server for the test, and retain the configuration/launcher version with the acceptance record.

For this configuration, the prompt is:

```text
Verify this skill: D:\Su Lab\sci-ai-verifier\examples\chemical-mass-fixture\submitted
```

Inspect both report files. Every fixture result must remain visibly synthetic. A fresh Chat should resume the returned run ID with the same report and pins. The demo supplies scripted semantic choices; only the app test checks whether Claude makes grounded claims, selects the intended scope and follows the workflow correctly.

## Release acceptance

Local tests and an extracted-package protocol run do not establish live app behavior, independent scientific approval or actual provider performance. Record the new package hash, installed file identities, visible app/model label, run IDs, reports and conversation inspection separately in [APP-ACCEPTANCE.md](APP-ACCEPTANCE.md). Keep the earlier 0.2.0 evidence intact.

Before using a real subject, review the catalog's scientific scope, NIST resource pins, seven-case coverage, tolerance and C-only policy. A host-provisioned live adapter must keep reference answers separate, enforce its own deadline/isolation, pin configuration and return attributable observations. That provider is deliberately not enabled in this fixture delivery. Independent D assessment and broader scientific methods need separate implementations and review.
