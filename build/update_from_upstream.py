#!/usr/bin/env python3
"""Maintainer tool: fetch the emoji from upstream and rebuild the payload.

Run it about once a year, after Noto Emoji has added the new Unicode emoji.
It needs git, network access and picosvg (python3 -m pip install picosvg),
not QGIS.

    python3 build/update_from_upstream.py             noto-emoji main
    python3 build/update_from_upstream.py <commit>    that commit

What it does:
  1. reads gemoji's emoji.json: every emoji with its category and English
     name
  2. lists the SVG files of googlefonts/noto-emoji at the commit
  3. downloads each emoji both of them have, skin-tone variants left out,
     to collections/noto_emoji_{map,people}/svg/<Category>/<name>.svg, and
     rewrites the files that Qt would draw wrong (see for_qt below)
  4. rewrites UPSTREAM_COMMIT.txt and index.csv, and checks that upstream
     still puts the SVG files under the license in LICENSE-noto-emoji.txt
  5. runs make_core.py, which fills in the sets and builds the style file

It prints the emoji that are new and those that are gone since the last
run. A file that is gone (renamed or dropped upstream) disappears from the
users' folders at their next install, and maps that use it show "?". Say so
in the release notes.

Then go on with "Maintenance" in README.md.
"""
import concurrent.futures
import csv
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

try:
    from picosvg.svg import SVG
except ImportError:
    sys.exit("ERROR: picosvg is missing. python3 -m pip install picosvg")

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
import make_core  # noqa: E402

GEMOJI_URL = ("https://raw.githubusercontent.com/github/gemoji/master/db/"
              "emoji.json")
NOTO_REPO = "https://github.com/googlefonts/noto-emoji.git"
NOTO_RAW = "https://raw.githubusercontent.com/googlefonts/noto-emoji/"
NOTO_SVG_DIR = "2D/svg"  # was "svg" until 2025; look here first if it fails

# gemoji category -> collection. The collections are also what QGIS
# Resource Sharing offers (metadata.ini); install.py puts both in one folder.
COLLECTIONS = {
    "map": ["Animals & Nature", "Food & Drink", "Travel & Places",
            "Activities", "Objects", "Symbols"],
    # Country flags are not in 2D/svg (upstream keeps them in third_party/,
    # under other terms), so "Flags" only brings the 8 that are not a
    # country's.
    "people": ["Smileys & Emotion", "People & Body", "Flags"],
}
SKIN_TONES = set(range(0x1F3FB, 0x1F400))
WINDOWS_RESERVED = {"con", "prn", "aux", "nul",
                    *(f"com{i}" for i in range(1, 10)),
                    *(f"lpt{i}" for i in range(1, 10))}
THREADS = 16

# QGIS draws SVG markers with Qt's SVG renderer. That renderer has no clip
# paths, does not follow xlink:href from one gradient to another and cannot
# read rgba() colors. Noto's hands, for one, are a shape plus shading that
# is clipped to the shape: Qt draws them as black hands with the shading
# sticking out. Files with these constructs are rewritten; all the others
# are kept byte for byte.
QT_CANNOT = re.compile(r"<clipPath|Gradient[^>]*xlink:href")
RGBA_STOP = re.compile(
    r'stop-color="rgba\(\s*(\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\s*\)"'
    r' stop-opacity="([0-9.]+)"')
# What Qt has trouble with. A file that still has one of these after the
# rewrite is reported, for a look at how QGIS draws it. Not on the list:
# mix-blend-mode, which Qt ignores. Three faces shade a cheek or a tongue
# with it and come out a little lighter in QGIS than in a browser.
QT_DOUBTFUL = re.compile(
    r"<clipPath|clip-path|Gradient[^>]*xlink:href|rgba\(|<mask|<filter"
    r"|<pattern|<style|<use|<image|<text|<symbol|<switch|<foreignObject")


def noto_name(emoji, keep_fe0f=False):
    """Noto's file name for an emoji, e.g. emoji_u1f3ea.svg."""
    return "emoji_u" + "_".join(
        f"{ord(c):x}" for c in emoji
        if keep_fe0f or ord(c) != 0xFE0F) + ".svg"


def file_name(description, used):
    """"hot beverage" -> "hot_beverage"; a repeated name gets _2, _3, ..."""
    name = re.sub(r"[\u2018\u2019\u201c\u201d\"']", "", description.lower())
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_") or "emoji"
    if name in WINDOWS_RESERVED:
        name += "_"
    base, n = name, 2
    while name in used:
        name, n = f"{base}_{n}", n + 1
    used.add(name)
    return name


def upstream_files(commit):
    """(commit hash, names of the SVG files) of noto-emoji at a commit,
    without downloading the repository's files."""
    with tempfile.TemporaryDirectory() as tmp:
        def git(*args):
            return subprocess.run(["git", "-C", tmp, *args], check=True,
                                  capture_output=True, text=True).stdout
        git("init", "-q")
        git("fetch", "-q", "--depth", "1", "--filter=blob:none", NOTO_REPO,
            commit or "HEAD")
        sha = git("rev-parse", "FETCH_HEAD").strip()
        names = git("ls-tree", "--name-only",
                    f"FETCH_HEAD:{NOTO_SVG_DIR}").split()
    return sha, {n for n in names if n.endswith(".svg")}


def build_rows(gemoji, noto):
    """One index.csv row for each emoji that gemoji and Noto both have."""
    collection_of = {c: k for k, cs in COLLECTIONS.items() for c in cs}
    used, rows = {}, []
    for e in gemoji:
        category = e.get("category")
        emoji = e["emoji"]
        if category not in collection_of \
                or any(ord(c) in SKIN_TONES for c in emoji):
            continue
        source = noto_name(emoji)
        if source not in noto:
            source = noto_name(emoji, keep_fe0f=True)
            if source not in noto:
                continue
        name = file_name(e["description"], used.setdefault(category, set()))
        rows.append({
            "emoji": emoji,
            "codepoint": " ".join(f"U+{ord(c):04X}" for c in emoji),
            "name": e["description"],
            "category": category,
            "collection": collection_of[category],
            "path": f"{category.replace(' & ', ' and ')}/{name}.svg",
            "noto_file": source,
            "set": "",  # make_core.py fills it in
        })
    return rows


def for_qt(svg, source):
    """The SVG rewritten so that Qt draws it the way a browser does, or
    None if it can stay as it is. `source` is Noto's file name."""
    original = text = svg.decode("utf-8")
    if not (QT_CANNOT.search(text) or "rgba(" in text):
        return None

    def stop(match):
        # rgba(r, g, b, a) next to a stop-opacity: a browser multiplies both
        red, green, blue = (int(match.group(i)) for i in (1, 2, 3))
        alpha = float(match.group(4)) * float(match.group(5))
        return 'stop-color="#%02x%02x%02x" stop-opacity="%s"' % (
            red, green, blue, ("%.4f" % alpha).rstrip("0").rstrip("."))

    text = RGBA_STOP.sub(stop, text)
    if QT_CANNOT.search(text):
        # picosvg is Google's tool for getting these SVGs ready for a font:
        # it applies the clip paths to the shapes and resolves references
        text = SVG.fromstring(text).topicosvg().tostring(pretty_print=True)
    if text == original:  # an rgba() of a kind this does not rewrite
        return None
    # Apache License 2.0, 4b: a changed file says that it was changed
    note = ("<!-- Changed by EmOji-san from Noto Emoji's %s so that Qt can "
            "draw it. See NOTICE. -->\n" % source)
    if text.startswith("<?xml"):  # the XML declaration has to stay first
        declaration, rest = text.split("?>", 1)
        text = declaration + "?>\n" + note + rest.lstrip("\n")
    else:
        text = note + text
    return text.encode("utf-8")


def fetch(url, tries=3):
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as reply:
                return reply.read()
        except Exception:
            if attempt == tries:
                raise
            time.sleep(attempt)  # 1,600 requests: one may well be dropped


def main(commit=None):
    print("reading gemoji ...")
    gemoji = json.loads(fetch(GEMOJI_URL))
    print("listing the SVG files of noto-emoji ...")
    sha, noto = upstream_files(commit)
    if not noto:
        sys.exit(f"ERROR: no SVG files under {NOTO_SVG_DIR}. Did upstream "
                 "move the folder again?")
    print(f"  commit {sha}, {len(noto)} SVG files")
    rows = build_rows(gemoji, noto)

    # Download everything before touching the repository, so that a failed
    # run leaves it as it was.
    print(f"downloading {len(rows)} SVG files ...")
    base = f"{NOTO_RAW}{sha}/"

    def get(row):
        try:
            return fetch(f"{base}{NOTO_SVG_DIR}/{row['noto_file']}")
        except Exception as ex:
            return ex

    with concurrent.futures.ThreadPoolExecutor(THREADS) as pool:
        blobs = list(pool.map(get, rows))
    failed = [(r["noto_file"], b) for r, b in zip(rows, blobs)
              if isinstance(b, Exception)]
    if failed:
        for name, ex in failed[:10]:
            print(f"  failed: {name}: {ex}")
        sys.exit(f"ERROR: {len(failed)} downloads failed. Nothing was "
                 "changed; run it again.")
    # The license file is kept by hand. Upstream's root LICENSE is the font
    # license (OFL); the one that covers the images sits in their folder.
    notice = fetch(f"{base}{NOTO_SVG_DIR}/LICENSE").strip()
    if not (ROOT / "LICENSE-noto-emoji.txt").read_bytes().startswith(notice):
        sys.exit("ERROR: upstream's license notice for the SVG files "
                 f"({NOTO_SVG_DIR}/LICENSE) is no longer the one at the top "
                 "of LICENSE-noto-emoji.txt. Nothing was changed. Read the "
                 "new notice, then bring LICENSE-noto-emoji.txt, NOTICE, "
                 "metadata.ini and README.md in line with it.")

    print("rewriting the files Qt would draw wrong ...")
    rewritten = 0
    for i, row in enumerate(rows):
        changed = for_qt(blobs[i], row["noto_file"])
        if changed:
            blobs[i] = changed
            rewritten += 1
    print(f"  {rewritten} of {len(rows)}")
    doubtful = [r["path"] for r, b in zip(rows, blobs)
                if QT_DOUBTFUL.search(b.decode("utf-8"))]

    try:
        with open(ROOT / "index.csv", encoding="utf-8", newline="") as f:
            before = {r["path"] for r in csv.DictReader(f)}
    except OSError:
        before = set()

    for collection in COLLECTIONS:
        shutil.rmtree(ROOT / "collections" / f"noto_emoji_{collection}"
                      / "svg", ignore_errors=True)
    for row, blob in zip(rows, blobs):
        dest = make_core.svg_file(row)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
    (ROOT / "UPSTREAM_COMMIT.txt").write_text(sha + "\n")
    make_core.write_index(rows)

    now = {r["path"] for r in rows}
    for label, paths in (("new", now - before), ("gone", before - now)):
        print(f"{label}: {len(paths)}")
        for path in sorted(paths):
            print(f"  {path}")
    make_core.main()
    if doubtful:
        print(f"WARNING: {len(doubtful)} files use something Qt may draw "
              "wrong. Look at them in QGIS, and extend for_qt if they are "
              "broken:")
        for path in doubtful:
            print(f"  {path}")
    print("Done. Look at `git status`, then go on with \"Maintenance\" in "
          "README.md.")


if __name__ == "__main__":
    main(*sys.argv[1:2])
