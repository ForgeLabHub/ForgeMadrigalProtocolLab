# Portability audit — 2026-10-29

## What was already in strong shape

| Area | Observation |
| --- | --- |
| Tests | 10 `tests/` directories (capture, corpus, hypothesis, integration, project, protocol, report, ui, web) |
| CI | a Python 3.12/3.13 × two-OS matrix, a separate `ui-tests` job offscreen, `code-quality`, `pip-audit` |
| Packaging | `pyproject.toml` with `gui-scripts`, the `dev` / `web` split, a desktop file, an installer |
| Documentation | 53 documents per language (45 in `docs/`, 8 in the root) + a complete Russian set in `docs/ru/` — a rarity, not the norm |
| Contracts | `CONTRACT.md`, `PROTOCOL_API.md`, `CAPTURE_API.md`, JSON schemas in `docs/schemas/` |
| Product invariants | "observation ≠ hypothesis", a mandatory counterexample, reproducibility |
| Dependencies | the base ones pinned to exact versions (`PySide6==`, `dpkt==`, `PyYAML==`) |

## Gaps and what was done

| # | Gap | Impact | Closed by |
| --- | --- | --- | --- |
| 1 | No `Makefile` | dozens of commands in the README/CI, reproducible only by hand | a `Makefile`: `doctor`, `test-core`, `test-web`, `test-ui`, `wheel`, `package`, `docs-check`, `verify` |
| 2 | No "core / interface" split in the check commands | the project could not be checked locally without Qt | `make test-core` (446 tests, ~15 s) against `make test-ui` |
| 3 | No host check | a missing `libEGL` surfaced as a PySide6 crash | `scripts/doctor.sh` |
| 4 | The build did not prove that the artefact installs | the wheel could be built but not start | `make package` + the `package` job (a clean venv, a headless `--help`, a dependency-set check) |
| 5 | 53 documents per language without an entry point | a newcomer did not know what to read | `docs/index.md` with a map by question |
| 6 | No "claim → check" matrix | "CI is green" was not decoded | `docs/verification/matrix.md` |
| 7 | No module specifications | the boundaries were described in the general ARCHITECTURE, not per module | `docs/modules/{capture,protocol}` + a template + a CI check |
| 8 | Links pointed at the former repository address (`Pavel1778/...`) | clones and releases did not match the current home | 21 links replaced with `ForgeLabHub/ForgeMadrigalProtocolLab`, `make docs-check` catches a regression |
| 9 | Nothing checked that the built package does not pull the web/dev dependencies | "I installed it and it brought fastapi" | a check in the `package` job |

## What remains open

- The `dev`/`web` requirements are given as ranges: strict release reproducibility needs a
  `pip freeze` snapshot inside the artefact.
- The English and Russian documentation sets could diverge; there is no automatic comparison —
  closed on 2026-10-30: `tools/docs_pdf.py --check` fails the build when a document has no
  translation or no PDF.
- The interface tests need PySide6 — outside CI they are available only on a machine with Qt.
- The declared platform is Linux x86-64; Windows/macOS are not supported.
