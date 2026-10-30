# Verification matrix

The project is large, so "CI is green" says little without a breakdown: below is which claim is
proven by what.

| Claim | Check | Command | CI |
| --- | --- | --- | --- |
| PCAP/PCAPNG parsing neither loses nor invents bytes | `tests/capture/*` | `make test-core` | `ci.yml` → `test` |
| Stream reassembly survives gaps, overlaps and retransmissions | `tests/capture/test_reassembly*`, `test_fragmentation`, `test_boundaries` | `make test-core` | `ci.yml` → `test` |
| Every byte is linked to the packet that produced it (provenance) | `tests/capture/test_provenance.py` | `make test-core` | `ci.yml` → `test` |
| Interpretation rules are deterministic and data-independent | `tests/protocol/test_engine.py`, `test_rule.py`, `test_framing.py` | `make test-core` | `ci.yml` → `test` |
| Hypotheses and counterexamples are distinguishable (observation ≠ conclusion) | `tests/hypothesis/*` | `make test-core` | `ci.yml` → `test` |
| Work on the real corpus | `tests/integration/*`, `tests/hypothesis/test_real_corpus.py` | `make test-integration` | `ci.yml` → `test` |
| The report and the export are reproducible | `tests/report/*`, `tests/integration/test_reference_report.py` | `make test-integration` | `ci.yml` → `test` |
| The project container is portable | `tests/project/*` | `make test-integration` | `ci.yml` → `test` |
| The interface does not lose state and is geometrically correct | `tests/ui/*` (offscreen) | `make test-ui` | `ci.yml` → `ui-tests` |
| The web interface works | `tests/web/*` | `make test-web` | `ci.yml` → `test` |
| Style and static analysis | `ruff check .` | `make lint` | `ci.yml` → `code-quality` |
| No known vulnerabilities in the dependencies | `pip-audit` | — | `ci.yml` → `audit` |
| The built wheel installs and starts | `make package` | `make package` | `portability.yml` → `package` |
| The documentation is complete, the links are alive and the languages match | `make docs-check` | `make docs-check` | `portability.yml` → `docs` |
| The environment is suitable before start-up | `make doctor` | `make doctor` | locally |

## What is proven locally and what only in CI

| Level | Where it is checked |
| --- | --- |
| The Qt-free core (`make test-core`, 446 tests) | locally in ~15 s and in CI |
| The web interface (`make test-web`) | locally and in CI |
| The interface (`make test-ui`) | only where PySide6 and the system Qt libraries exist |
| The package (`make package`) | locally in a venv and in CI |

The local core tests run without PySide6; `dpkt` and `PyYAML` are mandatory.

## What is deliberately not checked

- Parity of the English and Russian documentation sets — checked by `tools/docs_pdf.py --check`
  since 2026-10-30 (a document without a translation fails `make docs-check`).
- Compatibility with Windows/macOS: the project targets Linux x86-64.
- Performance on captures far larger than the corpus.
- The quality of hypotheses: what is checked is consistency and the presence of counterexamples,
  not the "truth" of the protocol.
