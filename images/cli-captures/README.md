# Data Relay Link CLI screenshot evidence

These assets deliberately replace **invented Web UI** illustrations. Data Relay Link v2.4 is CLI-first.

## What the PNGs contain

- The **terminal text** comes from retained, actual Data Relay Link v2.4 development `drlink` executions: interactive pseudo-terminal recordings (`*.typescript`), exit-code-qualified stdout records (`*.json`, where `actual_command` is recorded), or prior real E2E `*.stdout` files.
- A dark terminal frame, title, orange numbered line markers, right-hand guidance, and a source/date/footer label have been added for documentation. This is **a readable image rendering of real terminal capture evidence**, not a pixel-for-pixel camera capture of the original desktop terminal theme.
- Where metadata included an actually executed command, the header uses the shell prompt `$ drlink ...`. Interactive PTY prompt text such as `drlink> menu` is taken directly from the recorded session. For older stdout-only evidence without an independent command field, the image explicitly says that the exact command is not in that file; no command text is invented.
- Real IP addresses and personal hostnames have been replaced with visible redaction placeholders; long outputs may be excerpted or visually clipped. **No successful policy, enrollment, TLS or network result was synthesized.**
- Not all captures represent successful configured state. For example `server-inbound-default.png` shows **Remote Access No Policy → ALLOW**; `server-egress-default.png` shows **Internet Access No Policy → DENY**; and `mcp-direct-not-ready.png` is a real **MCP unavailable in Direct mode** warning.
- Source candidates are `bdc47ab0c9b681f06744026eb519b83056f7f28d` (2026-10-13/14 PTY/E2E) and `4d07644cdf248d9eebe36bcef341beb2028f1000` (2026-10-17 public CLI E2E). **They are not a claim that either candidate is today's stable release.** The product's actual installed version and live help take precedence.

## Traceability and verification

`provenance.json` lists, for every screenshot, the retained test-evidence source, candidate Source HEAD, original input SHA256, excerpt SHA256, capture date and annotations.

Run from the docs repository:

```bash
python3 tools/check_use_case_docs.py
git diff --check
```

The validation checks that screenshot files are real PNGs with matching provenance and that all English/Korean use-case pages contain the same screenshots with visible per-image captions.

## Safety and maintenance

These images must never be presented as the product's graphical application UI. Menu numbers, settings, and command output may evolve: refresh captures from the **current** exact-HEAD real CLI E2E whenever changing the public CLI contract. Do not alter an output line to depict a result not produced by the product. Keep credentials/tickets/private hosts out of public evidence.
