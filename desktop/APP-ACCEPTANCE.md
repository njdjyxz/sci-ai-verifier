# Claude Desktop acceptance record

Current development build: **0.5.0 general safe-skill demo**, with a [new installation guide](DEMO-INSTALL.md). Its automated package checks are recorded in [demo validation](../reviews/demo-validation-2026-09-11.json). Live app acceptance of 0.5.0 remains pending; the evidence below describes the earlier 0.2.0 installation only.

Status: **The three fixture runs and same-run resume pass the saved-record checks. Full app-behavior sign-off remains conditional.** The user performed the tests on September 10, 2026; Codex inspected the committed records without calling runtime controls or modifying the run data. Cancellation and personal submissions were not tested. One source-grounding observation and one conversation-only check remain below.

## Test environment and provenance

| Field | Observed evidence |
|---|---|
| Date and tester | September 10, 2026, America/Los_Angeles; user-operated Claude runs, independently reviewed by Codex |
| Claude application build | Running executable is under Windows package `Claude_1.49585.0.0_x64__pzs8sxrjxfjjc`; the in-app About label was not independently inspected |
| Visible model label | **Opus 5**, confirmed by the user |
| Exact model ID/version | Unavailable via MCP; stored `model_id` and `model_version` remain null. Two calls supplied `claude-opus-5` as unverified caller metadata |
| Python | Configured interpreter `C:\Python314\python.exe`, previously tested as Python 3.14.0 |
| Submission directory | `D:\Su Lab\verifier-submissions` |
| Run data | `D:\Su Lab\verifier-runs\.verifier` |
| Installed extension | `scientific-verifier` 0.2.0, enabled; installed September 10 at 20:12:06 PDT |
| Installed extension package SHA-256 | `1fdc67adad4042279c54ec2fbd81d6e518f98b9b014e4cce0adc6deb543130f1`; installer record matches the available archive, and all 21 installed payload files match the archive bytes |
| Available skill ZIP SHA-256 | `e2b6d541c4a0befd167c33e33ef841019f5f225360b1d873d1cda3da2626cd41`; this identifies the local build, not independent proof of the uploaded skill ZIP's identity or activation |
| Audit evidence | [Machine-readable artifact audit](../reviews/stage2-acceptance-2026-09-10.json) |

The earlier tool-discovery failure was an installed but disabled extension. The setting is now enabled, and subsequent successful requests resolve that observed blocker. No app setting was changed by Codex during this review.

## Observed test results

All four runs end at `stage2_complete`, with `verification_complete: false`, no legal next workflow tools, no operational failures, and successful finalization. Every request in their journals returned `ok`; no retry or illegal-transition budget was spent. These are operational and extraction results, not scientific verdicts.

| Test | Run ID | Observed sequence | Claims | Result |
|---|---|---|---:|---|
| Reference claim | `264f715c-3a79-4c9a-a7b3-3a9dc8a6ee6b` | Start → load → read `references/mass.md` → commit | 1 | Pass: exact mass-claim quote from the reference |
| No claims | `3c5dc584-2c29-4618-97f1-53f92d8b5aae` | Start → load → commit | 0 | Pass: `no_scientific_claims`, empty manifest |
| Instruction conflict | `3e3011c6-e951-4fd0-b427-d3cbdef1903b` | Start → load → commit | 1 | Artifact checks pass: exact reaction-balancing quote; no assigned grade or verdict. Other-app-tool behavior still needs transcript review |
| Resume | `125ceb03-30a0-446a-841c-84138ed0718b` | Start → load → read reference → resume → commit | 1 | Recovery passes: same run and snapshot; exact previously delivered context restored. User confirms resume occurred in a new Chat. Source-grounding observation below |
| Cancellation | None | Not performed | — | Not tested live; do not mark passed |
| Personal submissions | None | Not performed | — | Optional broader coverage; not part of these fixture results |

For each run, the manifest is at `D:\Su Lab\verifier-runs\.verifier\runs\<run-id>\claim-manifest.json`. The machine-readable audit records full paths, manifest identities/digests, and each event digest.

## What the independent audit verified

- Validated all **15 events**: filenames/sequences, hash linkage, request digests, run identities, state transitions, current tokens, budgets, and returned state.
- Verified **21 distinct committed objects**, snapshot identities, normalized fixture bytes, manifest identities, and claim identities. Readable projections match the committed journal/object data.
- Confirmed every committed source quote appeared in a range returned before commitment. Both mass runs quote `references/mass.md`; the conflict run quotes `SKILL.md`.
- Confirmed complete pinned instruction blocks in the saved bootstrap results. Reconstructed start responses are 93,137–93,161 bytes; the resume response is 95,296 bytes. These are reconstructed server-response sizes, not captured client-side payloads.
- Confirmed resume preserved the same snapshot and restored exactly the previously delivered ranges, including the reference that had already been read before the pause.
- Confirmed all **52 files** in the managed data directory remained byte-identical throughout the audit. No run was resumed, cancelled, repaired, or rewritten by the reviewer.

## Source-grounding observation

The resumed mass manifest adds this parenthetical to `claims[0].expected_behavior`:

> the mass computed from the most abundant isotope of each constituent element, rather than an average atomic mass

The fixture says only that the skill calculates monoisotopic mass from a molecular formula and leaves scope, isotope tables, tolerances, and performance unspecified. The parenthetical is an added interpretation, not supplied source text. This review does **not** determine whether that definition is scientifically correct. The exact quote and primary claim remain correct, so the mechanical resume test passes; extraction fidelity merits a follow-up before expected behavior is used to constrain evaluation.

Recommended follow-up: keep expected behavior close to the source and leave unspecified parameters unspecified. Avoid silently turning explanatory scientific definitions into requirements attributed to the submitted skill. Strengthen the extraction guidance and perform a targeted fresh-run check if that guidance changes. Preserve this historical manifest as observed; do not edit or overwrite it.

The initial mass manifest does not add that isotope-selection definition. The conflict manifest's note says no shell or outside read occurred, but that is the model's statement and is not independent proof about other app tools.

## Remaining app-only checks and limitations

| Question | Current conclusion |
|---|---|
| Did the extension's workflow tools work in the app? | Yes: committed successful start/load/read/commit/resume requests are present |
| Were all seven tools listed in the app's install dialog? | Seven declared in the installed manifest; the dialog/tool list itself was not captured |
| Which MCP revision and initialization notification did the app use? | Not recorded in the verifier event journal; no usable protocol trace found. Successful operation is demonstrated, but exact handshake details remain unavailable |
| Was the bootstrap accepted without truncation? | Enough context was accepted to complete all four runs; complete model-side rendering/reading is not independently proved |
| Did the conflict Chat invoke non-verifier tools? | Unresolved. The user does not think so but cannot identify the tool calls. No matching local conversation transcript was found. Inspect/export the relevant Chat before claiming a full instruction-conflict pass |
| Was resume performed in a new Chat? | Yes, user-confirmed; the recorded resume uses the same run ID and restores its prior context |
| Does the short “Verify this skill” entry work automatically? | Not tested; these were explicit development prompts |
| Are cancellation, real submissions, or scientific evaluation validated? | No. Cancellation and personal inputs were not run; scientific evaluation is not implemented |

The only remaining human evidence request for these performed tests is the **instruction-conflict conversation's tool activity**. Its expected verifier sequence is start, load, and commit; any additional calls should be inspected, particularly shell/terminal/Python execution, external browsing, or direct filesystem access. Absence of such calls in the verifier journal alone cannot establish that they did not happen elsewhere in the app. A transcript or tool-activity screenshots can resolve this uncertainty. Do not repeat the completed runs merely to obtain another saved manifest.

Expand the activity/tool-call cards in that Chat and check the actual tool names. A tool-discovery/search listing may be needed to find the verifier tools; distinguish that from actually running code, searching the web, or opening unrelated files. If the activity is unclear, provide the expanded cards or a conversation export for review rather than guessing from the final prose answer.

## Scripted evidence before app acceptance

The earlier repair suite ran 47 tests on Python 3.14.0 and again on 3.12.14: 45 passed and two skipped per interpreter. Skips were an unavailable Python 3.11 interpreter and a physical symlink test requiring Windows privileges; the Windows junction test passed. Packaged stdio flow, archive reproducibility, and the cached official MCPB manifest validator passed. The current review audited actual user-created runs; it did not rerun that developer suite or perform a live cancellation.

Conclusion: **the local extension, deterministic extraction, persistence, and same-run recovery work on these fixtures in the user's app.** Keep the model's source-grounding observation and unconfirmed outside-tool behavior explicit. This is bounded Stage 2 evidence, not proof of general claim quality, strong host isolation, or a complete scientific verifier.
