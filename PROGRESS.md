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
- Broken: none. `ruff check .` clean, 618 offline tests pass.
- Next: full-suite and CI check, then hold for review.

## 2026-10-14

- Done: `rework/ui-usable` merged into `main` (start guide, rule builder, web
  capture upload). Documentation resynced to the merged tree: the suite is now
  846 tests (613 without the Qt UI tests), `ruff check .` clean.
- Broken: none. The test count had drifted in the docs (840 → 830 → 846); the
  figure now matches `main`.
- Next: hold for the final release; the deck and screenshots were refreshed on
  `main` separately.
