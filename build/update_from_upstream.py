#!/usr/bin/env python3
"""Maintainer tool: fetch the emoji from upstream and rebuild the payload.

Run it about once a year, after Noto Emoji has added the new Unicode emoji.
It needs git, network access and picosvg (python3 -m pip install picosvg),
not QGIS.

    python3 build/update_from_upstream.py             noto-emoji main
    python3 build/update_from_upstream.py <commit>    that commit
    python3 build/update_from_upstream.py --unicode-version 17.0.0 <commit>

The pinned Unicode emoji-test.txt supplies the emoji groups and English
names. The corresponding Noto SVGs are downloaded and rewritten where
needed for Qt. Skin-tone variants and regional flags are excluded.

Previously published paths and collections stay stable. If an emoji or
its artwork is absent upstream, the previous SVG is kept for existing
maps and its source commit is recorded. The script reports newly added
emoji, SVGs kept from previous builds, and Unicode emoji lacking Noto SVGs.
It verifies the Noto license and builds the S style before publishing files.

Then go on with "Maintenance" in README.md.
"""
import argparse
import concurrent.futures
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from xml.etree import ElementTree

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build"))
import make_core  # noqa: E402

UNICODE_VERSION = "18.0.0"
UNICODE_PUBLIC = "https://www.unicode.org/Public/"
NOTO_REPO = "https://github.com/googlefonts/noto-emoji.git"
NOTO_RAW = "https://raw.githubusercontent.com/googlefonts/noto-emoji/"
NOTO_SVG_DIR = "2D/svg"  # was "svg" until 2025; look here first if it fails

# Unicode emoji group -> collection. The collections are also what QGIS
# Resource Sharing offers (metadata.ini); install.py puts both in one folder.
COLLECTIONS = {
    "map": ["Animals & Nature", "Food & Drink", "Travel & Places",
            "Activities", "Objects", "Symbols"],
    "people": ["Smileys & Emotion", "People & Body", "Flags"],
}
COLLECTION_OF = {group: key for key, groups in COLLECTIONS.items()
                 for group in groups}
VARIATION_SELECTOR = 0xFE0F
SKIN_TONES = range(0x1F3FB, 0x1F400)
REGIONAL_INDICATORS = range(0x1F1E6, 0x1F200)
TAG_CHARACTERS = range(0xE0020, 0xE0080)
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


def emoji_key(points):
    return tuple(point for point in points if point != VARIATION_SELECTOR)


def codepoint_label(points):
    return " ".join(f"U+{point:04X}" for point in points)


def allocate_path(description, folder, used):
    """Allocate a path from a short name, adding _2, _3, ... as needed."""
    name = re.sub(r"[\u2018\u2019\u201c\u201d\"']", "", description.lower())
    name = re.sub(r"[^a-z0-9]+", "_", name).strip("_") or "emoji"
    if name in WINDOWS_RESERVED:
        name += "_"
    base, n = name, 2
    path = f"{folder}/{name}.svg"
    while path.casefold() in used:
        name, n = f"{base}_{n}", n + 1
        path = f"{folder}/{name}.svg"
    used.add(path.casefold())
    return path


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


def release_number(value):
    if not re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", value):
        raise ValueError("Use a fixed Unicode version, for example 18.0.0.")
    return value + ".0" if value.count(".") == 1 else value


def unicode_url(version):
    major, minor, _ = version.split(".")
    if int(major) >= 17:  # Unicode moved the files for Emoji 17.0
        return f"{UNICODE_PUBLIC}{version}/emoji/emoji-test.txt"
    return f"{UNICODE_PUBLIC}emoji/{major}.{minor}/emoji-test.txt"


def unicode_emoji(data, version):
    """Read the fully qualified, non-regional entries of emoji-test.txt."""
    text = data.decode("utf-8")
    header = re.search(r"^# Version: (\S+)", text, flags=re.M)
    if not header or release_number(header[1]) != version:
        raise ValueError(f"Expected Unicode Emoji {version} in emoji-test.txt")
    category, subgroup = "", ""
    entries = {}
    for line in text.splitlines():
        if line.startswith("# group: "):
            category, subgroup = line[len("# group: "):], ""
        elif line.startswith("# subgroup: "):
            subgroup = line[len("# subgroup: "):]
        if category not in COLLECTION_OF or line.startswith("#"):
            continue
        record, _, comment = line.partition("#")
        codepoints, _, status = record.partition(";")
        if status.strip() != "fully-qualified":
            continue
        points = tuple(int(point, 16) for point in codepoints.split())
        if any(point in SKIN_TONES or point in REGIONAL_INDICATORS
               or point in TAG_CHARACTERS for point in points):
            continue
        if category == "Flags" and subgroup != "flag":
            continue
        label = comment.split(maxsplit=2)
        emoji = "".join(chr(point) for point in points)
        key = emoji_key(points)
        if len(label) != 3 or label[0] != emoji or not key or key in entries:
            raise ValueError(
                f"Invalid or duplicate emoji-test.txt row: {line}")
        entries[key] = (points, emoji, label[2], category)
    if not entries:
        raise ValueError("emoji-test.txt has no eligible emoji")
    return entries


def match_noto(noto):
    """Index available SVGs by their sequences, with and without VS16."""
    files = {}
    for filename in sorted(noto):
        match = re.fullmatch(r"emoji_u([0-9a-f]+(?:_[0-9a-f]+)*)\.svg",
                             filename)
        if match:
            points = tuple(int(point, 16) for point in match[1].split("_"))
            files.setdefault(emoji_key(points), {})[points] = filename
    return files


def previous_rows(root):
    rows, used = {}, set()
    for row in make_core.read_index(root):
        if not all(row.get(field) for field in make_core.INDEX_FIELDS):
            raise ValueError("index.csv has an incomplete row")
        points = tuple(map(ord, row["emoji"]))
        key = emoji_key(points)
        path = row["path"]
        if (not key or key in rows or path.casefold() in used
                or row["codepoint"] != codepoint_label(points)
                or row["collection"] not in COLLECTIONS
                or row["set"] not in ("S", "M", "L")
                or not re.fullmatch(
                    r"[A-Za-z0-9 _&-]+/[A-Za-z0-9_-]+\.svg", path)):
            raise ValueError(f"Invalid or duplicate index.csv row for {path}")
        rows[key] = row
        used.add(path.casefold())
    return rows, used


def reserve_existing_paths(root, used):
    """Keep paths occupied by extra files out of the new assignments."""
    for collection in COLLECTIONS:
        folder = root / "collections" / f"noto_emoji_{collection}" / "svg"
        if folder.is_dir() and folder.resolve() == folder:
            for category in folder.iterdir():
                if category.is_dir() and not category.is_symlink():
                    used.update(f"{category.name}/{path.name}".casefold()
                                for path in category.iterdir())


def plan_rows(entries, noto, previous, used):
    files = match_noto(noto)
    updated, added, missing = {}, [], []
    for key, (points, emoji, name, category) in entries.items():
        prior = previous.get(key)
        candidates = files.get(key)
        if not candidates:
            if prior is None:
                missing.append(f"{codepoint_label(points)} {name}")
            continue
        source = candidates.get(key) or candidates.get(points)
        if source is None:
            if len(candidates) != 1:
                raise ValueError(
                    f"Ambiguous Noto SVGs for {codepoint_label(points)}")
            source = next(iter(candidates.values()))
        if prior:
            # The old spelling and variation selectors also enter style
            # symbol names. Keep those and the category/collection stable.
            updated[key] = {**prior, "name": name, "noto_file": source}
        else:
            folder = category.replace(" & ", " and ")
            added.append({
                "emoji": emoji,
                "codepoint": codepoint_label(points),
                "name": name,
                "category": category,
                "collection": COLLECTION_OF[category],
                "path": allocate_path(name, folder, used),
                "noto_file": source,
                "set": "",  # make_core fills it in
            })
    rows = [updated.get(key, prior) for key, prior in previous.items()] + added
    retained = [prior for key, prior in previous.items() if key not in updated]
    return rows, list(updated.values()) + added, added, retained, missing


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
        try:
            from picosvg.svg import SVG
        except ImportError as error:
            raise RuntimeError(
                "picosvg is missing. Run python3 -m pip install picosvg."
            ) from error
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


def provenance(root, sha, url, retained):
    current = (root / "UPSTREAM_COMMIT.txt").read_text(
        encoding="utf-8").splitlines()
    previous_sha = current[0]
    earlier = {}
    for line in current[1:]:
        match = re.fullmatch(r"Retained SVG ([0-9a-f]+): (.+)", line)
        if match:
            earlier[match[2]] = match[1]
    lines = [sha, f"Unicode emoji-test data: {url}"]
    for row in retained:
        path = row["path"]
        lines.append(f"Retained SVG {earlier.get(path, previous_sha)}: {path}")
    return "\n".join(lines) + "\n"


def stage_update(root, staging, commit, version):
    previous, used = previous_rows(root)
    reserve_existing_paths(root, used)
    url = unicode_url(version)
    print(f"reading Unicode Emoji {version} ...")
    entries = unicode_emoji(fetch(url), version)
    print("listing the SVG files of noto-emoji ...")
    sha, noto = upstream_files(commit)
    if not noto:
        raise ValueError(f"No SVG files under {NOTO_SVG_DIR}. "
                         "Did upstream move the folder again?")
    print(f"  commit {sha}, {len(noto)} SVG files")
    rows, downloads, added, retained, missing = plan_rows(
        entries, noto, previous, used)
    if not downloads:
        raise ValueError("No Unicode emoji match the Noto SVGs")

    base = f"{NOTO_RAW}{sha}/"
    # Upstream's root license is for the font. The license for the SVG
    # assets is in their directory and the local copy is maintained by hand.
    notice = fetch(f"{base}{NOTO_SVG_DIR}/LICENSE").strip()
    local_license = (root / "LICENSE-noto-emoji.txt").read_bytes()
    if not notice or not local_license.startswith(notice):
        raise ValueError(
            f"Upstream's license notice ({NOTO_SVG_DIR}/LICENSE) no longer "
            "matches the top of LICENSE-noto-emoji.txt. Read the new notice "
            "and update the licensing documentation first.")

    def get(row):
        name = row["noto_file"]
        try:
            return fetch(f"{base}{NOTO_SVG_DIR}/{name}")
        except OSError as error:
            raise RuntimeError(
                f"Could not download {name}: {error}") from error

    print(f"downloading {len(downloads)} SVG files ...")
    with concurrent.futures.ThreadPoolExecutor(THREADS) as pool:
        blobs = list(pool.map(get, downloads))

    print("rewriting the files Qt would draw wrong ...")
    rewritten, doubtful = 0, []
    for row, original in zip(downloads, blobs):
        changed = for_qt(original, row["noto_file"])
        rewritten += changed is not None
        blob = original if changed is None else changed
        try:
            tag = ElementTree.fromstring(blob).tag
        except ElementTree.ParseError as error:
            raise ValueError(
                f"Invalid SVG: {row['noto_file']}: {error}") from error
        if tag not in ("svg", "{http://www.w3.org/2000/svg}svg"):
            raise ValueError(f"Invalid SVG root: {row['noto_file']}")
        if QT_DOUBTFUL.search(blob.decode("utf-8")):
            doubtful.append(row["path"])
        dest = staging / make_core.svg_path(row)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
    print(f"  {rewritten} of {len(downloads)}")
    for row in retained:
        path = make_core.svg_path(row)
        source = root / path
        if source.resolve() != source or not source.is_file():
            raise ValueError(
                f"Previously published SVG is unavailable: {path}")
        dest = staging / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)

    upstream_commit = pathlib.Path("UPSTREAM_COMMIT.txt")
    (staging / upstream_commit).write_text(
        provenance(root, sha, url, retained), encoding="utf-8")
    shutil.copyfile(root / "core_list.txt", staging / "core_list.txt")
    make_core.build_core(staging, staging, rows)
    paths = [make_core.svg_path(row) for row in downloads]
    paths += [upstream_commit, *make_core.OUTPUTS]
    make_core.publish(root, staging, paths)

    for label, paths in (("new", [row["path"] for row in added]),
                         ("retained from previous builds",
                          [row["path"] for row in retained]),
                         ("Unicode entries without a Noto SVG", missing)):
        print(f"{label}: {len(paths)}")
        for path in sorted(paths):
            print(f"  {path}")
    if doubtful:
        print(f"WARNING: {len(doubtful)} files use something Qt may draw "
              "wrong. Look at them in QGIS, and extend for_qt if they are "
              "broken:")
        for path in doubtful:
            print(f"  {path}")


def main(commit=None, version=UNICODE_VERSION):
    version = release_number(version)
    with make_core.build_workspace(ROOT) as staging:
        stage_update(ROOT, staging, commit, version)
    print("Done. Look at `git status`, then go on with \"Maintenance\" in "
          "README.md.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("commit", nargs="?", help="Noto Emoji commit or tag")
    parser.add_argument("--unicode-version", default=UNICODE_VERSION,
                        help="fixed Unicode release (default: %(default)s)")
    options = parser.parse_args()
    try:
        main(options.commit, options.unicode_version)
    except (OSError, RuntimeError, ValueError,
            subprocess.CalledProcessError) as error:
        sys.exit(f"ERROR: {error}")
