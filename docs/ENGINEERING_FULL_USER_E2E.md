# datarelay-link-docs — Full User E2E

**ChatGPT itself is the executor and final auditor.** ChatGPT performs realistic reader/user missions through a real Chromium/Chrome browser on the exact candidate. Another agent, scripted replay, CI, curl/API probe, or static source test cannot substitute.

Run mission-first and black-box. At minimum cover first-entry discovery, navigation to a primary guide/task, search or equivalent discovery to a second relevant page, cross-link/deep-link continuity, published language continuity where applicable, and realistic failure/recovery such as unknown route, empty/no-result search, Back/Forward, reload, and direct deep link.

A finding is not a stop condition. Continue every safe independent mission, freeze the complete finding set, batch-remediate, and rerun invalidated E2E from the beginning. If remediation changes the public surface/contract, rerun Surface Reconciliation.

Use a clean deployed preview or public exact-candidate build and record candidate identity. Retain machine-readable mission/findings ledgers and a ledger-derived summary. PASS requires 100% applicable mission/real-effect coverage, zero mandatory FAIL/PARTIAL/BLOCKED, zero unresolved blocking finding, and cleanup of run-owned browser/test state.

The final clean Full User E2E and Surface Reconciliation must bind to the **same exact HEAD**. Only after ChatGPT directly executes and finally audits both gates may the authoritative release Work Packet record terminal product-quality closure and freeze that HEAD.
