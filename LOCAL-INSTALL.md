# Personal/local version 1

The main branch contains version 0.6.0. Run the verifier from this checkout with
Python 3.11 or newer; Python runtime dependencies are standard-library only.

## Set up Claude Code

Install the native [Claude Code CLI](https://code.claude.com/docs/en/setup), version
2.1.248 or newer. Use the native executable rather than a `.cmd` wrapper.

For subscription use, sign in with Claude Code and run `claude setup-token` yourself.
Supply the resulting token as `CLAUDE_CODE_OAUTH_TOKEN` in the environment of the
verifier process. Do not put it in this repository, a run folder, or an MCP JSON
file. A subscription needs available eligible usage. This mode uses isolated
configuration with the supplied token; it does not copy your existing login files.

Alternatively supply `ANTHROPIC_API_KEY` and add `--auth api`. API mode uses bare
execution and separate API billing. The verifier never switches billing modes
automatically. Both modes send submitted skill text and test inputs to Claude;
this is local orchestration and storage, not an offline language model.

Check setup without consuming model usage:

```powershell
python scripts/verify.py doctor
```

## Verify a skill

```powershell
python scripts/verify.py verify "D:\path\to\my-skill"
```

Optional settings: `--workspace "D:\path\to\results"`, `--model opus`,
`--auth api`, `--claude-executable "C:\path\to\claude.exe"`, and
`--timeout 1800`. Model defaults to the configurable `opus` alias; the receipt
records actual model IDs observed in responses separately from the requested alias.

The command prints the outcome and report paths. JSON and Markdown reports live
under `.verifier/runs/<run-id>/report-card.*` in the selected workspace.
The outer Claude Code session chooses the workflow using its own native tool loop.
Every subject case runs in a fresh restricted session with explicit skill invocation.

Press Ctrl+C to stop. Requests already attempted remain recorded; an uncertain
sample is never replayed. Running `verify` again creates a new run. Internal
recovery remains available for diagnostics, while the public flow is restart-first.

## Use one tool from Claude Code

Configure a local stdio MCP server using the following command and arguments,
substituting the absolute Python and checkout paths on your machine:

```json
{
  "mcpServers": {
    "scientific-verifier": {
      "command": "C:/Python314/python.exe",
      "args": ["D:/Su Lab/sci-ai-verifier/scripts/verify.py", "serve-local",
               "--workspace", "D:/Su Lab/sci-ai-verifier"]
    }
  }
}
```

The process must inherit the selected authentication environment. It exposes only
`verify_skill`; say **Verify this skill: <full path>**. Existing Desktop MCPB files
and the historical `serve --profile ...` commands are compatibility interfaces.
They are not the recommended local installation.

## What the first local version can establish

The planner can discover public primary reference pages, build source-backed
numeric or exact cases, qualify their mechanics, reuse them offline, and report
the subject's actual comparisons. Newly discovered candidates remain provisional
scientifically: a comparison pass is not a scientific grade. References, versions,
license notes, applicability assertions, fixed cases and limitations are saved.

Only plain text skills and supporting text resources are supported. Skills needing
scripts, shell commands, external apps, networking or binary assets receive an
explicit limitation. Wider executable evaluators, independently approved grading,
automatic GitHub contributions and releases remain subsequent development.

## Validate the checkout

```powershell
python -m unittest discover -s tests -q
python scripts/run_local_fixture.py
python scripts/build_local.py
```

The fixture is visibly synthetic and needs no Claude credentials. It demonstrates
the saved local workflow and is not a live acceptance test. As of this delivery,
live model execution has not been performed; see the current development log.

The builder writes `dist/scientific-verifier-local-0.6.0.zip` with the editable
source, contracts, tests and examples. Extract it and use the same commands there.
It excludes credentials, `.git`, saved verification runs and legacy source.
