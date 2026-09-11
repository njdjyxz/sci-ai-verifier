# Install and test the routing release

Historical 0.3.0 procedure. For current default behavior, use [the 0.4.0 guide](VERIFICATION-INSTALL.md). Select `--profile stage3` explicitly when reproducing this checkpoint with the newer source.

Version 0.3.0 retains the Stage 2 reader and adds internal claim routing and catalog lookup. Scientific execution and reports are still pending. The installed 0.2.0 acceptance remains evidence for that version only; the new package needs a separate live Chat check.

## Build and update

From this repository in PowerShell:

```powershell
python -m unittest discover -s tests -v
python scripts/build_desktop.py
```

Install `dist/scientific-verifier-0.3.0.mcpb` and upload `dist/scientific-verifier-skill-0.3.0.zip` using the extension/skill settings described in [the original guide](INSTALL.md). Keep the Python interpreter, submission directory and data directory from the existing installation. Ensure the extension is enabled and start a fresh Chat. Updating the source checkout alone does not replace the installed package. The builder performs no app setup.

The public prompt can be short:

> Verify this skill: `D:\Su Lab\verifier-submissions\reference-claim`. Use Scientific Verifier and follow its returned state. Explain the work completed and any remaining limitation.

Use an actual path inside the configured submission directory. Extraction, classification and lookup are internal steps; the user does not choose a separate extraction feature.

## Expected current result

The default reviewed registries are empty. For a nonempty manifest, Claude reads the empty taxonomy, proposes a bounded type, and requests a lookup for each claim. Python records `implementation_required` per claim and stops at `stage3_complete`, with `verification_complete: false`. This does not mean the scientific claim failed. Zero claims close at the same checkpoint without selection calls.

Below `<data directory>/.verifier/runs/<run-id>/`, inspect `source-snapshot.json`, `claim-manifest.json`, `catalog-lock.json`, `routing.json`, and any `operational-outcomes/`. The journal under `events/` owns the committed state. Routing files appear only once routing starts. Candidate scientific entries are deliberately not enabled as approved: see [the chemical mass pilot](../reviews/CHEMICAL-MASS-PILOT.md).

## Catalog releases without reinstalling

Build local review releases with `scripts/catalog_release.py build`; see [the catalog contract](../skills/scientific-verifier/references/stage3-contract.md). The initial checked-in `catalog/` mirrors the empty reviewed registries. Local source does not establish GitHub publication.

After a reviewed catalog commit is published, replace both placeholders with its full commit SHA and independently obtained manifest SHA-256:

```powershell
python scripts/catalog_release.py fetch --workspace 'D:\Su Lab\sci-ai-verifier' --commit '<40-character commit SHA>' --manifest-sha256 '<64-character manifest SHA-256>'
```

Use your extension's actual data directory for `--workspace`. Retrieval is fixed to this project's repository. The utility activates only fully verified compatible content. Add `--offline` for an already verified exact cache; absent or altered data fails explicitly. Existing runs retain their immutable pins.

For developer testing, `desktop/server.py serve --profile stage2 ...` retains the extraction stop. `--profile stage3 --catalog <local-release-directory>` selects an explicit local fixture release; it is not proof of human review. These are operator settings, never model-controlled tool arguments.

## Live acceptance to record

Record app version, visible model label, package hash and run IDs. Inspect Chat tool activity separately from the journal. Confirm no invented isotope convention in extracted claims, actual routing tool calls, a durable missing-capability outcome, and identical catalog pins after resume. Automated tests cannot establish these app/model observations. Preserve the earlier Stage 2 acceptance results.
