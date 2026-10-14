# Progress

Daily checkpoint of the work. One entry per day: done, broken, next.

## 2026-10-09

- Done: repository foundation created (structure, contracts, schemas, style,
  CI, license, packaging).
- Broken: none.
- Next: capture engine modules and fixtures.

## 2026-10-09 (later)

- Done: rule field types (float, varint, tlv, bits), CSV/JSONL result export,
  request/response pairing with a confidence, and researcher annotations stored
  in the project and rendered in both reports.
- Broken: none. `ruff check .` clean, the offline suite passes (no UI/web extras).
- Next: full-suite and CI check, then hold for review.

## 2026-10-14

- Done: `rework/ui-usable` merged into `main` (start guide, rule builder, web
  capture upload). Documentation resynced to the merged tree: the suite is now
  846 tests (613 without the Qt UI tests), `ruff check .` clean.
- Broken: none. The test count had drifted in the docs (840 -> 830 -> 846); the
  figure now matches `main`.
- Next: hold for the final release; the deck and screenshots were refreshed on
  `main` separately.

## 2026-10-14 (interface test isolation)

- Done: the interface-language tests are order independent. `tests/ui/conftest.py`
  now removes the `QTranslator` a test installs, so a window closed with Russian
  selected no longer leaks its catalogue into the next module. Added
  `docs/DEVELOPMENT.md`: the translation workflow and the mandatory `lupdate`
  strip step.
- Broken: none. Full suite 846 passed, `ruff check .` clean.
- Next: usability pass for a first-time user (hypothesis wizard, bundled sample
  project); the start guide, rule builder and provenance card are already in.

## 2026-10-14 (ux-select merged)

- Done: `feat/ux-select` merged into `main` (PR #59) — the bundled demo
  (`src/ui/samples/`, `File -> Open demo`, web `GET /demo`), the timeline view
  and the web status guidance. Documentation resynced: the suite is now
  **849 tests** (615 without the Qt UI tests), `ruff check .` clean.
- Broken: none. The test count had drifted in the docs (846 -> 849); the figure
  now matches `main`.
- Next: full GUI usability overhaul (`ux/full-overhaul`) — empty-state screen,
  Russian-only strings, rule wizard, provenance inspector.
