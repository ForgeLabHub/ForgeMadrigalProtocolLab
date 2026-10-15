#!/usr/bin/env python3
"""Fill an English ``.ts`` catalogue with the source strings.

English is the source language of the window, so every ``tr()`` string is
already English. A catalogue for it is still useful: it makes the set of
translated strings explicit, lets a reviewer see them in one file, and gives the
translation check a second catalogue to hold to the same 100 % bar as Russian.

The script rewrites each ``<translation>`` with its ``<source>`` text and clears
the ``unfinished``/``vanished``/``obsolete`` markers, so ``pyside6-lrelease``
reports the catalogue as fully finished.

Usage:
    python3 scripts/fill_english_catalogue.py src/ui/locale/madrigal_en.ts
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ElementTree

_STALE_MARKERS = ("unfinished", "vanished", "obsolete")


def fill(path: str) -> int:
    """Fill every message in *path* with its source text; return the count."""
    tree = ElementTree.parse(path)
    root = tree.getroot()
    filled = 0
    for message in root.iter("message"):
        source = message.findtext("source")
        translation = message.find("translation")
        if translation is None or source is None:
            continue
        if translation.get("type") in _STALE_MARKERS:
            del translation.attrib["type"]
        translation.text = source
        filled += 1
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return filled


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    filled = fill(argv[1])
    print(f"filled {filled} message(s) in {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
