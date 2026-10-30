# Documentation index

Entry point. The project has many documents (53 in each language: 45 in `docs/` and 8 in the root, with a parallel Russian set in
`docs/ru/`); this page is the map: what to read, when, and what of it is machine-checked.

## If you are new here

1. [../README.md](../README.md) — what the tool does and its three invariants.
2. [PROJECT_MAP.md](PROJECT_MAP.md) — the whole picture in 15 minutes.
3. [../BUILD.md](../BUILD.md) — build, tests, artefacts.
4. [verification/matrix.md](verification/matrix.md) — what proves that it works.

## Map by question

| Question | Document |
| --- | --- |
| What it is and how to use it | [../README.md](../README.md), [USAGE.md](USAGE.md), [demo.md](demo.md), [demo_cli.md](demo_cli.md) |
| How the system is built | [../ARCHITECTURE.md](../ARCHITECTURE.md), [PROJECT_MAP.md](PROJECT_MAP.md) |
| Why the decisions were made | [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) |
| Format and rule contracts | [CONTRACT.md](CONTRACT.md), [PROTOCOL_API.md](PROTOCOL_API.md), [CAPTURE_API.md](CAPTURE_API.md), [schemas/](schemas/) |
| Interpretation rules v1/v2 | [RULE_V1_V2.md](RULE_V1_V2.md) |
| The corpus and its analysis | [CORPUS_ANALYSIS.md](CORPUS_ANALYSIS.md), [REAL_CORPUS_ANALYSIS.md](REAL_CORPUS_ANALYSIS.md), [DATASET_INVESTIGATION.md](DATASET_INVESTIGATION.md), [REFERENCE_INVESTIGATION.md](REFERENCE_INVESTIGATION.md) |
| Metrics and benchmarks | [METRICS.md](METRICS.md), [BENCHMARK.md](BENCHMARK.md) |
| The web interface | [WEB.md](WEB.md) |
| The interface and its checks | [UI_TESTING.md](UI_TESTING.md), [GUI_VERIFICATION.md](GUI_VERIFICATION.md), [UX_COHERENCE_PLAN.md](UX_COHERENCE_PLAN.md) |
| Installation and artefacts | [INSTALL.md](INSTALL.md), [BINARY.md](BINARY.md) |
| Portability | [PORTABILITY.md](PORTABILITY.md) |
| Settings | [SETTINGS.md](SETTINGS.md) |
| Style and development | [STYLE.md](STYLE.md), [DEVELOPMENT.md](DEVELOPMENT.md), [GIT_HYGIENE.md](GIT_HYGIENE.md) |
| The boundaries of the project | [BEYOND_SCOPE.md](BEYOND_SCOPE.md) |
| Audit and compliance | [AUDIT.md](AUDIT.md), [STACK_COMPLIANCE.md](STACK_COMPLIANCE.md), [INTEGRATION_CHECKLIST.md](INTEGRATION_CHECKLIST.md) |
| Defence and demonstration | [DEFENSE_CHECKLIST.md](DEFENSE_CHECKLIST.md), [DEFENSE_FAQ.md](DEFENSE_FAQ.md), [DEMO_CHEATSHEET.md](DEMO_CHEATSHEET.md), [FAQ_FOR_JUDGES.md](FAQ_FOR_JUDGES.md), [PRESENTATION_VERIFICATION.md](PRESENTATION_VERIFICATION.md), [SUBMISSION.md](SUBMISSION.md) |
| Plans and progress | [ROADMAP.md](ROADMAP.md), [../PROGRESS.md](../PROGRESS.md), [../CHANGELOG.md](../CHANGELOG.md) |
| Module specifications | [modules/](modules/), [modules/module-map.md](modules/module-map.md) |
| Build and checks | [../BUILD.md](../BUILD.md), [verification/matrix.md](verification/matrix.md) |

## Two languages

`docs/*.md` is the English set, `docs/ru/*.md` the Russian one. The rule: a change to a contract
or to behaviour updates **both** sets. Language parity is no longer a manual promise — it is
checked by `make docs-check` (`tools/docs_pdf.py --check`): every document must have a translation
in the other language and a PDF in both.

## Rules

1. A document that claims behaviour must have a row in
   [verification/matrix.md](verification/matrix.md).
2. A new module is described following [modules/module-template.md](modules/module-template.md);
   the presence of the 11 sections is checked by `make docs-check`.
3. Links point only at the current repository address (`ForgeLabHub/ForgeMadrigalProtocolLab`);
   `make docs-check` verifies that.

## Project management

- `forge.sh` / `forge.bat` — start, stop, logs, tests, the database and containers with one
  command; see the section in the README.
