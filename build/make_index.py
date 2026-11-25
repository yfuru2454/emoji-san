#!/usr/bin/env python3
"""Maintainer tool: write index.csv, the emoji <-> file lookup table.

    python3 build/make_index.py

Rebuilds the same gemoji x noto-emoji mapping that update_from_upstream.py
used (at the commit in UPSTREAM_COMMIT.txt), checks that every file it
names exists under collections/, and writes index.csv:

    emoji, codepoint, name, category, collection, path, noto_file, set

`path` is relative to the installed EmOji-san folder (= the SVG path), the
same form QGIS stores in projects, e.g. "Food and Drink/hot_beverage.svg".
`name` is the English CLDR short name (via gemoji). install.py adds a
column with names in the user's own QGIS language at install time.
`set` is the smallest install set holding the emoji; the sets nest, so
basic < advanced < full and upgrading never removes an emoji:
  basic    = the curated core in core_list.txt (also emoji_san_core.xml)
  advanced = basic + the six map categories
  full     = everything

update_from_upstream.py runs this automatically at the end.
"""
import csv
import json
import pathlib
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
from update_from_upstream import (  # noqa: E402
    COLLECTIONS, GEMOJI_URL, NOTO_REPO, NOTO_SVG_DIR, SKIN, noto_code,
    slugify)


def main() -> None:
    sha = (ROOT / "UPSTREAM_COMMIT.txt").read_text().strip()
    gemoji = json.loads(urllib.request.urlopen(GEMOJI_URL).read())
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["git", "init", "-q", td], check=True)
        subprocess.run(["git", "-C", td, "fetch", "-q", "--depth", "1",
                        "--filter=blob:none", NOTO_REPO, sha], check=True)
        files = subprocess.run(
            ["git", "-C", td, "ls-tree", "--name-only",
             f"FETCH_HEAD:{NOTO_SVG_DIR}"],
            check=True, capture_output=True, text=True).stdout.split()
    noto = {f for f in files if f.endswith(".svg")}

    core = set()
    core_file = ROOT / "core_list.txt"
    if core_file.exists():
        for line in core_file.read_text(encoding="utf-8").splitlines():
            if line.strip():
                slug, folder = line.split("\t")
                core.add(f"{folder}/{slug}.svg")

    cat_to_coll = {c: k for k, cats in COLLECTIONS.items() for c in cats}
    used, rows, missing = {}, [], []
    for e in gemoji:
        cat = e.get("category")
        coll = cat_to_coll.get(cat)
        if not coll:
            continue
        em = e["emoji"]
        if any(ord(c) in SKIN for c in em):
            continue
        code = noto_code(em)
        if f"emoji_u{code}.svg" not in noto:
            code = noto_code(em, keep_fe0f=True)
            if f"emoji_u{code}.svg" not in noto:
                continue
        slug = slugify(e["description"], used.setdefault(cat, set()))
        folder = cat.replace(" & ", " and ")
        path = f"{folder}/{slug}.svg"
        if not (ROOT / "collections" / coll / "svg" / path).exists():
            missing.append(path)
        rows.append({
            "emoji": em,
            "codepoint": " ".join(f"U+{ord(c):04X}" for c in em),
            "name": e["description"],
            "category": cat,
            "collection": "map" if coll == "noto_emoji_map" else "people",
            "path": path,
            "noto_file": f"emoji_u{code}.svg",
            "set": ("basic" if path in core else
                    "advanced" if coll == "noto_emoji_map" else "full"),
        })
    if missing:
        sys.exit(f"ERROR: {len(missing)} rows point at missing files, "
                 f"e.g. {missing[:3]} — rerun update_from_upstream.py")

    unknown = core - {r["path"] for r in rows}
    if unknown:
        sys.exit(f"ERROR: core_list.txt names unknown files: {sorted(unknown)[:3]}")

    out = ROOT / "index.csv"
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print(f"wrote {out} ({len(rows)} rows)", dict(Counter(r["set"] for r in rows)))


if __name__ == "__main__":
    main()
