# Module map: what to borrow for another project

Russian version: [../ru/modules/module-map.md](../ru/modules/module-map.md).

The table answers "what to take if I need X": the minimal set of files, the dependencies, and what
has to be replaced. The module specifications are in [capture.md](capture.md) and
[protocol.md](protocol.md).

| Need | Files to take | External dependencies | Replace |
| --- | --- | --- | --- |
| PCAP/PCAPNG and TCP session parsing | `src/capture/parser.py`, `src/capture/session.py` | `dpkt` | the list of supported link layers |
| Stream reassembly with gap and overlap diagnostics | `src/capture/reassembly.py`, `src/capture/fragment.py` | — | the policy for conflicting overlaps |
| Byte-to-packet provenance | `src/capture/provenance.py`, `src/capture/stream.py` | — | the "offset → packet" index model |
| A normalised JSON contract between stages | `src/capture/export_*.py`, `docs/schemas/` | `jsonschema` (for validation) | the contract field set |
| Message framing (4 strategies) | `src/protocol/framing.py` | — | your own boundary strategies |
| A declarative rule engine with field types | `src/protocol/engine.py`, `src/protocol/rule.py` | `PyYAML` | the type and operator sets |
| Result classification and counterexamples | `src/hypothesis/` | — | the `matched`/`mismatched` criteria |
| Rule versioning and version comparison | `src/hypothesis/versioning.py` | — | the version storage scheme |
| A portable project with a manifest and sha256 | `src/project/` | stdlib (`zipfile`, `sqlite3`) | the manifest contents |
| Reports in Markdown and self-contained HTML | `src/report/` | — | the template and the section set |
| A hex view linked to packets | `src/ui/hex_view.py` | PySide6 | — (the widget is self-contained) |
| A local web interface over the same engines | `src/web/` | FastAPI, uvicorn, Jinja2 | the page templates |
| Bilingual documentation with parity | `tools/docs_pdf.py`, `Makefile` (`docs-check`) | markdown, weasyprint | the document set and the languages |

## Transfer rules

1. The core (`capture`, `protocol`, `hypothesis`, `project`, `report`) depends on neither Qt nor
   the network: it can be taken whole and verified with `make test-core` without graphics.
2. An external system always sits behind an adapter: `dpkt` is isolated in `parser.py` and the file
   storage in `project/storage.py`; the implementation is replaced, not the calling code.
3. The "fact ≠ hypothesis" invariant is part of the contract: a rule application result carries a
   status and a byte linkage, so it cannot be "improved" silently.
4. Tests are part of the module: every module has a directory of the same name under `tests/`.
5. Application settings are one dialogue and one key set ([docs/SETTINGS.md](../SETTINGS.md)), with
   no "magic" environment variables.
