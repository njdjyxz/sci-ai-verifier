# Claude Desktop acceptance record

Status: **Pending installation and a live app test.** Scripted Python and MCP tests are not a substitute for this record.

| Field | Record after the live test |
|---|---|
| Date and tester | Pending |
| Claude Desktop version | Pending |
| Visible model label | Pending |
| Exact model ID/version | Unavailable via MCP; fill only from an independent reliable source |
| Extension package SHA-256 | Copy from `dist/checksums.json` |
| Skill ZIP SHA-256 | Copy from `dist/checksums.json` |
| Reference-claim run ID and manifest | Pending |
| Zero-claim run ID and manifest | Pending |
| Instruction-conflict run ID | Pending |
| Observed tool sequence and state | Pending |
| Source quotes and claim-quality review | Pending |
| Unexpected other-tool use or missing context | Pending |
| Resume/cancel behavior observed | Pending |
| Conclusion and remaining limitations | Pending |

## Compatibility target, established by this record

These fields exist because scripted tests cannot answer them. Record what the app did, not what it should do. Until they are filled, the required MCP compatibility target is undecided and no second protocol implementation should be written.

| Field | Record after the live test |
|---|---|
| Extension loaded and listed its tools | Pending |
| Tool list shown in the install dialog | Pending; the manifest declares seven tools with `tools_generated: false` |
| Protocol version the app negotiated | Pending; the server offers `2025-06-18`, `2025-03-26`, `2024-11-05` |
| App sent `notifications/initialized` before `tools/list` | Pending; the server requires it, which is stricter than the lifecycle specification |
| Bootstrap accepted without truncation | Pending; the assembled result is roughly 85 KB, down from 227 KB |
| Path spelling the model actually sent for `source_path` | Pending; any spelling of the authorized location is accepted |
| Independent MCP client used, if any | Pending; none is bundled, and the test suite has only a specification-derived stand-in |
| Python interpreter selected, and its version | Pending; the 3.11 floor is unverified because only 3.14 is installed here |

Completion requires the reference claim to be traced to the correct file, the zero-claim fixture to stop with an empty manifest, and conflicting source instructions to remain data. Every successful fixture must stop at the Stage 2 extraction checkpoint without grades or scientific verdicts. Review the saved event journal alongside what the app actually did.
