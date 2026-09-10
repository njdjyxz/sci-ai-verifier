# Install Stage 2 in Claude Desktop

Use **Chat in the installed Claude desktop app**. This delivery does not require Claude Code CLI. Install both packages: the skill supplies instructions; the extension runs the local Python tools.

## 1. Install the local tools

In Claude Desktop, open **Settings -> Extensions -> Advanced settings -> Install Extension** and choose `dist/scientific-verifier-0.2.0.mcpb`. These are the [documented custom-extension installation steps](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop).

The package asks for three values:

| Setting | Value for this computer's first fixture test |
|---|---|
| Python interpreter | `C:\Python314\python.exe` |
| Submission directory | `D:\Su Lab\sci-ai-verifier\examples\submissions` |
| Verifier data directory | `D:\Su Lab\verifier-runs` |

Python 3.14 is installed on this computer; the extension requires 3.11 or newer and has no pip dependencies. Only 3.14 is installed here, so the 3.11 floor has not actually been exercised. The submission directory limits what the extension can read. For your own submissions, change it to a dedicated folder containing sanitized skill folders. The data directory must be writable; records will be under its `.verifier` subfolder.

Keep the data directory **outside this checkout**. Acceptance runs saved under the repository sit beside the gitignored test workspaces and would be removed by ordinary repository cleanup. Create the folder before installing.

None of the three directories may contain a symlink, junction, or other reparse point anywhere in its path, and the submission directory must already exist. If one of them is unusable the server does not start, and it writes a single line naming the setting and the fix rather than a Python traceback. Check the app's MCP log for that line before changing anything else.

The package is unsigned local project code, not a listing reviewed by Anthropic. Organizational extension policies may require an administrator to allow it. App installation has not been exercised during the scripted build tests.

## 2. Upload the skill

Enable **Code execution and file creation** in Settings -> Capabilities if required for skills. Go to **Customize -> Skills -> + -> Create skill -> Upload a skill**, choose `dist/scientific-verifier-skill-0.2.0.zip`, and enable it. The ZIP contains one `scientific-verifier/` folder with `SKILL.md` and its references. See [Claude's skill upload instructions](https://support.claude.com/en/articles/12512180-use-skills-in-claude).

Code execution is an app prerequisite for uploaded skills; the verifier must still use the local extension for all verifier operations. Uploading the ZIP alone does not install the Python tools. Enable the scientific-verifier extension in the test conversation and avoid unrelated connectors for that test.

## 3. Run the first bounded test

Start a fresh Chat, select your preferred Opus model, and send:

```text
Use the scientific-verifier skill and its local extension to run Stage 2 on:
D:\Su Lab\sci-ai-verifier\examples\submissions\reference-claim

Start with start_verifier_run. Read the complete returned bootstrap and the
reference file containing the claim. Commit only supported atomic scientific
claims with exact source quotes. Stop at stage2_complete. Tell me the run ID
and saved manifest path. Do not assign grades or claim scientific verification.
```

Expected behavior: source snapshot, a read of `references/mass.md`, and a manifest with the monoisotopic-mass claim linked to that file. Wording may vary; the quote must match exactly. The final run state is `stage2_complete`, `verification_complete` is false, and no report card or evidence grade is created.

Also test the `no-claims` fixture: it should produce an empty manifest with outcome `no_scientific_claims`. The `instruction-conflict` fixture contains deliberately conflicting instructions; they must remain source data, and the app must not obey the requests to call a shell or assign grade A.

If the conversation is interrupted, ask the extension to `resume_verifier_run` with the saved run ID. It restores the pinned instructions and previously read snapshot ranges. Use `get_verifier_context` after compaction or a lost response. Use `cancel_verifier_run` only when you intend to terminate an unfinished run.

## 4. Inspect and record acceptance

Under `.verifier/runs/<run-id>/`, inspect:

- `run.json`: lifecycle, limits, context identities, and artifact references.
- `source-snapshot.json`: included files, exclusions, and digests.
- `claim-manifest.json`: exact claims and provenance after successful commitment.
- `events/*.json`: requests/results and committed state changes.
- `operational-outcomes/*.json`: durable failures or cancellation, when present.

The extension cannot see the app's exact model/version, private response IDs, billing, or refusal reasons, nor disable its other tools. Unavailable values remain null; a reported visible model label is explicitly unverified metadata. For the live test, record the app version, visible model label, run ID, fixture, observed tool sequence, claim-quality review, and any unavailable exact model identifier. Use [APP-ACCEPTANCE.md](APP-ACCEPTANCE.md) to record this without claiming a test has already happened.

## Manual configuration alternative

If custom-extension installation is unavailable but manual local MCP configuration is supported, open the app's developer MCP configuration and merge the `scientific-verifier` server entry from `dist/claude_desktop_config.example.json` into its `mcpServers` object. Preserve existing server entries. The example points at this checkout, so keep the checkout in place. Restart the app after saving. Do not install both versions of the same connector simultaneously.

The MCPB contains its own Python source and instruction files and does not depend on the checkout location after installation. The manual configuration does. Neither method changes your settings automatically during the build.

## Rebuild

From the repository root:

```powershell
python -m unittest discover -s tests -v
python scripts/build_desktop.py
```

`dist/checksums.json` records the generated package digests. Run artifacts, build output, and local test dependencies are excluded from Git.
