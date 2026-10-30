# Module: capture parsing (src/capture)

## 1. Purpose and boundaries
Reads PCAP/PCAPNG, identifies TCP sessions and reassembles directed byte streams with diagnostics
for gaps, overlaps and retransmissions. Keeps every byte tied to its packet.
It does not: interpret message content (that is `src/protocol`), or draw the UI.

## 2. Use cases
- Opening a capture with several interface blocks and different link types.
- A session with a gap: the stretch is marked as a gap instead of being filled with zeros.
- An ambiguous overlap: shown as an ambiguity instead of being resolved silently.
- A retransmission: marked, the bytes are not duplicated.
- Failure: a corrupted file → a clear error, with no partially "successful" result.

## 3. Contract
The public functions of the `src.capture` package; the result formats are described in
[docs/CAPTURE_API.md](../CAPTURE_API.md) and the schema in [docs/schemas/](../schemas/). A
normalised capture is serialised to JSON.

## 4. Data
Input: `.pcap`/`.pcapng` files (in the repository — `tests/fixtures/`, `tests/corpus/`).
Output: a normalised capture (JSON) with per-byte provenance. There is no storage of its own:
everything lives in memory and in explicit files.

## 5. Permissions
A local application: access is defined by the file system. The network is not used — only local
files are processed.

## 6. Dependencies
External: `dpkt` (parsing), `PyYAML` (not for captures, but part of the base dependencies).
Inbound: `src.protocol`, `src.ui`, `src.report`, `src.project`.

## 7. Configuration
Paths and modes come from CLI/UI arguments. Encodings and time zones are never "guessed":
timestamps are taken from the file and preserved as they are.

## 8. Build and debugging
```bash
make test-core
PYTHONPATH=src python -m pytest tests/capture -q
```

## 9. Tests
`tests/capture/`: `test_parser.py` (formats), `test_reassembly*.py` (reassembly and its
properties), `test_fragmentation.py`, `test_boundaries.py`, `test_provenance.py`,
`test_streaming.py`, `test_session.py`, `test_export*.py`, `test_deformed_captures.py` (corrupted
inputs), `test_cli*.py`.

## 10. Observability
The diagnostics are returned as part of the result (gaps, overlaps, retransmissions) and appear in
the report. Logs — CLI/UI. There is no hidden state: the result is either complete or carries
explicitly listed defects.

## 11. Limitations and readiness
- TCP/IP (IPv4 and IPv6) and Ethernet-like link layers are supported; exotic links are not
  claimed.
- Memory grows with the capture size: streaming exists, but gigabyte dumps are not the target
  scenario.
- Readiness: per-byte provenance is confirmed by a test; input defects are visible in the result.
