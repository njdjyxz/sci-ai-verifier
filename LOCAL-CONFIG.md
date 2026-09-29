# Local configuration and reusable evaluators

Use [LOCAL-INSTALL.md](LOCAL-INSTALL.md) for ordinary setup and manual testing.
This reference is for adding your datasets, scientific dependencies, app adapters
and independently reviewed methods. None of these require switching Claude to
API billing.

## Settings

`scripts/configure_local.py` creates `.verifier/local-settings.json`. Pass that
file with `--config` to `verify`, `serve-local` and `doctor`. It is private and
ignored by Git. Edit it between runs; a run pins its exact effective settings.
Unknown settings are rejected so spelling mistakes cannot silently change access.

| Setting | Default / purpose |
| --- | --- |
| `sandbox_image` | Exact installed `sha256:…` image ID; null means text-only sessions |
| `docker_executable` | Native Docker executable; only a local Linux engine is accepted |
| `trial_count` | 3 fresh subject sessions per case |
| `max_subject_calls` | 128 per verification |
| `subject_timeout_seconds` | 120 per subject session |
| `memory_mib`, `cpus`, `pids_limit` | 512 MiB, 1 CPU, 64 processes per container |
| `workspace_mib` | 128 MiB writable trial workspace |
| `max_file_bytes` | 4 MiB per artifact/resource |
| `max_artifact_bytes`, `max_artifacts` | 16 MiB and 200 regular files per workspace |
| `allowed_reference_hosts` | Empty means public HTTPS references may be discovered; a nonempty list restricts exact hosts |
| `allowed_subject_hosts` | Empty means no subject downloads; otherwise exact permitted public hostnames |
| `resources`, `external_tools` | Empty until you configure them |
| `documentary_assessment` | true; attempt a fresh documentary assessment when execution cannot support a grade |
| `minimum_grade` | null, or A/B/C/D; reports state whether the requested minimum was met |
| `catalogs` | Empty until you select exact shared bundles |

Scientific packages belong in a reviewed custom Linux image. Build it before a
verification, using pinned package versions and hashes, then run the configuration
helper with that installed image name and a **new** output filename. The helper
saves its immutable image ID. Include only the required scientific tools; do not
bake account credentials into an image. Trials never run host `pip` or install
dependencies. Images must provide Python 3, `/bin/sh` and `cp`.

[`images/rdkit/`](images/rdkit/Dockerfile) is one such image, for skills that use RDKit
and pandas, such as `examples/sar-analysis`. It holds the pinned `python:3.12-slim` base,
exact Debian libraries for RDKit's drawing module and hash-pinned wheels. Build it and
read its ID:

```powershell
docker build -t sci-verifier-rdkit:2026.3.6 "D:\Su Lab\sci-ai-verifier\images\rdkit"
docker image inspect --format "{{.Id}}" sci-verifier-rdkit:2026.3.6
```

Pin that ID through the helper as above, or set `sandbox_image` to it in the settings
file the verifier is registered with. A run pins the ID, never the tag.

## Datasets and binary resources

Add a named entry under `resources` with exactly these fields, using real values:

```json
{
  "path": "D:/My Research/reference.csv",
  "sha256": "the file's 64-character SHA256",
  "version": "dataset release/version",
  "license": "license and analysis permissions",
  "units": "column units, or not applicable with a reason",
  "description": "what the data measures and the input/answer mapping"
}
```

Get a file hash in PowerShell with `(Get-FileHash "D:\My Research\reference.csv" -Algorithm SHA256).Hash.ToLower()`.
The planner sees the configured name and provenance, not permission to read an
arbitrary host path. JSON, rectangular CSV/TSV and ZIP structure can be checked.
ZIP members are inspected under expansion limits and never extracted on the host.
Binary bytes remain pinned; a companion text manifest supplies auditable labels,
units and input/expected-value relationships. Format checks cannot establish that
a scientific dataset is correct or that its license permits redistribution.

Subject downloads use a separate tool and only hosts in `allowed_subject_hosts`.
They are bounded HTTPS GET requests with no redirects, private addresses or
credentials. Downloads create a new filename directly inside `/work`; existing
files are preserved. The log records the URL and actual content digest.

## External apps

The current bridge supports **read-only native app adapters** that accept one JSON
request on stdin and return one JSON response on stdout. An app does not become
connected just because it is installed or listed in Claude's other connections.
Its adapter must implement this interface and enforce the app's permitted read
operations. Apps without such an adapter need app-specific integration work.

Each `external_tools` entry has `executable` (absolute native program path),
`sha256` (of that executable), `arguments` (fixed argument list), `description`,
`credential_env` (environment variable names only), and `read_only: true`.
The model supplies JSON data, never an executable, command template or shell
arguments. Program changes fail the digest check. Shell and script launchers are
rejected. The adapter runs on the host and is explicitly trusted; its declaration
is not an OS sandbox or a proof that a third-party app is read-only.

Keep app credentials in the desktop environment editor or your process environment.
Forward the named variables in your verifier MCP configuration when needed. Do
not put their values in this settings file. The bridge passes only those named
app credentials to the adapter; Claude's token is not passed to it. App calls
are bounded and logged. Writes, sending messages and transactions are not exposed
by this bridge.

## How the evidence grade is decided

The grade says how strong the evidence is, not whether anyone endorses the skill.
You do not enter or approve grades anywhere in this configuration.

For each claim the runner computes the strongest grade its **own** recorded facts allow
for the verifier's test design. The verifier must propose exactly that ceiling: claiming
more is refused, and so is aiming lower to look cautious. "There was no good enough
source for a higher grade" is not a reason to aim low, because that is already what the
ceiling reflects.

Each grade has two requirements, and the ceiling is the weaker of the two. The
reference requirements (where the expected answers came from and how they are scored)
are in [`local-contract.md`](skills/scientific-verifier/references/local-contract.md)
under "Negotiated evidence grade". The number and kind of cases each grade needs are in
[`evidence-rubric.md`](skills/scientific-verifier/references/evidence-rubric.md) under
"Cases each grade requires". D means no execution: an independent session assessed
cited sources. U means no acceptable evidence was found at all.

A generated Python evaluator cannot reach A, because direct validation excludes AI
judgment from scoring. One trial against a model subject cannot reach A or B,
because one sample cannot separate a skill that is right from one that is sometimes
right. Set `trial_count` to at least 3 if you want those grades to be reachable.

The runner then starts a fresh Claude session that never saw the planning, gives it
only the claim, the evidence design, the source provenance and a fixed critique rubric,
and asks what grade the evidence actually supports, and whether each case counts.
That session can only lower the grade, and the runner re-derives the ceiling from the
cases it counted.

If it supports less, the verifier has two moves: improve the evidence and propose the
new ceiling, which costs a round, or accept the grade this design was critiqued at,
which settles at once and costs nothing. Proposing again **without changing the
evidence** is refused outright and costs no round, so it cannot argue in circles. The
budget is one round per rubric grade, five, and it is spent only on genuine revisions.

Each new reviewer is told what earlier reviewers objected to, so it can check whether
those concerns were fixed, but never what grade they gave — a reviewer shown "the last
one said C" would just agree. The plan audit in the report shows every round: the
proposal, the runner's ceiling with its limiting reasons, each critique's findings and
objections, and the settled grade.

The installed policy also requires complete scored trials, zero invalid observations
and unanimous scored-status agreement within each case. A failed claim can have
strong evidence: a unanimous fail is graded exactly like a unanimous pass. No
eligible grade triggers the documentary path, not an invented scientific pass.

Inspect the exact installed policy and documentary rubric with their digests:

```powershell
python scripts/local_policy.py
```

The documentary assessor always uses a new no-tool Claude session with a bounded
cited packet. A completed assessment is grade D on its own. D means documentary
consistency only; execution accuracy stays unverified and AI judgment is primary.
U/inconclusive means no acceptable evidence was found after a search the runner
observed; an unavailable tool or assessor is an operational failure instead.
List saved candidates and their fingerprints at any time:

```powershell
python scripts/local_catalog.py list --workspace "D:\Su Lab\sci-ai-verifier"
```

## Shared catalog and contributions

To reuse a bundle or reviewed catalog release, add `{ "location": "absolute file path or public HTTPS URL",
"sha256": "exact reviewed digest" }` under `catalogs`. First use verifies and
requalifies it; subsequent uses can read its cached bytes offline. Python
candidates still require their local container for controls and scoring. A grade
is never imported from someone else's asserted status; your own run settles it.
Choose an updated release deliberately by its new digest; existing runs retain
their original pins. Historical registry releases remain supported by
`scripts/catalog_release.py` for the historical profiles.

### Propose a candidate for review

The order is: prepare and check locally, open a draft pull request, let a person
review it there, address the comments, and let that person merge. Review happens on
the pull request, not before it.

Export the selected candidate IDs, recording the licence and source of every
included reference so a reviewer can judge redistribution:

```powershell
python scripts/local_catalog.py export --workspace "D:\Su Lab\sci-ai-verifier" --candidate CANDIDATE_ID --file ".verifier\candidate-proposal.json" --redistribution "Reference sources and licences as recorded in the bundle; assessed as redistributable under those terms."
```

That statement is the preparer's assessment for a reviewer to check, not a legal
authorization. The command creates a local file and prints its SHA256; it uploads
nothing. The bundle excludes subject observations, logs and settings; reference
content and case inputs are included, so inspect them before sharing.

Open the draft PR with your own signed-in [GitHub CLI](https://cli.github.com/):

```powershell
python scripts/local_catalog.py publish --workspace "D:\Su Lab\sci-ai-verifier" --config ".verifier\local-settings.json" --file ".verifier\candidate-proposal.json" --sha256 EXACT_PRINTED_HASH --repository njdjyxz/sci-ai-verifier
```

This requalifies the bundle in disposable storage, uploads it and opens one draft
PR. It never merges. If it fails, retry the same file and command; completed stages
and the PR identity are reconciled without executing the submitted skill again.

Read the review that comes back:

```powershell
python scripts/local_catalog.py review --file ".verifier\candidate-proposal.json" --sha256 EXACT_PRINTED_HASH --repository njdjyxz/sci-ai-verifier
```

To address comments, re-export a corrected bundle **to a new file**, then publish
that file with its own hash and the same repository. A changed bundle for the same
candidate set commits a revision onto the same branch and pull request instead of
opening a second one. Republishing an unchanged file pushes nothing. Accepting the
candidate is the reviewer's merge, and merging confers no scientific grade.

### Prepare and distribute a reviewed catalog release

This is maintainer work; ordinary personal verification does not require it.
Save one prepared assessment per candidate as a JSON list. Each record must have
exactly `candidate_ref`, `proposal` (`propose_for_catalog` or `propose_retirement`),
`prepared_by`, `prepared_at`, `provenance`, `scope`, `coverage`, `uncertainty`,
`redistribution` and `scientific_approval: "not_conferred"`. All are nonempty
strings, and there must be exactly one for every candidate in the bundle. These
records exist so a reviewer has something specific to review on the pull request;
the program checks their completeness and reruns mechanical qualification, and
neither step approves anything.

Prepare the release:

```powershell
python scripts/local_catalog.py release --file ".verifier\candidate-proposal.json" --sha256 EXACT_BUNDLE_HASH --assessments ".verifier\catalog-assessments.json" --catalog-id personal-methods --version 1.0.0 --config ".verifier\local-settings.json" --output ".verifier\catalog-1.0.0.json"
```

This writes a new local file and prints its exact hash. It uploads nothing and
does not overwrite an existing release. The default supported runtime range is
0.7.0 inclusive to 0.8.0 exclusive; maintainers may supply a tested range using
`--minimum-runtime` and `--maximum-runtime-exclusive`.

For an update, add `--previous` and `--previous-sha256` for the exact preceding
release and increase `--version`. The bundle must retain every previous candidate
ID, with an explicit `propose_retirement` record for each withdrawn method. New runs
exclude retired IDs even when their candidate bytes are cached. An active run
keeps its original release and retirement set. Select only one version of each
catalog in a configuration; conflicts and incompatible runtimes stop preflight.

To distribute the prepared release, use the same `publish` command above with
the **release** file and its hash. This prepares a draft PR containing
`catalog/releases/CATALOG_ID/VERSION.json`, and `review` reads its comments the same
way. After actual maintainer review and merge, consumers use that file's public raw
URL, preferably with the exact GitHub commit, and its SHA256 in `catalogs`. Releases are independent data files; compatible
updates do not require reinstalling the verifier. Cached exact bytes work offline.
Importing a release with the maintenance `import` command installs its candidate
bytes; configuring that release under `catalogs` applies its inventory to new
runs. No command merges a PR, silently upgrades a run or grants a scientific grade.
