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
| `scientific_reviews`, `documentary_review` | Empty/null; no scientific approval is assumed |
| `documentary_assessment` | true; attempt a fresh documentary assessment when execution cannot support a grade |
| `minimum_grade` | null, or A/B/C/D; reports state whether the requested minimum was met |
| `catalogs` | Empty until you select exact shared bundles |

Scientific packages belong in a reviewed custom Linux image. Build it before a
verification, using pinned package versions and hashes, then run the configuration
helper with that installed image name and a **new** output filename. The helper
saves its immutable image ID. Include only the required scientific tools; do not
bake account credentials into an image. Trials never run host `pip` or install
dependencies. Images must provide Python 3, `/bin/sh` and `cp`.

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

## Scientific review

Running a method successfully does not qualify its science. List saved candidates:

```powershell
python scripts/local_catalog.py list --workspace "D:\Su Lab\sci-ai-verifier"
```

The output includes `candidate_fingerprint`. An independent reviewer assesses the
exact method, source/answer mapping, units, coverage, uncertainty, leakage,
controls and scientific applicability before you enter a review in settings.
Use a reviewer qualified for the actual domain. Do not mark a method approved
merely to obtain a letter grade.

An A/B/C review has exactly `candidate_fingerprint`, `source_digest`,
`environment_digest` (the latter two are shown in the plan audit), `model_ids`
(the exact observed model IDs being approved), `scope` (the exact claim
scope), `reviewer`, `reviewed_at`, `provenance`, `grades` (supported letters),
`independent: true`, `scientific_basis`, `coverage`, `uncertainty`, `independence`,
`trial_policy: "all-trials-v1"`, and `minimum_trials` (1–20). All descriptive fields
are nonempty strings. Store actual review evidence in `provenance`; do not invent
a reviewer or attestation. The planner cannot write these operator settings.

The policy requires complete scored trials, zero invalid observations and
unanimous scored-status agreement within each case. A/B need at least three
trials per case; C may use one if separately authorized. A failed claim can have
strong evidence. A downgrade needs its own supported rubric predicate. No eligible
grade triggers the documentary path, not an invented scientific pass.

A D authorization has `rubric_ref`, `reviewer`, `reviewed_at`, `provenance` and
`independent: true`. The exact installed rubric and digest can be inspected with:

```powershell
python scripts/local_policy.py
```

The assessor always uses a new no-tool Claude session with a bounded cited packet.
D means documentary consistency only. Without independent rubric authorization,
the assessment is saved without a scientific grade. U/inconclusive means no
acceptable evidence was found; an unavailable tool or assessor is an operational
failure instead.

## Shared catalog and contributions

To reuse a bundle or reviewed catalog release, add `{ "location": "absolute file path or public HTTPS URL",
"sha256": "exact reviewed digest" }` under `catalogs`. First use verifies and
requalifies it; subsequent uses can read its cached bytes offline. Python
candidates still require their local container for controls and scoring. Operator
scientific approvals are not imported from someone else's asserted status.
Choose an updated release deliberately by its new digest; existing runs retain
their original pins. Historical registry releases remain supported by
`scripts/catalog_release.py` for the historical profiles.

To propose your candidate, first inspect the candidate and **every reference's
redistribution rights**. Export only the selected candidate IDs:

```powershell
python scripts/local_catalog.py export --workspace "D:\Su Lab\sci-ai-verifier" --candidate CANDIDATE_ID --file ".verifier\candidate-proposal.json" --authorization "I authorize redistribution of this candidate and all included reference assets under their recorded licenses."
```

Only run that command when its authorization statement is true. It creates a
local reviewable file and prints its SHA256. It does not upload anything. The
bundle excludes subject observations, logs, settings and private review records;
reference content and case inputs are included, so inspect them before sharing.

After reviewing that exact file, you may explicitly submit a draft PR using your
own signed-in [GitHub CLI](https://cli.github.com/):

```powershell
python scripts/local_catalog.py publish --workspace "D:\Su Lab\sci-ai-verifier" --config ".verifier\local-settings.json" --file ".verifier\candidate-proposal.json" --sha256 EXACT_PRINTED_HASH --repository njdjyxz/sci-ai-verifier --approve-publication
```

This uploads the proposal and opens a draft PR. It does not merge or approve it.
If publication fails, retry the same file and command; completed stages and the
PR identity are reconciled without executing the submitted skill again.
Maintainers must independently review candidates before promoting a catalog
release. Catalog review does not supply the separate, source/environment/model
review required for scientific grades.

### Prepare and distribute a reviewed catalog release

This is maintainer work; ordinary personal verification does not require it.
Save the actual independent review records as a JSON list. Each record must have
exactly `candidate_ref`, `decision` (`approved_for_catalog` or `retired`),
`reviewer`, `reviewed_at`, `provenance`, `independent: true`, `scope`, `coverage`,
`uncertainty` and `redistribution`. All fields except `independent` are nonempty
strings. Include one record for every candidate in the exported bundle. The
program checks these records and reruns mechanical qualification; the maintainer
is responsible for verifying the reviewer's identity and evidence.

After inspecting the bundle and real reviews, explicitly prepare a release:

```powershell
python scripts/local_catalog.py release --file ".verifier\candidate-proposal.json" --sha256 EXACT_BUNDLE_HASH --reviews ".verifier\catalog-reviews.json" --catalog-id personal-methods --version 1.0.0 --config ".verifier\local-settings.json" --output ".verifier\catalog-1.0.0.json" --approve-promotion
```

This writes a new local file and prints its exact hash. It uploads nothing and
does not overwrite an existing release. The default supported runtime range is
0.7.0 inclusive to 0.8.0 exclusive; maintainers may supply a tested range using
`--minimum-runtime` and `--maximum-runtime-exclusive`.

For an update, add `--previous` and `--previous-sha256` for the exact preceding
release and increase `--version`. The bundle must retain every previous candidate
ID, with explicit `retired` review decisions for withdrawn methods. New runs
exclude retired IDs even when their candidate bytes are cached. An active run
keeps its original release and retirement set. Select only one version of each
catalog in a configuration; conflicts and incompatible runtimes stop preflight.

To distribute the prepared release, use the same `publish` command above with
the **release** file and its hash. This prepares a draft PR containing
`catalog/releases/RELEASE_HASH.json`. After actual maintainer review and merge,
consumers use that file's public raw URL, preferably with the exact GitHub commit,
and its SHA256 in `catalogs`. Releases are independent data files; compatible
updates do not require reinstalling the verifier. Cached exact bytes work offline.
Importing a release with the maintenance `import` command installs its candidate
bytes; configuring that release under `catalogs` applies its inventory to new
runs. No command merges a PR, silently upgrades a run or grants a scientific grade.
