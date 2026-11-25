#!/usr/bin/env python3
"""Maintainer tool: (re)build the distribution payload from upstream.

Run OUTSIDE QGIS, about once a year (new emoji land roughly on Unicode's
annual cycle), on a normal machine with git + network:

    python3 build/update_from_upstream.py

What it does:
  1. fetches gemoji's emoji.json (the standard RGI set, categories,
     English names)
  2. lists the SVGs available in googlefonts/noto-emoji at its current
     main commit (blobless clone — fast, no 1GB checkout)
  3. downloads the curated intersection, renamed to readable slugs,
     into  collections/noto_emoji_map/svg/<Category>/  and
           collections/noto_emoji_people/svg/<Category>/
  4. refreshes LICENSE-noto-emoji.txt and prints a summary

Then review `git status`, commit, tag (e.g. v2027.1), and update the
tag in install.py / README. install.py downloads the tagged repository
archive, so nothing else needs uploading.
"""
import concurrent.futures
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent

GEMOJI_URL = "https://raw.githubusercontent.com/github/gemoji/master/db/emoji.json"
NOTO_REPO = "https://github.com/googlefonts/noto-emoji.git"
NOTO_SVG_DIR = "2D/svg"  # moved from "svg/" in 2025; re-check on failure

COLLECTIONS = {
    "noto_emoji_map": [
        "Animals & Nature",
        "Food & Drink",
        "Travel & Places",
        "Activities",
        "Objects",
        "Symbols",
    ],
    # Country flags are not in 2D/svg (they live in third_party/ with
    # per-country caveats), so "Flags" here only yields the 8 generic ones.
    "noto_emoji_people": [
        "Smileys & Emotion",
        "People & Body",
        "Flags",
    ],
}

SKIN = set(range(0x1F3FB, 0x1F400))
WIN_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                *(f"lpt{i}" for i in range(1, 10))}
THREADS = 16


def noto_code(emoji: str, keep_fe0f: bool = False) -> str:
    cps = [f"{ord(c):x}" for c in emoji if keep_fe0f or ord(c) != 0xFE0F]
    return "_".join(cps)


def slugify(desc: str, used: set) -> str:
    s = desc.lower()
    s = re.sub(r"[‘’“”\"']", "", s)
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    s = re.sub(r"__+", "_", s) or "emoji"
    if s in WIN_RESERVED:
        s += "_"
    base, i = s, 2
    while s in used:
        s, i = f"{base}_{i}", i + 1
    used.add(s)
    return s


def main() -> None:
    print("fetching gemoji ...")
    gemoji = json.loads(urllib.request.urlopen(GEMOJI_URL).read())

    print("listing noto-emoji svg files (blobless clone) ...")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(
            ["git", "clone", "--filter=blob:none", "--no-checkout",
             "--depth", "1", NOTO_REPO, td],
            check=True, capture_output=True)
        sha = subprocess.run(["git", "-C", td, "rev-parse", "HEAD"],
                             check=True, capture_output=True,
                             text=True).stdout.strip()
        files = subprocess.run(
            ["git", "-C", td, "ls-tree", "--name-only",
             f"HEAD:{NOTO_SVG_DIR}"],
            check=True, capture_output=True, text=True).stdout.split()
    noto_files = {f for f in files if f.endswith(".svg")}
    if not noto_files:
        sys.exit(f"ERROR: no SVGs under {NOTO_SVG_DIR} — "
                 "did upstream move the folder again?")
    print(f"  upstream commit: {sha}  ({len(noto_files)} svg files)")
    raw_base = ("https://raw.githubusercontent.com/googlefonts/noto-emoji/"
                f"{sha}/{NOTO_SVG_DIR}/")

    cat_to_coll = {c: k for k, cats in COLLECTIONS.items() for c in cats}
    jobs = []  # (url, dest_path)
    counts = {}
    used_by_cat = {}
    for e in gemoji:
        cat = e.get("category")
        coll = cat_to_coll.get(cat)
        if not coll:
            continue
        em = e["emoji"]
        if any(ord(c) in SKIN for c in em):
            continue
        code = noto_code(em)
        if f"emoji_u{code}.svg" not in noto_files:
            code = noto_code(em, keep_fe0f=True)
            if f"emoji_u{code}.svg" not in noto_files:
                continue
        slug = slugify(e["description"], used_by_cat.setdefault(cat, set()))
        dest = (ROOT / "collections" / coll / "svg"
                / cat.replace(" & ", " and ") / f"{slug}.svg")
        jobs.append((raw_base + f"emoji_u{code}.svg", dest))
        counts[cat] = counts.get(cat, 0) + 1

    # clean rebuild so removed/renamed upstream emoji don't linger
    for coll in COLLECTIONS:
        shutil.rmtree(ROOT / "collections" / coll / "svg",
                      ignore_errors=True)
    for _, dest in jobs:
        dest.parent.mkdir(parents=True, exist_ok=True)

    def fetch(job):
        url, dest = job
        try:
            dest.write_bytes(
                urllib.request.urlopen(url, timeout=30).read())
            return None
        except Exception as ex:
            return f"{url} -> {ex}"

    print(f"downloading {len(jobs)} svgs ...")
    fails = []
    with concurrent.futures.ThreadPoolExecutor(THREADS) as pool:
        for i, err in enumerate(pool.map(fetch, jobs), 1):
            if err:
                fails.append(err)
            if i % 300 == 0:
                print(f"  ... {i} / {len(jobs)}")

    lic = urllib.request.urlopen(
        "https://raw.githubusercontent.com/googlefonts/noto-emoji/"
        f"{sha}/LICENSE", timeout=30).read()
    (ROOT / "LICENSE-noto-emoji.txt").write_bytes(lic)
    (ROOT / "UPSTREAM_COMMIT.txt").write_text(sha + "\n")

    for cat, n in counts.items():
        print(f"  {cat:20s} {n}")
    print(f"  total {len(jobs)}, failed {len(fails)}")
    for f in fails[:10]:
        print("  NG", f)
    if fails:
        sys.exit("ERROR: some downloads failed — rerun.")

    import make_index  # same folder; rebuilds index.csv for this commit
    make_index.main()
    print("\nDone. Review `git status`, commit, tag, and update the tag "
          "in install.py and README.md.")


if __name__ == "__main__":
    main()
