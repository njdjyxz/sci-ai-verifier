# Install the verifier on Windows or macOS

This guide sets up **sci-ai-verifier 0.8.0** on a computer of your own, with **your own
Claude subscription**. Every path below is a placeholder: `<project folder>` is wherever you
clone this repository, for example `C:\Users\<you>\sci-ai-verifier` on Windows or
`~/sci-ai-verifier` on macOS. Nothing in the repository carries a credential, a machine
name or a personal path; you supply all three during setup.

**What you get.** From the Claude desktop app's **Code** tab you can say "verify this skill"
with a folder path, and the verifier runs the skill in a disposable container, checks its
outputs in Python, has an independent Claude session critique the evidence, and writes a
report with an evidence grade and a pass/fail status. The report is a file on your disk.

**What it needs.** The Claude desktop app, the Claude Code command-line program, Python 3.11
or newer, Git, Docker Desktop, and a Claude subscription that includes Claude Code. "Local"
means the program, settings and reports live on your computer; skill text and test inputs
still go to Claude's hosted models and use your Claude usage allowance.

**Platform status.** The verifier has been developed and run on Windows 11. Its code has the
POSIX branches macOS needs (process groups instead of Windows job objects, the same `docker`
command line) and the automated tests are platform-neutral, but **no macOS verification run
has been recorded yet**. Treat the macOS steps as the same procedure, untested; if you are the
first to run one, record what you find in [DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md).

## Before you start: your credential, not the author's

The verifier starts separate Claude Code sessions for its tests. Those sessions sign in with
a **token you generate** from your own subscription (step 3). The repository, the saved
settings file and the tool registration never contain the token itself: the registration
stores the placeholder `${SCI_VERIFIER_OAUTH_TOKEN:-}`, which Claude Code fills from an
environment variable at start-up. If you clone this repository from GitHub, there is no
credential in it and nothing runs on anyone else's account until you complete step 3 with
your own token.

Keep the token out of chat messages, repository files, screenshots and support requests.
To stop using it, generate a new one (which replaces it) or remove the variable from the
desktop app and your shell.

## 1. Install the prerequisites

### Windows

1. **Python 3.11 or newer.** Install from [python.org](https://www.python.org/downloads/windows/)
   and tick "Add python.exe to PATH". Then in **PowerShell**:

   ```powershell
   python --version
   ```

   Expect `Python 3.11` or later. No extra Python packages are needed.
2. **Git.** Install [Git for Windows](https://git-scm.com/downloads/win) with its defaults.
   The desktop app's Code tab needs it.
3. **Docker Desktop.** Install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/),
   follow its WSL 2 instructions, restart, open Docker Desktop and wait until the engine shows
   as running. Use **Linux containers** (the default).
4. **Claude desktop app.** Install from [claude.ai/download](https://claude.ai/download) and
   sign in with your subscription. Open the **Code** tab once so it finishes its own setup.
5. **Claude Code command-line program.** In PowerShell:

   ```powershell
   winget install Anthropic.ClaudeCode
   ```

   Close and reopen PowerShell, then:

   ```powershell
   claude --version
   ```

   The verifier needs **2.1.268 or newer** for its restricted execution mode, and **2.1.302 or
   newer** to run its pinned model (step 5). Update an older WinGet install with
   `winget upgrade Anthropic.ClaudeCode`. If WinGet is unavailable, follow Anthropic's
   [Windows instructions](https://code.claude.com/docs/en/setup#install-claude-code) and use a
   native (not WSL) installation.

### macOS

1. **Python 3.11 or newer.** The `python3` that ships with Xcode's tools may be older. Install
   from [python.org](https://www.python.org/downloads/macos/) or with Homebrew
   (`brew install python@3.12`). Then in **Terminal**:

   ```bash
   python3 --version
   ```

   Expect `Python 3.11` or later. No extra Python packages are needed.
2. **Git.** Run `git --version`; if macOS offers to install the command-line developer tools,
   accept.
3. **Docker Desktop.** Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
   (choose the Apple silicon or Intel build), open it and wait until the engine shows as
   running. It provides the `docker` command used below.
4. **Claude desktop app.** Install from [claude.ai/download](https://claude.ai/download) and
   sign in with your subscription. Open the **Code** tab once.
5. **Claude Code command-line program.** In Terminal:

   ```bash
   curl -fsSL https://claude.ai/install.sh | bash
   ```

   (Homebrew users can run `brew install --cask claude-code` instead.) Open a new Terminal
   window, then:

   ```bash
   claude --version
   ```

   The same minimum versions apply as on Windows: **2.1.268**, and **2.1.302** for the pinned
   model. Update with `claude update`.

## 2. Get the project

### Windows

```powershell
git clone https://github.com/njdjyxz/sci-ai-verifier.git "$HOME\sci-ai-verifier"
```

### macOS

```bash
git clone https://github.com/njdjyxz/sci-ai-verifier.git ~/sci-ai-verifier
```

Any folder works; the rest of this guide calls it `<project folder>`. Do not put it inside a
cloud-synced folder (OneDrive, iCloud Drive): runs write many files under
`<project folder>/.verifier/`, which Git ignores and which must stay private.

## 3. Generate your own sign-in token

Signing in to the desktop app is not enough for the verifier's separate test sessions. Create
a token, a private credential for those sessions, from your subscription:

```bash
claude setup-token
```

(The same command on both systems.) Follow the sign-in instructions in the browser and copy
the token it prints. This needs a Claude subscription that includes Claude Code; see the
[CLI reference](https://code.claude.com/docs/en/cli-reference).

Now give it to the desktop app. In the **Code** tab, open the environment selector at the top,
hover over **Local**, click its **gear**, and add a variable:

| Name | Value |
| --- | --- |
| `SCI_VERIFIER_OAUTH_TOKEN` | the token you copied |

Save. Anthropic documents encrypted storage for these values, supplied to local sessions
([desktop environment setup](https://code.claude.com/docs/en/desktop#local-sessions)).
Step 5 registers the verifier so that this variable reaches it; keep step 5's placeholder
exactly as written and never type the token into that command.

## 4. Prepare the container image and the settings file

The verifier runs every test inside a disposable Docker container built from an image you
pin once. Start with the official plain Python image.

### Windows

```powershell
docker version
docker pull python:3.12-slim
Set-Location "$HOME\sci-ai-verifier"
python scripts\configure_local.py --image python:3.12-slim
```

### macOS

```bash
docker version
docker pull python:3.12-slim
cd ~/sci-ai-verifier
python3 scripts/configure_local.py --image python:3.12-slim
```

`docker version` must show both a client and a server; if the server part is missing, Docker
Desktop is not running. The helper writes `<project folder>/.verifier/local-settings.json`,
prints the image's exact ID, and pins it. It deliberately does not overwrite an existing
settings file; delete the old one first if you want it regenerated.

The plain image holds Python's standard library only. For skills that need scientific
packages you have two options, both described in [LOCAL-CONFIG.md](LOCAL-CONFIG.md):

- let the verifier install the packages a skill itself declares, for that skill's trials
  only, by setting `package_index` and `environment_base_image` in the settings file;
- build a reviewed image with pinned packages, such as the RDKit image under `images/rdkit/`,
  and pin its ID instead.

Missing packages produce a reported limitation, never an invented result.

## 5. Register the verifier with Claude Code

This tells Claude Code how to start the verifier and which variable carries your token. Paste
the whole box; it registers a tool connection named `scientific-verifier-local` in your
personal Claude Code configuration, available in every project.

### Windows (PowerShell)

```powershell
$project = "$HOME\sci-ai-verifier"
$python = (Get-Command python -ErrorAction Stop).Source
$claudeExe = (Get-Command claude -ErrorAction Stop).Source
claude mcp add --env 'CLAUDE_CODE_OAUTH_TOKEN=${SCI_VERIFIER_OAUTH_TOKEN:-}' --transport stdio --scope user scientific-verifier-local -- "$python" "$project\scripts\verify.py" serve-local --workspace "$project" --config "$project\.verifier\local-settings.json" --claude-executable "$claudeExe" --model claude-opus-5-5 --timeout 10800
```

### macOS (Terminal)

```bash
project="$HOME/sci-ai-verifier"
claude mcp add --env 'CLAUDE_CODE_OAUTH_TOKEN=${SCI_VERIFIER_OAUTH_TOKEN:-}' --transport stdio --scope user scientific-verifier-local -- "$(command -v python3)" "$project/scripts/verify.py" serve-local --workspace "$project" --config "$project/.verifier/local-settings.json" --claude-executable "$(command -v claude)" --model claude-opus-5-5 --timeout 10800
```

Expect an **Added** message. If you cloned to another folder, change `project` first. Keep the
single quotes around the `--env` value: `${SCI_VERIFIER_OAUTH_TOKEN:-}` must be stored
literally, so that Claude Code expands it from the variable you saved in step 3 each time the
verifier starts. The saved registration (in `~/.claude.json`) therefore holds a placeholder,
not a token.

Three arguments matter:

- `--model claude-opus-5-5` pins the exact model that runs the tests. A verdict is evidence
  about one model, so the verifier refuses a trial set that mixes two, and an alias such as
  `opus` can change underneath a run. Before changing the pin, check that your Claude Code
  can serve the new model (`claude -p "Reply OK" --model <id>`; `unrecognized_model` means
  it cannot). Runs on different pins are different series and should not be compared blindly.
- `--timeout 10800` gives each verification three hours, the maximum; a skill with several
  claims takes 20 to 100 minutes, and the 30-minute default cuts runs off mid-claim.
- `--scope user` makes the connection personal to you and independent of the project folder.

This follows Anthropic's [local MCP server setup](https://code.claude.com/docs/en/mcp#option-3-add-a-local-stdio-server)
and [environment-variable expansion](https://code.claude.com/docs/en/mcp#environment-variable-expansion-in-mcpjson).

## 6. Start a fresh desktop session and check the connection

Quit and reopen the Claude desktop app. In **Code**, choose **Local**, select `<project folder>`
as the project, and start a new session. Send:

> Check whether scientific-verifier-local provides the verify_skill tool. Do not start a verification yet.

Expect **`verify_skill`**. If it is missing, see Troubleshooting. A connected tool still needs
a real run to confirm the token, model access and container execution.

## 7. Verify your first skill

Pick a small skill folder that contains a `SKILL.md` whose expected behaviour you understand.
Copy its full path and send, in a **new** session:

> Use scientific-verifier-local to verify this skill: <full path to the skill folder>. Show me the saved report and its limitations.

Approve the tool when asked and leave the session running. A run takes tens of minutes for a
handful of claims and uses a noticeable share of your subscription's 5-hour usage window
(a four-claim run has used about half of it). Start one run at a time, and check your usage
before starting another.

When it finishes, the reply names the saved files:

| File | What it is |
| --- | --- |
| `<project folder>/.verifier/runs/<run-id>/report-card.md` | The verifier's report: each claim, its tests, expected and found outputs, references, grade, status and limitations |
| `<project folder>/.verifier/runs/<run-id>/report-card.json` | The same, structured |
| `<project folder>/.verifier/reports/<run-id>.html` | The run as one web page; the agent that asked for the run fills in its plain-language summaries |
| `<project folder>/.verifier/attempts/<attempt-id>/workflow.md` | The attempt's timeline, written even when setup fails before a run exists |

Completion is not a scientific pass. The **evidence grade** says how strong the evidence is:
**A** means Python checked the skill's outputs against values it planted from, or quoted out
of, a source it retrieved itself; **B** a weaker design (judged written answers, a dataset you
pinned, or fewer independent tasks); **C** a reproducible comparison with weaker traceability;
**D** a fresh session judged cited sources with no execution; **U** no acceptable source was
found. The **status** (pass, fail, inconclusive) is a separate axis. No grade is ever
entered by hand, and a skill that merely ran does not get an A. Read
[LOCAL-CONFIG.md](LOCAL-CONFIG.md#how-the-evidence-grade-is-decided) for how the grade is
negotiated and critiqued.

Keep logs private: they can include your skill's text, inputs, outputs and local paths.
Credentials are redacted from them.

## Optional: run from the command line

The variable you saved in the desktop app is not visible to a separate terminal. Provide the
token to that terminal only, then run the same program directly. Replace the placeholders.

### Windows (PowerShell)

```powershell
$secret = Read-Host "Paste your Claude token (hidden)" -AsSecureString
$env:CLAUDE_CODE_OAUTH_TOKEN = [System.Net.NetworkCredential]::new("", $secret).Password
Remove-Variable secret
Set-Location "$HOME\sci-ai-verifier"
python scripts\verify.py doctor --config ".verifier\local-settings.json"
python scripts\verify.py verify "<full path to the skill folder>" --workspace "$HOME\sci-ai-verifier" --config ".verifier\local-settings.json" --timeout 10800
```

### macOS (Terminal)

```bash
read -r -s -p "Paste your Claude token (hidden): " CLAUDE_CODE_OAUTH_TOKEN; echo
export CLAUDE_CODE_OAUTH_TOKEN
cd ~/sci-ai-verifier
python3 scripts/verify.py doctor --config .verifier/local-settings.json
python3 scripts/verify.py verify "<full path to the skill folder>" --workspace ~/sci-ai-verifier --config .verifier/local-settings.json --timeout 10800
```

`doctor` reports `"status":"ok"` when it finds the Claude program, an acceptable version, a
credential and the pinned image; it uses no model allowance and does not validate the token
with Claude. Press Ctrl+C to stop a run; the attempt log and any evidence saved so far are
kept. Close the terminal when done; the token lives only in that process.

Other options: `--model <id>`, `--no-html` to skip the web page, and
`--claude-executable <path>`. The CLI's default timeout is 1800 seconds, which is usually
too short; pass `--timeout 10800`. **API billing instead of a subscription:** set
`ANTHROPIC_API_KEY` and add `--auth api` to `verify` or `serve-local`. API mode is billed
separately; the verifier never switches to it on its own.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| `claude` is not recognized / command not found | Finish step 1.5 and open a new terminal. The desktop app alone does not provide the command-line program. |
| `claude_version_unsupported` | Update Claude Code to at least 2.1.268. |
| `model_unavailable` before the planner starts | Your Claude Code cannot serve the pinned model. Update it, or re-register (step 5) with a model it can serve. |
| "Git is required" in the Code tab | Install Git and restart the app. |
| The verifier tool is missing in a session | Confirm step 5 printed **Added**, fully restart the app, start a new Local session in the project folder, and check that `scientific-verifier-local` is not disabled in the session's tool list. |
| The connection name already exists | `claude mcp remove --scope user scientific-verifier-local`, then repeat step 5. This removes the registration, not your reports. |
| `authentication_required` before the planner starts | Check the variable name and token from step 3, save, and start a new session. |
| Planner runs, but a test or review session returns `authentication_required` | Confirm the registration carries the `CLAUDE_CODE_OAUTH_TOKEN=${SCI_VERIFIER_OAUTH_TOKEN:-}` placeholder, then fully restart the app. |
| Expired-token, sign-in or usage-limit error | Run `claude setup-token` again and update the variable, or wait for your usage window to reset. |
| `source_missing` or `source_not_authorized` | Give the full path of an existing skill folder, the same one you named when starting the run. |
| `sandbox_unavailable`, `sandbox_configuration_required` | Start Docker Desktop and wait for its engine; complete step 4 and make sure the registration points at the settings file. |
| `sandbox_image_unavailable` or `sandbox_start_failed` | The pinned image no longer exists, or Docker stopped. Pull or build it again; do not edit an active run's settings. |
| `skill_environment_unavailable` | The packages the skill declares could not be installed for the sandbox's Python (no wheel, a renamed or missing package). The report names the error. Prepare an image with those packages, or accept that the skill cannot run as declared. |
| A Python import error in a trial | The skill needs a package the image lacks. Set `package_index` or build an image with it (LOCAL-CONFIG.md), then start a new run. |
| `subject_refused` | Anthropic's safety classifiers declined the test task. Nothing was observed; the claim is retried once at the end of the run and otherwise reported as refused, never as a failure of the skill. |
| `claude_timeout` on a trial | A test session hit the per-trial limit (`subject_timeout_seconds`, 600 s by default). Raise it in the settings file for long-running skills and start a new run. |
| `planner_incomplete` | The run did not finish. Keep the run id and the attempt log; see "Legal operations" in the local contract for the illegal-transition budget. |
| `critic_unavailable`, `assessor_unavailable`, `*_response_invalid` | An independent review session did not complete or answered outside its rubric. Operational, never a grade; keep the attempt log. |
| `verification_timeout` | The attempt hit the registered timeout. Re-register with `--timeout 10800` if yours is smaller. |
| `subject_model_changed` | The model identity changed partway through a claim's trials; the claim stops rather than mixing models. Expect this occasionally even with a correct pin. |

When asking for help, share the error code, the run id and the attempt log, never the token.

## Updating or removing

- **Updating the source.** Stop running verifications, `git pull` in `<project folder>`, and
  restart the desktop app: a running `serve-local` keeps the old code until the session that
  started it ends. Keep `.verifier/` (settings, reports, logs); it is never overwritten by Git.
- **Moving the project folder.** Remove the registration and repeat step 5 with the new path:

  ```bash
  claude mcp remove --scope user scientific-verifier-local
  ```

- **Changing the model or timeout.** Same: remove and re-add. Registered arguments are read
  when the connection starts, so restart the app afterwards.
- **Removing the verifier.** Remove the registration as above, delete the variable from the
  desktop app, and keep or delete `<project folder>` as you wish.

## Your manual acceptance tests

Automated fixtures establish implementation behaviour only. Run these yourself, with skills
whose expected behaviour you know, before trusting the verifier on your own work. Use copies
when deliberately introducing errors.

| Test | What to check in the report and workflow log |
| --- | --- |
| First small skill | The planner calls internal verifier tools; each test session explicitly invokes the pinned skill; real model and session ids are recorded. |
| Repeated trials | Three observations per task by default, with distinct sessions and planned/attempted/obtained/evaluated counts that add up. |
| Deliberately wrong result | A copied skill changed to give a wrong answer must fail the relevant task and must not gain a grade merely because it ran. |
| Script and generated file | The log shows container execution; the saved output path and digest are in the JSON report. |
| Boundary check | In a disposable copied skill, ask it to read an arbitrary host file or contact an unapproved host. It must not obtain that content. Use a harmless sentinel file, never a real secret. |
| Missing dependency | With an image lacking a required package, expect a clear limitation and no fabricated output. |
| Documentary assessment | A separate assessor session, exact cited quotes and disclosed AI judgment; no planner conversation or test answers in its packet. |
| Cancellation | Ctrl+C on the CLI and Stop in the desktop app both leave the attempt log and saved evidence in place. |
| Operational versus scientific | Every claim without a verdict names why (a refused, incomplete or off-rubric session), and none of those appears as a scientific failure or quietly becomes a grade. |
| Grade negotiation | The report's plan audit shows the proposed grade, the runner's ceiling with its reasons and the independent critique; the settled grade is no stronger than any of them. |

During a computational trial Docker Desktop shows a temporary container named
`sci-verifier-...`, which disappears when the trial ends. Report a lingering one as a cleanup
defect; do not touch unrelated containers.

## For development only

```bash
cd <project folder>
python -m unittest discover -s tests -q      # python3 on macOS
python scripts/run_local_fixture.py          # synthetic end-to-end run, no Claude account needed
python scripts/build_local.py                # source-complete zip in dist/, credentials excluded
```

The fixture uses synthetic data and does not validate the desktop connection.
[DEVELOPMENT-PLAN.md](DEVELOPMENT-PLAN.md) introduces the project, records what has been
verified live, and lists the roadmap.
