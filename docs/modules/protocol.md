# Module: the rule engine (src/protocol)

## 1. Purpose and boundaries
Applies declarative rules to a reassembled stream: message framing, field types, control values.
Produces a result in which a fact and a hypothesis are distinguishable.
It does not: read captures directly or decide for the engineer — the rule belongs to a human.

## 2. Use cases
- Applying a rule to a corpus of sessions; obtaining matches and counterexamples.
- Updating a rule with version v2 without touching the source bytes.
- Failure: a rule that does not converge on the corpus → a counterexample tied to bytes.

## 3. Contract
`docs/CONTRACT.md`, `docs/PROTOCOL_API.md`, `docs/RULE_V1_V2.md`, the JSON schemas in
`docs/schemas/` (validated with `jsonschema` in the tests). The CLI — `docs/demo_cli.md`.

## 4. Data
Input: a normalised stream from `src.capture` and a rule (YAML/JSON).
Output: the application result (JSON) and a report with counterexamples. The input bytes are never
modified — that is the reproducibility invariant.

## 5. Permissions
A local tool: there are no access boundaries beyond the file system. No network at all.

## 6. Dependencies
External: `PyYAML`. Inbound: `src.ui`, `src.web`, `src.report`, `src.project`.

## 7. Configuration
The rule and its parameters live in files; there are no global "magic" settings. Application
settings — [docs/SETTINGS.md](../SETTINGS.md).

## 8. Build and debugging
```bash
make test-core
PYTHONPATH=src python -m pytest tests/protocol -q
```

## 9. Tests
`tests/protocol/`: `test_rule.py`, `test_engine.py`, `test_framing.py`, `test_field_types.py`,
`test_stream.py`, `test_result.py`, `test_export.py`, `test_cli.py`. Additionally
`tests/hypothesis/*` — the properties of hypotheses, versions, alternatives and differences.

## 10. Observability
The result documents itself: the status (`matched`, a counterexample), the byte linkage, the rule
version. The report in Markdown/HTML — `src/report`.

## 11. Limitations and readiness
- `matched` means "consistent with the observation", not "proven".
- A rule describes linear structures; nested containers are limited.
- Readiness: a counterexample is mandatory and tied to bytes; changing a rule does not change the
  source data (verified by a test).
