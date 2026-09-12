# Set up the verifier on your Windows PC

**Yes, you can keep using Claude Code in the desktop app.** Install its
command-line program once as well: this verifier uses it to start separate test
sessions. You can then request verification in the app, without typing commands
for everyday use.

This guide is for **version 0.7.0**, your Claude subscription, and the **Code** tab.
The older verifier desktop extensions are compatibility packages; installing one
does not set up this version's `verify_skill` action.

This build adds computational execution, resources, generated evaluators, repeated
trials, scientific review gates, independent documentary assessment and workflow
logs. **Live acceptance is pending your manual tests below.** The
[development plan](DEVELOPMENT-PLAN.md#codex-2026-09-11-1932-pdt) remains the complete
project checklist; automated fixtures do not establish scientific acceptance.

The examples use your current folder, `D:\Su Lab\sci-ai-verifier`, and Python at
`C:\Python314\python.exe`. On another PC, replace those paths with its actual
locations. Python must be 3.11 or newer; no extra Python packages are needed.

“Local” means the program and reports live on your PC. Skill text and test inputs
still go to Claude's hosted models and use your available Claude usage.

**What is verified so far:** automated local checks passed. The desktop connection
below follows Anthropic's documentation, but a real desktop-to-verifier run on
this PC is still untested. Setup checks alone do not establish live acceptance.

## One-time setup

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
Missing packages produce a limitation, not an invented result. Text-only use
can skip this step, but then omit `--config` and its path from the next command.

### 5. Connect the verifier to Claude Code

Back in **PowerShell**, paste the entire box:

```powershell
$verifierClaude = (Get-Command claude.exe -ErrorAction Stop).Source
claude.exe mcp add --env 'CLAUDE_CODE_OAUTH_TOKEN=${SCI_VERIFIER_OAUTH_TOKEN:-}' --transport stdio --scope user scientific-verifier-local -- "C:/Python314/python.exe" "D:/Su Lab/sci-ai-verifier/scripts/verify.py" serve-local --workspace "D:/Su Lab/sci-ai-verifier" --config "D:/Su Lab/sci-ai-verifier/.verifier/local-settings.json" --claude-executable "$verifierClaude"
```

Expect an **Added** message. The first line finds the installed Claude program;
the second registers a tool connection named `scientific-verifier-local` in your
personal Claude Code configuration. It is available across projects. The saved
configuration contains a credential placeholder, not the token itself.

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
allows up to 30 minutes by default. You do not need to run extraction, discovery,
or evaluation separately.

The result includes report paths. With the setup above, reports live here:

```text
D:\Su Lab\sci-ai-verifier\.verifier\runs\<run-id>\
```

Each run gets its own ID. Open **`report-card.md`** for the readable report;
`report-card.json` is the structured version. The report shows inputs, expected
and actual answers, references, outcomes, and limitations.

Completion is not automatically a scientific pass. Scripts, binary inputs and
generated files use the configured container; exact/numeric and generated Python
evaluators compare the observations. The default is three trials per case.
Generated files have saved paths in the JSON report. Scientific A/B/C grades need
an independent review of the exact method and scope. D uses a fresh documentary
assessor and separately reviewed rubric; it does not prove execution accuracy.
Without those reviews, comparison/assessment evidence remains ungraded. No review
or scientific grade is fabricated during setup.

Network downloads and external apps need explicit settings. Installed apps are
not automatically connected. See [app adapters and scientific reviews](LOCAL-CONFIG.md)
when you are ready to configure them.

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
| `authentication_required` | Check the exact variable name and token in step 3. Save and start a new session. |
| Expired-token, sign-in, or usage-limit error | Renew the token through step 3 or wait for eligible usage. The verifier never switches to API billing automatically. |
| `source_missing` | Supply the full path to an existing skill folder or its `SKILL.md`. |
| `planner_incomplete` or another incomplete result | Save the run ID and error. The run did not finish; setup checks cannot diagnose every live-model failure. |
| `sandbox_unavailable` or no Docker server information | Open Docker Desktop, wait for its engine, and use Linux containers. |
| `sandbox_configuration_required` | Complete step 4 and ensure the connection includes the settings path. |
| `sandbox_image_unavailable` or `sandbox_start_failed` | Check Docker is running and the pinned image still exists. Retain the log; do not change an active run's settings. |
| A Python import/package error | Prepare a new image with that dependency, pin it to a new settings file, then start a new verification. |
| `resource_not_authorized` or `app_not_authorized` | Configure the exact resource host or a reviewed read-only app adapter in LOCAL-CONFIG.md. |
| `assessor_unavailable` | The independent documentary session did not complete. This is an operational problem, not grade U. |
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
& "C:\Python314\python.exe" "D:\Su Lab\sci-ai-verifier\scripts\verify.py" verify "D:\My Skills\my-skill" --workspace "D:\Su Lab\sci-ai-verifier" --config "D:\Su Lab\sci-ai-verifier\.verifier\local-settings.json"
```

Press **Ctrl+C** to stop. Close PowerShell when finished; the token set above
lasts only for that process and its children.

Advanced options: `--model opus`, `--timeout 1800`, and
`--claude-executable "C:\path\to\claude.exe"`. The default requested model is
`opus`; receipts also record actual returned model IDs.

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
| Scientific review | Only after a real independent review, configure its exact fingerprint/scope. Check that grades follow that review and the fixed trial policy. Leave this pending if no review exists. |
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

Stop active verification sessions before replacing this checkout. Preserve
`.verifier` to retain reports. Old completed runs remain readable; changed runtime
code cannot resume an earlier scientific execution with its old audit.
Re-register the connection if the code or settings paths move. To stop using the
tool, remove `scientific-verifier-local` using the troubleshooting command; your
saved data remains until you deliberately delete it yourself.

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
