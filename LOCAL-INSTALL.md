# Set up the verifier on your Windows PC

**Yes, you can keep using Claude Code in the desktop app.** Install its
command-line program once as well: this verifier uses it to start separate test
sessions. You can then request verification in the app, without typing commands
for everyday use.

This guide is for **version 0.6.0**, your Claude subscription, and the **Code** tab.
The older verifier desktop extensions are compatibility packages; installing one
does not set up this version's `verify_skill` action.

Version 0.6.0 is an **incomplete implementation**. This guide explains how to run
what exists today. The [development plan](DEVELOPMENT-PLAN.md#codex-2026-09-11-1932-pdt)
lists the full local completion work; the limitations below are not the product goal.

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

### 4. Connect the verifier to Claude Code

Back in **PowerShell**, paste the entire box:

```powershell
$verifierClaude = (Get-Command claude.exe -ErrorAction Stop).Source
claude.exe mcp add --env 'CLAUDE_CODE_OAUTH_TOKEN=${SCI_VERIFIER_OAUTH_TOKEN:-}' --transport stdio --scope user scientific-verifier-local -- "C:/Python314/python.exe" "D:/Su Lab/sci-ai-verifier/scripts/verify.py" serve-local --workspace "D:/Su Lab/sci-ai-verifier" --claude-executable "$verifierClaude"
```

Expect an **Added** message. The first line finds the installed Claude program;
the second registers a tool connection named `scientific-verifier-local` in your
personal Claude Code configuration. It is available across projects. The saved
configuration contains a credential placeholder, not the token itself.

“MCP” is the connection that lets Claude call the verifier. This command follows
Anthropic's [local tool setup](https://code.claude.com/docs/en/mcp#option-3-add-a-local-stdio-server)
and [environment-variable configuration](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson).
No manual JSON editing is needed. **Added** confirms registration, not live execution.

### 5. Start a fresh desktop session

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

Completion is not automatically a scientific pass. The current build supports
text-only skills and exact or numeric reference comparisons. Newly generated
methods have **no scientific grade**. Skills needing scripts, external apps,
network tools, or binary assets are not implemented in this execution path yet
and should receive an explicit limitation. Implementing them and qualified
scientific grading is part of the remaining local project.

If a run stops or fails, retain its run ID for diagnosis. Asking to verify again
starts a new run; prior evidence is retained and uncertain tests are not replayed
automatically.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| `claude.exe` is not recognized | Complete step 2 and reopen PowerShell. Having the desktop app alone does not guarantee a standalone executable is available. |
| `claude_version_unsupported` | Update the standalone installation to at least 2.1.248. |
| “Git is required” in Code | Install [Git for Windows](https://git-scm.com/downloads/win) and restart the app. |
| The verifier tool is missing | Confirm step 4 printed **Added**, start a fresh local Code session, and check whether `scientific-verifier-local` is disabled. |
| The connection name already exists | Try step 5. To replace an old configuration, run `claude.exe mcp remove --scope user scientific-verifier-local`, then repeat step 4. |
| `authentication_required` | Check the exact variable name and token in step 3. Save and start a new session. |
| Expired-token, sign-in, or usage-limit error | Renew the token through step 3 or wait for eligible usage. The verifier never switches to API billing automatically. |
| `source_missing` | Supply the full path to an existing skill folder or its `SKILL.md`. |
| `planner_incomplete` or another incomplete result | Save the run ID and error. The run did not finish; setup checks cannot diagnose every live-model failure. |

Share the error code and run ID when asking for help, without credentials.

## Optional: use PowerShell directly

The desktop editor's saved variable is not automatically available in a separate
PowerShell window. Paste the token into this hidden prompt; it will not appear
in the command text:

```powershell
$verifierSecret = Read-Host "Paste your Claude token (hidden)" -AsSecureString
$env:CLAUDE_CODE_OAUTH_TOKEN = [System.Net.NetworkCredential]::new("", $verifierSecret).Password
Remove-Variable verifierSecret
& "C:\Python314\python.exe" "D:\Su Lab\sci-ai-verifier\scripts\verify.py" doctor
```

Look for **`"status":"ok"`**. `doctor` checks the executable, version, and presence
of a credential. It uses no model allowance and does **not** validate the token
with Claude or run a model.

Then, in the same window, replace the example skill path and run:

```powershell
& "C:\Python314\python.exe" "D:\Su Lab\sci-ai-verifier\scripts\verify.py" verify "D:\My Skills\my-skill" --workspace "D:\Su Lab\sci-ai-verifier"
```

Press **Ctrl+C** to stop. Close PowerShell when finished; the token set above
lasts only for that process and its children.

Advanced options: `--model opus`, `--timeout 1800`, and
`--claude-executable "C:\path\to\claude.exe"`. The default requested model is
`opus`; receipts also record actual returned model IDs.

API users must supply `ANTHROPIC_API_KEY` instead and add `--auth api` to
`verify` or `serve-local`. API mode has separate billing. Never place the actual
token or key in command arguments or repository configuration files.

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

The builder creates `dist/scientific-verifier-local-0.6.0.zip`, including editable
source, tests, and this guide. Credentials and saved runs are excluded. If you
move or extract the checkout elsewhere, remove the old connection as described
above, then repeat step 4 with the new paths.
