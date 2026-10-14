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

## 2026-10-14 (rework)

- Done: interface rework on `rework/ui-usable` — the start guide is a one-line
  strip that no longer forces a wide window, the Russian catalogue has no
  vanished or unfinished entries, and the language-switch tests are order
  independent. Documentation added: `docs/DEVELOPMENT.md` (translation
  workflow, the mandatory strip step after `lupdate`), the `127.0.0.1` binding
  note in `docs/WEB.md`, and the test count synced to 846 everywhere.
- Broken: none. Full suite 846 passed, `ruff check .` clean.
- Next: usability pass for a first-time user (empty-state checklist, hypothesis
  wizard, rule builder without YAML, provenance inspector, sample project).
