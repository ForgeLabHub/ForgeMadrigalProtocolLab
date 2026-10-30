# Build: from a clean machine to an installed application

The project targets **Linux x86-64**, Python **>=3.12**. The delivery formats are described in
[docs/INSTALL.md](docs/INSTALL.md) and [docs/BINARY.md](docs/BINARY.md).

## Pinned versions

| Tool | Version | Source of truth |
| --- | --- | --- |
| Python | 3.12 and 3.13 (the CI matrix) | `pyproject.toml` (`requires-python`), `ci.yml` |
| PySide6 | 6.8.1 | `pyproject.toml` |
| dpkt | 1.9.8 | `pyproject.toml` |
| PyYAML | 6.0.2 | `pyproject.toml` |
| dev tools | pytest 9.0.3, ruff 0.16.10, mypy 2.4.0, pytest-cov 7.1.0, pip-audit 2.10.1 | `[project.optional-dependencies].dev` |
| web stack | fastapi, uvicorn, jinja2, python-multipart | `[project.optional-dependencies].web` |

The `web` and `dev` requirements are given as ranges: for a reproducible release environment pin
them with `pip freeze` when building the artefact — a deliberate trade-off (see
[docs/audit/portability-audit-2026-10-29.md](docs/audit/portability-audit-2026-10-29.md)).

## Level A — source code

```bash
make doctor          # python, dpkt/PyYAML, PySide6, libEGL, QT_QPA_PLATFORM, ruff, LICENSE
make install-dev     # pip install -e ".[dev,web]"
make lint            # ruff
make test-core       # 446 tests without Qt: protocol, capture, hypothesis (~15 s)
make test-web        # the web interface
make docs-check
```

Level A works without a graphical subsystem: the core does not depend on Qt.

## Level B — artefacts

```bash
make wheel            # dist/*.whl + sdist
make package          # install the wheel into a clean venv and run madrigal-lab --help
```

## Level C — the interface

```bash
make test-ui          # QT_QPA_PLATFORM=offscreen, needs PySide6 and libEGL
```

On a server without a display the interface runs with `QT_QPA_PLATFORM=offscreen`.

## Level D — the full test set

```bash
make test             # all tests/ directories (as in CI)
```

## Level E — installation on a clean machine

```bash
python -m venv /tmp/venv && . /tmp/venv/bin/activate
pip install dist/*.whl
QT_QPA_PLATFORM=offscreen madrigal-lab --help
```

The delivery formats (a binary, a `.deb`-like layout, a desktop file, an installer) are described
in [docs/INSTALL.md](docs/INSTALL.md) and `packaging/`.

## Typical errors

| Error | Cause | Solution |
| --- | --- | --- |
| `ImportError: libEGL.so.1` | the system Qt libraries are missing | install `libegl1 libgl1 libxkbcommon0` |
| `qt.qpa.plugin: could not load the Qt platform plugin "xcb"` | no display | `QT_QPA_PLATFORM=offscreen` |
| The UI tests fail on a runner | no PySide6 or no locale | the CI matrix installs the Qt libraries; locally `make install` |
| `ModuleNotFoundError: src` | run without installing the package | `make install-dev` or `PYTHONPATH=src` |
| `pytest` finds no tests | the venv is not activated | activate `$(VENV)` |

## Proof

`ci.yml` (tests, interface, code quality, dependency audit) and `portability.yml` (packaging, an
installation check, documentation). The claim matrix —
[docs/verification/matrix.md](docs/verification/matrix.md).
