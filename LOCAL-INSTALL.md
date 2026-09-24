# Set up the verifier on your Windows PC

**Yes, you can keep using Claude Code in the desktop app.** Install its
command-line program once as well: this verifier uses it to start separate test
sessions. You can then request verification in the app, without typing commands
for everyday use.

This guide is for **version 0.7.0**, your Claude subscription, and the **Code** tab.
The older verifier desktop extensions are compatibility packages; installing one
does not set up this version's `verify_skill` action.

This build adds computational execution, resources, generated evaluators, repeated
trials, a negotiated evidence grade with an independent critique, independent
documentary assessment and workflow logs. **Live acceptance is pending your manual tests below.** The
[development plan](DEVELOPMENT-PLAN.md) remains the complete project checklist and its
latest entry is the current roadmap; automated fixtures do not establish scientific
acceptance.

The examples use your current folder, `D:\Su Lab\sci-ai-verifier`, and Python at
`C:\Python314\python.exe`. On another PC, replace those paths with its actual
locations. Python must be 3.11 or newer; no extra Python packages are needed.

“Local” means the program and reports live on your PC. Skill text and test inputs
still go to Claude's hosted models and use your available Claude usage.

**What is verified so far** is recorded in one place: the "Current state" section of
the [development plan](DEVELOPMENT-PLAN.md), which lists every live run and which grade
branches each has exercised. It is not repeated here, because a copy drifts. Setup
checks alone do not establish live acceptance, and neither does a single run that
completes.

## One-time setup

**Upgrading an older verifier?** Read [Updating or removing the connection](#updating-or-removing-the-connection)
first. A full uninstall is unnecessary; keep your project, settings and reports.

### 1. Open PowerShell and check Python

Click **Start**, type **PowerShell**, and open it. Paste the command boxes there,
not into a Claude conversation. Press **Enter** after each box.

```powershell
& "C:\Python314\python.exe" --version
```

Expect `Python 3.14.0` on this PC. On another PC, locate its Python installation
first; if needed, use the [official Windows downloads](https://www.python.org/downloads/windows/).

### 2. Install the Claude Code background program

Check whether it is already available:

```powershell
claude.exe --version
```

If it prints **2.1.248 or newer**, skip installation. Our verifier needs that
minimum version for its restricted execution mode. If the command is not found:

```powershell
winget install Anthropic.ClaudeCode
```

Close PowerShell, reopen it, and repeat `claude.exe --version`. To update an older
WinGet installation, run `winget upgrade Anthropic.ClaudeCode`. If WinGet is
unavailable, follow Anthropic's [Windows installation instructions](https://code.claude.com/docs/en/setup#install-claude-code).
Use a native Windows installation for this guide.

### 3. Give the verifier access to your subscription

Desktop sign-in alone is insufficient for our separate test sessions. Generate
a token, a private sign-in credential for those sessions:

```powershell
claude.exe setup-token
```

Follow the sign-in instructions and copy the resulting token. This requires a
Claude subscription; see the [token command reference](https://code.claude.com/docs/en/cli-reference).
Keep the token out of chat messages, repository files, and screenshots.

In the desktop app's **Code** tab, open the environment selector, hover over
**Local**, and click its **gear**. Add and save:

| Name | Value |
| --- | --- |
| `SCI_VERIFIER_OAUTH_TOKEN` | Paste the generated token |

Anthropic documents encrypted storage for this editor's values, supplied to local
sessions. See [desktop environment setup](https://code.claude.com/docs/en/desktop#local-sessions).
The next step passes this value to the verifier. Keep its command's placeholder
exactly as written; do not replace it with your token.

### 4. Prepare the environment for scripts and data

Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/)
using its Windows installer and follow its WSL 2 setup/restart instructions.
Open Docker Desktop and wait until its engine is running. Use **Linux containers**.
Docker gives each test a separate disposable workspace; Claude itself still uses
your locally installed CLI and subscription.

In PowerShell, run:

```powershell
docker version
docker pull python:3.12-slim
& "C:\Python314\python.exe" "D:\Su Lab\sci-ai-verifier\scripts\configure_local.py" --image python:3.12-slim
```

The first command should show both client and server information. The second
downloads the [official Python image](https://hub.docker.com/_/python). The helper
then writes `.verifier\local-settings.json` and prints its exact image ID. That ID
is pinned for future tests; verification does not download images or install
packages. Keep Docker Desktop running while testing computational skills.

This initial image provides Python's standard library. If a skill needs NumPy,
R, a chemistry toolkit or another package, prepare an image containing those
dependencies first; see [dependencies and configuration](LOCAL-CONFIG.md).
Missing packages produce a limitation, not an invented result. If
`.verifier\local-settings.json` already exists from your previous setup, keep it
and check its image/settings before reusing it. The helper deliberately does not
overwrite an existing configuration.

### 5. Connect the verifier to Claude Code

Back in **PowerShell**, paste the entire box. If the connection already exists
and its settings need changing, remove the old registration using the
[upgrade instructions](#updating-or-removing-the-connection) first:

```powershell
$verifierClaude = (Get-Command claude.exe -ErrorAction Stop).Source
claude.exe mcp add --env 'CLAUDE_CODE_OAUTH_TOKEN=${SCI_VERIFIER_OAUTH_TOKEN:-}' --transport stdio --scope user scientific-verifier-local -- "C:/Python314/python.exe" "D:/Su Lab/sci-ai-verifier/scripts/verify.py" serve-local --workspace "D:/Su Lab/sci-ai-verifier" --config "D:/Su Lab/sci-ai-verifier/.verifier/local-settings.json" --claude-executable "$verifierClaude" --model claude-opus-5 --timeout 5400
```

Expect an **Added** message. The first line finds the installed Claude program;
the second registers a tool connection named `scientific-verifier-local` in your
personal Claude Code configuration. It is available across projects. The saved
configuration contains a credential placeholder, not the token itself.

`--model claude-opus-5` pins an exact model rather than the `opus` alias. This
matters more than it looks. A verdict is evidence about *one* model running the
skill, so the runner freezes the model identity at the first trial and refuses a
trial set containing two. An alias is free to resolve to a different version
partway through a run, and when that happened on 2026-09-18 it voided a claim that
had already settled at grade B with the critique's support. Pinning removes that
cause, but not every cause: on 2026-09-21, with the pin in place, the CLI served
part of one subject session from a different model, and the runner voided that
claim too. It is correct to — a grade cannot describe two models — but expect an
occasional `subject_model_changed` even when the pin is right.

Changing the pinned model starts a new series. Runs on one model are not directly
comparable with runs on another, so note the switch when reading results across it.

**Before changing the pin, check that this CLI can run the new model.** A newer model
can require a newer Claude Code than you have, and WinGet may not offer that version
yet even when Anthropic has released it — `claude update` defers to WinGet for a
WinGet-managed install. Run:

```powershell
claude.exe -p "Reply OK" --model <new-model-id>
```

If the output contains `unrecognized_model`, this CLI cannot serve that model; keep
the current pin. `Not logged in` is expected from a plain PowerShell window, because
the verifier's token is supplied only through the desktop app, and the model check
happens before sign-in, so `unrecognized_model` is the line that matters. The verifier
now makes the same check itself before every run and stops with `model_unavailable`
if it fails, so a wrong pin no longer costs a run, only a few seconds; checking first
still saves you the restart.

`--timeout 5400` gives each verification 90 minutes. Without it the limit is 30
minutes, which measurement shows is not enough: a five-claim skill took about 50
minutes of real work, and an earlier run of the same skill was cut off mid-claim at
the 30-minute default and produced only a partial report. Accepted values are 1 to
7200 seconds. The timeout covers the whole attempt including setup, so raise it
further for larger skills.

“MCP” is the connection that lets Claude call the verifier. This command follows
Anthropic's [local tool setup](https://code.claude.com/docs/en/mcp#option-3-add-a-local-stdio-server)
and [environment-variable configuration](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson).
No manual JSON editing is needed. **Added** confirms registration, not live execution.

### 6. Start a fresh desktop session

Restart the app. In **Code**, choose **Local** and select
`D:\Su Lab\sci-ai-verifier` as the project folder. Start a new session to load the
connection. Desktop and CLI tool configurations are shared, as documented
[here](https://code.claude.com/docs/en/desktop#shared-configuration).

To check the connection before running a skill, send:

> Check whether scientific-verifier-local provides the verify_skill tool. Do not start a verification yet.

Expect **`verify_skill`**. If it is missing, use the troubleshooting table below.
A connected tool still needs a real run to confirm token validity, model access,
and test-session execution.

## Everyday use in the desktop app

Choose a small skill folder containing `SKILL.md`. In File Explorer, open that
folder, click its address bar, and copy the path. Replace this example path:

> Use scientific-verifier-local to verify this skill: D:\My Skills\my-skill. Show me the saved report and its limitations.

Approve the verifier tool if Claude asks. Leave the session running; verification
allows up to the timeout registered in step 5, 90 minutes with the command above and
30 minutes without it. Expect real work to take tens of minutes for a handful of
claims. You do not need to run extraction, discovery, or evaluation separately.

The result includes report paths. With the setup above, reports live here:

```text
D:\Su Lab\sci-ai-verifier\.verifier\runs\<run-id>\
```

Each run gets its own ID. Open **`report-card.md`** for the readable report;
`report-card.json` is the structured version. The report shows inputs, expected
and actual answers, references, outcomes, and limitations.

Completion is not automatically a scientific pass. Scripts, binary inputs and
generated files use the configured container; the installed comparison methods and
generated Python evaluators compare the observations. The default is three trials per case.
Generated files have saved paths in the JSON report.

The evidence grade in the report says how strong the evidence was, not whether
anyone endorses the skill, and you never enter or approve one. A means the answers
came from a source the verifier itself retrieved and were scored by installed code;
B means a dataset you pinned or a generated evaluator did the scoring; C means the
comparison is reproducible but the traceability, independence or trial count is
weaker; D means a fresh assessor judged cited sources and execution accuracy stays
unverified; U means no acceptable evidence was found. The verifier proposes a grade
and a separate session that never saw the planning critiques it and can only lower
it, so the report shows the proposal, the runner's ceiling and that critique. No
grade is fabricated during setup.

Network downloads and external apps need explicit settings. Installed apps are
not automatically connected. See
[app adapters and grading](LOCAL-CONFIG.md#how-the-evidence-grade-is-decided) when
you are ready to configure them.

Every attempt also returns **log paths**, even if setup fails before a run exists:

```text
D:\Su Lab\sci-ai-verifier\.verifier\attempts\<attempt-id>\workflow.md
```

Open `workflow.md` for the timeline, or `workflow.jsonl` for structured events.
It records visible process/tool activity, outcomes, errors and timing. It omits
private model reasoning and redacts recognized credentials. Entries have size
limits and disclose truncation; recorded events have a 32 MiB total limit. Keep logs private: they may include your skill
text, inputs, outputs and local paths. The immutable run journal remains the
authority for scientific results.

If a run stops or fails, retain its run ID for diagnosis. Asking to verify again
starts a new run; prior evidence is retained and uncertain tests are not replayed
automatically.
The desktop connection accepts cancellation while work is running; use its Stop
control. Allow a short time for cleanup, then inspect the saved attempt log.
Clients that request progress updates receive stage notifications. One verification
runs at a time per connection. The configured timeout applies to the whole attempt,
including setup and catalog checks; cleanup and partial reporting can finish after
that deadline.
If the planner stops after a run has begun, `partial-report.md` and
`partial-report.json` summarize the incomplete run when its storage remains
available. They do not claim verification completed.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| `claude.exe` is not recognized | Complete step 2 and reopen PowerShell. Having the desktop app alone does not guarantee a standalone executable is available. |
| `claude_version_unsupported` | Update the standalone installation to at least 2.1.248. |
| “Git is required” in Code | Install [Git for Windows](https://git-scm.com/downloads/win) and restart the app. |
| The verifier tool is missing | Confirm step 5 printed **Added**, start a fresh local Code session, and check whether `scientific-verifier-local` is disabled. |
| The connection name already exists | To update the earlier setup, run `claude.exe mcp remove --scope user scientific-verifier-local`, then repeat steps 5–6. This removes the connection, not saved reports. |
| `authentication_required` before the planner starts | Check the exact variable name and token in step 3. Save and start a new session. |
| Planner runs, but subject or assessor returns `authentication_required` | Confirm the connection registers the `CLAUDE_CODE_OAUTH_TOKEN` placeholder from step 5, then fully restart Claude and start a new local Code session. Keep the existing token. An early build did not pass credentials to its internal sessions; if you are on source older than 0.7.0, update it. |
| Expired-token, sign-in, or usage-limit error | Renew the token through step 3 or wait for eligible usage. The verifier never switches to API billing automatically. |
| `source_missing` | Supply the full path to an existing skill folder or its `SKILL.md`. |
| `planner_incomplete` or another incomplete result | Save the run ID and error. The run did not finish; setup checks cannot diagnose every live-model failure. |
| `sandbox_unavailable` or no Docker server information | Open Docker Desktop, wait for its engine, and use Linux containers. |
| `sandbox_configuration_required` | Complete step 4 and ensure the connection includes the settings path. |
| `sandbox_image_unavailable` or `sandbox_start_failed` | Check Docker is running and the pinned image still exists. Retain the log; do not change an active run's settings. |
| A Python import/package error | Prepare a new image with that dependency, pin it to a new settings file, then start a new verification. |
| `resource_not_authorized` or `app_not_authorized` | Configure the exact resource host or a reviewed read-only app adapter in LOCAL-CONFIG.md. |
| `assessor_unavailable` | The independent documentary session did not complete. This is an operational problem, not grade U. |
| `critic_unavailable` | The independent grade critique session did not complete. The claim is recorded as an operational limitation; it does not become an ungraded pass. |
| `critic_response_invalid` or `assessor_response_invalid` | That session answered outside its fixed rubric, so its reply could not be recorded. Operational, never a grade. Keep the attempt log: the reply is in it, and a reply the verifier should have accepted is a defect worth reporting. |
| `subject_refused` | Anthropic's safety classifiers declined the test question, naming the category. Nothing was observed, so this reports that the provider would not answer, never that the skill failed. It is not retried, because the frozen case input would refuse again. Its trials stay missing rather than being replaced. |
| `claude_incomplete` | A test session exited without a complete observation and was not retried. Check the attempt log for that session before assuming the skill is at fault. |
| `subject_model_changed` | The observed model identity changed partway through one claim's trials. A grade describes one subject, so the claim stops rather than mixing them. |
| `subject_response_invalid` | A test session returned no usable text, or did not explicitly invoke the pinned skill. |
| `evaluator_failed` | The scoring program did not print exactly one JSON object with a `status` of pass, fail or invalid. Check the evaluator's own output in the log. |
| `local_grade_proposal_refused` with `above_evidence_ceiling` | The planner proposed a grade its own recorded facts cannot support. It should strengthen the design or propose the stated ceiling; no action is needed from you, and no critique session is spent. |
| `local_grade_proposal_refused` with `below_evidence_ceiling` | The planner proposed a weaker grade than its evidence supports. Aiming low is refused for the same reason as overclaiming. |
| `local_design_unchanged` or `local_grade_rounds_exhausted` | The planner re-proposed a grade on a design already critiqued, or spent its negotiation budget. Neither consumes a session; the claim settles or continues without one. |
| `source_not_authorized` | The path given to the verifier is not the one you authorized for this run. Supply the exact folder you named when starting. |
| `verification_timeout` | The attempt hit the registered timeout. Raise `--timeout` in step 5 and re-register, then start a new verification. Saved evidence and a partial report are retained. |
| `stronger_evidence_available` | The planner tried to conclude documentarily while holding a qualified candidate it had not run. It must run it or explain why it does not apply. |
| `workflow_log_unavailable` | Check the data folder is writable and disk space is available; keep any existing attempt folder for diagnosis. |

Share the error code and run ID when asking for help, without credentials.

## Optional: use PowerShell directly

The desktop editor's saved variable is not automatically available in a separate
PowerShell window. Paste the token into this hidden prompt; it will not appear
in the command text:

```powershell
$verifierSecret = Read-Host "Paste your Claude token (hidden)" -AsSecureString
$env:CLAUDE_CODE_OAUTH_TOKEN = [System.Net.NetworkCredential]::new("", $verifierSecret).Password
Remove-Variable verifierSecret
& "C:\Python314\python.exe" "D:\Su Lab\sci-ai-verifier\scripts\verify.py" doctor --config "D:\Su Lab\sci-ai-verifier\.verifier\local-settings.json"
```

Look for **`"status":"ok"`**. `doctor` checks the executable, version, and presence
of a credential, plus the configured local container image. It uses no model
allowance and does **not** validate the token with Claude or execute a live test.

Then, in the same window, replace the example skill path and run:

```powershell
& "C:\Python314\python.exe" "D:\Su Lab\sci-ai-verifier\scripts\verify.py" verify "D:\My Skills\my-skill" --workspace "D:\Su Lab\sci-ai-verifier" --config "D:\Su Lab\sci-ai-verifier\.verifier\local-settings.json" --timeout 5400
```

Press **Ctrl+C** to stop. Close PowerShell when finished; the token set above
lasts only for that process and its children.

Advanced options: `--model opus`, `--timeout <seconds>` and
`--claude-executable "C:\path\to\claude.exe"`. The timeout accepts 1 to 7200 seconds
and defaults to 1800, which is usually too short; `--timeout 5400` matches the
registered connection above. The default requested model is `opus`; receipts also
record actual returned model IDs.

API users must supply `ANTHROPIC_API_KEY` instead and add `--auth api` to
`verify` or `serve-local`. API mode has separate billing. Never place the actual
token or key in command arguments or repository configuration files.

## Your manual acceptance tests

You will perform these live tests yourself. Start with a small skill whose expected
behavior you understand. Run it once from the desktop and once from PowerShell
using the commands above. Use copies when deliberately introducing errors.

| Test | What to check in the report and workflow log |
| --- | --- |
| First small skill | The planner calls internal verifier tools; each subject explicitly invokes `verifier-subject:submitted`; real model/session IDs are recorded. |
| Repeated trials | Three observations per selected case by default, with distinct sessions, individual scores, and planned/attempted/obtained/evaluated counts. |
| Deliberately wrong answer | Modify a copied skill to give an obviously wrong answer. It must fail the relevant comparison; it must not gain a scientific grade merely because it ran. |
| Script and generated file | Use a skill with a small script and output file. The log must show container execution; inspect the saved output path and content digest in the JSON report. |
| Binary input | Use a skill with a small known binary input and its required preinstalled library. Check that exact bytes were used and the result is inspectable. |
| Boundary check | In a disposable copied skill, ask it to read an arbitrary host file or contact an unapproved host. It must not obtain that content. Use a harmless sentinel file, never a real secret. |
| Missing dependency | Use an image missing a required package. Expect a clear error/limitation, with no fabricated output or scientific pass. |
| Resource/app connection | After configuring one, verify the exact resource digest or adapter identity and its actual response. An installed but unconfigured app should remain unavailable. |
| Documentary assessment | Check a separate assessor session, exact cited quotes and disclosed AI judgment. No planner conversation or subject answers should be included in its packet. |
| Cancellation | Interrupt a CLI run with Ctrl+C and a desktop run with Stop. The attempt log and any receipts should remain. No uncertain trial should be replayed automatically. |
| Reuse | Verify the skill again and confirm lookup reuses a saved candidate where applicable; references are pinned rather than invented again. |
| Operational versus scientific | Check that every claim without a verdict names *why*: a refused test session, an incomplete one, a session that answered outside its rubric. None of those may appear as a scientific failure, and none may quietly become a grade. Counts of planned, attempted, obtained and missing trials must add up. |
| Grade negotiation | Read the plan audit in the report. Confirm the proposed grade, the runner's evidence ceiling with its limiting reasons, and the independent critique's findings are all recorded, and that the settled grade is no stronger than any of them. A skill that only ran should not carry an A. |
| Catalog contribution | If you propose a candidate, confirm the draft PR opens without any prior sign-off, that `review` returns the comments you leave on it, and that republishing a corrected bundle revises the same PR instead of opening a second one. Nothing should merge by itself. See [LOCAL-CONFIG.md](LOCAL-CONFIG.md#propose-a-candidate-for-review). |
| Catalog updates | If you maintain a shared catalog, use the release steps in [LOCAL-CONFIG.md](LOCAL-CONFIG.md#prepare-and-distribute-a-reviewed-catalog-release). Confirm a retired candidate disappears from a new run and old reports retain their pins. This does not require publishing your personal results. |

During a computational trial, Docker Desktop should show a temporary container
named `sci-verifier-…`. It should disappear when the trial ends. If you interrupt
the parent app, allow the bounded container lifetime to expire, then check again.
Report lingering containers as a cleanup defect. Do not inspect or remove
unrelated containers.

For each test, retain the attempt ID, run ID, error code if any, and report/log
paths. When reporting results, say what you expected and what actually happened.
No tokens or full private datasets are needed. Passing these tests establishes
behavior for your tested skills and environment; domain-specific scientific
acceptance still depends on the actual reviewed evidence.

## Updating or removing the connection

**You do not need a full uninstall before upgrading.** Keep Claude Desktop,
Claude Code CLI, Python and Docker if installed. Update a dependency only when
it no longer meets this guide's requirements.

1. Stop active verification sessions before updating the project's source files.
   Keep the project folder and every `.verifier` data folder, including any older
   report folder outside this checkout. They contain settings, reports and logs.
2. If you installed the old Stage 2/3 or demo verifier extension and uploaded
   verifier skill, disable those old verifier components to avoid choosing their
   obsolete workflow. Uninstalling them is optional. Keep the separate skill
   folders you want to submit for testing.
3. If `scientific-verifier-local` already exists and you are changing its program
   path or configuration path, remove that connection registration:

   ```powershell
   claude.exe mcp remove --scope user scientific-verifier-local
   ```

   This removes the user-scoped connection entry, not the project, settings or
   reports. Then repeat step 5. If the connection
   already has the correct program, configuration and environment-variable
   settings, keep it; no re-registration is needed. See
   [Claude's connection-management documentation](https://code.claude.com/docs/en/mcp#managing-your-servers).
   A connection registered before this guide added `--timeout` still runs on the
   30-minute default; remove and re-add it to pick the longer limit up. Registered
   arguments are read when the connection starts, so restart Claude Desktop after
   changing them.
4. If you created `.verifier\local-settings.json` with an earlier build, delete the
   `scientific_reviews` and `documentary_review` lines from it. Those settings were
   removed: an evidence grade is now settled by the evidence and an independent
   critique, not by a review you enter. Preflight names any leftover key. The rest of
   the file is unchanged, and you do not need to regenerate it.
5. Restart Claude Desktop and start a fresh **Code → Local** session as in step 6.

Old completed runs remain readable. Changed runtime code cannot continue an
earlier scientific execution using its old audit; start a new verification.
To stop using the tool entirely, remove its connection with the command above
and keep your saved data for as long as you need it.

## For development only

These are not installation steps. Run them from the checkout:

```powershell
Set-Location "D:\Su Lab\sci-ai-verifier"
& "C:\Python314\python.exe" -m unittest discover -s tests -q
& "C:\Python314\python.exe" scripts/run_local_fixture.py
& "C:\Python314\python.exe" scripts/build_local.py
```

The fixture uses synthetic data and needs no Claude account; it does not validate
the desktop connection. See the [development log](DEVELOPMENT-PLAN.md) for status.

The builder creates `dist/scientific-verifier-local-0.7.0.zip`, including editable
source, tests, and this guide. Credentials and saved runs are excluded. If you
move or extract the checkout elsewhere, remove the old connection as described
above, then repeat step 5 with the new paths.
