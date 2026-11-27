#!/usr/bin/env python3
"""Maintainer tool: build everything that depends on the S set.

    python3 build/make_core.py

Reads core_list.txt (the S set, edited by hand), l_only_list.txt (what
the M set leaves out, edited by hand) and index.csv, and writes:

  index.csv                    the "set" column: S for the emoji in
                               core_list.txt; M for the rest of the map
                               collection, except l_only_list.txt, and for
                               the faces (Smileys & Emotion); L for the
                               others: people, hands and flags
  styles/emoji_san_core.xml    the S set as QGIS symbols with the SVG
                               inside, for the Style Manager. This is the
                               file attached to a release.
  review_core.html             the S set on one page, for looking it over
                               (not committed)

Run it after editing core_list.txt. update_from_upstream.py runs it as its
last step.

Taking an emoji out of core_list.txt takes it away from everyone who has
the S set, the next time they run the installer. Maps that use it then show
"?". Adding is always safe.
"""
import base64
import contextlib
import csv
import html
import os
import pathlib
import shutil
import sys
import tempfile
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIZE_MM = "5"
INDEX_FIELDS = ["emoji", "codepoint", "name", "category", "collection",
                "path", "noto_file", "set"]
OUTPUTS = (pathlib.Path("index.csv"),
           pathlib.Path("styles/emoji_san_core.xml"),
           pathlib.Path("review_core.html"))


L_ONLY_LIST = "l_only_list.txt"
M_CATEGORIES = ("Smileys & Emotion",)  # outside the map collection


def read_l_only(root):
    """Paths in l_only_list.txt: map-collection emoji kept out of M."""
    listing = root / L_ONLY_LIST
    if not listing.is_file():
        return set()
    paths = set()
    for line in listing.read_text(encoding="utf-8").splitlines():
        entry = line.partition("#")[0].strip()
        if entry:
            paths.add(entry + ".svg")
    return paths


def read_core(root):
    """[(path, note), ...] from core_list.txt, in the order of the file."""
    entries = []
    text = (root / "core_list.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        entry, _, note = line.partition("#")
        if entry.strip():
            entries.append((entry.strip() + ".svg", note.strip()))
    return entries


def read_index(root):
    with (root / "index.csv").open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != INDEX_FIELDS:
            raise ValueError("index.csv has unexpected columns")
        return list(reader)


def write_index(root, rows):
    with (root / "index.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def svg_path(row):
    return (pathlib.Path("collections") / f"noto_emoji_{row['collection']}"
            / "svg" / row["path"])


@contextlib.contextmanager
def build_workspace(root):
    """Keep both maintainer commands from publishing at the same time."""
    lock = root / ".emoji-san-build.lock"
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise RuntimeError(
            f"Another build holds {lock}. If it was interrupted, "
            "check the repository before removing the lock."
        ) from error
    try:
        with tempfile.TemporaryDirectory(prefix=".emoji-san-build-",
                                         dir=root) as directory:
            yield pathlib.Path(directory)
    finally:
        lock.rmdir()


def publish(root, staging, paths):
    """Replace changed build files and restore them if a replacement fails."""
    replacements = []
    for path in paths:
        source, target = staging / path, root / path
        if not source.is_file():
            raise ValueError(f"Missing staged build output: {path}")
        if target.resolve() != target or (
                target.exists() and not target.is_file()):
            raise ValueError(f"Cannot replace build output: {target}")
        if not target.is_file() or source.read_bytes() != target.read_bytes():
            replacements.append(path)

    if not replacements:
        return
    backups = pathlib.Path(tempfile.mkdtemp(prefix=".emoji-san-backup-",
                                           dir=root))
    attempted, created = [], []
    try:
        for path in replacements:
            target, backup = root / path, backups / path
            if target.is_file():
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
        for path in replacements:
            target = root / path
            missing = []
            parent = target.parent
            while not parent.exists():
                missing.append(parent)
                parent = parent.parent
            for parent in reversed(missing):
                parent.mkdir()
                created.append(parent)
            attempted.append(path)
            os.replace(staging / path, target)
    except BaseException as error:
        rollback_errors = []
        for path in reversed(attempted):
            if (staging / path).exists():
                continue  # this replacement did not happen
            target, backup = root / path, backups / path
            try:
                if backup.is_file():
                    os.replace(backup, target)
                else:
                    target.unlink()
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        for parent in reversed(created):
            try:
                parent.rmdir()
            except OSError as rollback_error:
                rollback_errors.append(str(rollback_error))
        if rollback_errors:
            raise RuntimeError(
                f"Build failed and could not be fully restored. "
                f"Backups remain in {backups}: {'; '.join(rollback_errors)}"
            ) from error
        shutil.rmtree(backups)
        raise
    else:
        shutil.rmtree(backups)


def attr(value):
    return escape(value, {'"': "&quot;"})


def symbol_xml(name, tags, b64):
    # <prop> is the form every QGIS 3 and 4 reads; QGIS itself writes
    # <Option> since 3.18, which 3.16 and older cannot read.
    props = [("name", "base64:" + b64), ("size", SIZE_MM),
             ("size_unit", "MM"), ("angle", "0"), ("offset", "0,0"),
             ("offset_unit", "MM"), ("scale_method", "diameter"),
             ("vertical_anchor_point", "1"),
             ("horizontal_anchor_point", "1")]
    ps = "".join(f'\n      <prop k="{k}" v="{attr(v)}"/>' for k, v in props)
    return (f'  <symbol alpha="1" clip_to_extent="1" type="marker" '
            f'name="{attr(name)}" tags="{attr(tags)}" favorite="0">\n'
            f'    <layer pass="0" class="SvgMarker" locked="0" enabled="1">'
            f'{ps}\n    </layer>\n  </symbol>')


REVIEW_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EmOji-san S set</title><style>
:root{color-scheme:light}body{font-family:'Noto Sans CJK JP','Hiragino Sans',
'Yu Gothic',sans-serif;background:#fcfbf7;margin:24px;color:#2b2b2b}
h1{font-size:22px}h2{font-size:17px;margin:26px 0 8px;color:#9a4a00}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
gap:8px}.card{background:#fff;border:1.5px solid #e0d8c8;border-radius:10px;
padding:8px;cursor:pointer;text-align:center;user-select:none}
.card img{width:44px;height:44px}.nm{font-size:12px;font-weight:600;
word-break:break-all}.rs{font-size:10.5px;color:#8a7a5c;margin-top:2px}
.card.off{opacity:.32;filter:grayscale(1);border-style:dashed}
#bar{position:sticky;top:0;background:#fcfbf7ee;padding:10px 0;z-index:9}
#total{font-weight:700;color:#1f6b33}textarea{width:100%;height:160px;
font:12px/1.5 monospace;margin-top:10px}.cnt{color:#999;font-size:13px;
font-weight:400}</style></head><body>
<div id="bar"><h1>EmOji-san S set</h1>
<div>In the set: <span id="total"></span>. Click an emoji to take it out or
put it back, then replace the lines of core_list.txt with the list at the
bottom and run build/make_core.py again.</div></div>
__SECTIONS__
<h2>Lines for core_list.txt</h2><textarea id="out" readonly></textarea>
<script>
function upd(){const on=[...document.querySelectorAll('.card:not(.off)')];
document.getElementById('total').textContent=on.length;
document.querySelectorAll('.cnt').forEach(e=>{const c=e.dataset.cat;
e.textContent='('+document.querySelectorAll(
'.card[data-cat="'+c+'"]:not(.off)').length+')';});
document.getElementById('out').value=on.map(e=>e.dataset.line).join('\\n');}
function tg(el){el.classList.toggle('off');upd()}upd();
</script></body></html>"""


def build_core(source, output, rows):
    """Build the CSV, style XML and review page in an isolated directory."""
    by_path = {r["path"]: r for r in rows}
    if len(by_path) != len(rows):
        raise ValueError("index.csv contains duplicate SVG paths")
    core = read_core(source)
    paths = [p for p, _ in core]
    if not paths:
        raise ValueError("core_list.txt must contain at least one emoji")
    unknown = [p for p in paths if p not in by_path]
    if unknown:
        raise ValueError(
            f"core_list.txt names emoji that index.csv does not have: "
            f"{unknown}. Correct core_list.txt and run build/make_core.py."
        )
    twice = sorted({p for p in paths if paths.count(p) > 1})
    if twice:
        raise ValueError(f"Listed twice in core_list.txt: {twice}")
    missing = [r["path"] for r in rows if not (source / svg_path(r)).is_file()]
    if missing:
        raise ValueError(
            f"{len(missing)} SVG files named in index.csv are missing, "
            f"e.g. {missing[:3]}. Run build/update_from_upstream.py."
        )

    l_only = read_l_only(source)
    unknown = sorted(l_only - set(by_path))
    if unknown:
        raise ValueError(f"{L_ONLY_LIST} names emoji that index.csv does not "
                         f"have: {unknown}")

    # 1) index.csv: which set each emoji belongs to
    in_core = set(paths)
    for r in rows:
        in_m = ((r["collection"] == "map" and r["path"] not in l_only)
                or r["category"] in M_CATEGORIES)
        r["set"] = ("S" if r["path"] in in_core else "M" if in_m else "L")
    # 2) the style file. A symbol is named "<emoji> <file name>", e.g.
    # "✈️ airplane". A bare "airplane" or "bank" could collide with a
    # user's existing symbol and prompt for an overwrite.
    commit = (source / "UPSTREAM_COMMIT.txt").read_text(
        encoding="utf-8").splitlines()[0]
    symbols = []
    encoded = {}
    for path in paths:
        row = by_path[path]
        folder, name = path[:-len(".svg")].split("/")
        b64 = base64.b64encode((source / svg_path(row)).read_bytes()).decode()
        encoded[path] = b64
        symbols.append(symbol_xml(f"{row['emoji']} {name}",
                                  f"EmOji-san,Noto Emoji,{folder}", b64))
    xml = ("<!DOCTYPE qgis_style>\n"
           "<!-- EmOji-san S set: https://github.com/yfuru2454/emoji-san\n"
           "     Emoji artwork: Google Noto Emoji, Apache License 2.0,\n"
           "     https://github.com/googlefonts/noto-emoji (commit "
           f"{commit[:12]}).\n"
           "     The SVG files are embedded as the repository has them; its\n"
           "     NOTICE says which of Noto's files were changed, and how. "
           "-->\n"
           '<qgis_style version="2">\n<symbols>\n'
           + "\n".join(symbols)
           + "\n</symbols>\n<colorramps/>\n</qgis_style>\n")
    out = output / OUTPUTS[1]
    out.parent.mkdir(exist_ok=True)
    out.write_text(xml, encoding="utf-8")

    # 3) the review page
    sections, cards = [], {}
    width = max(len(p) for p in paths) - len(".svg") + 2
    for path, note in core:
        folder, name = path[:-len(".svg")].split("/")
        b64 = encoded[path]
        line = f"{folder}/{name}".ljust(width) + f"# {note}"
        if folder not in cards:
            sections.append(folder)
        cards.setdefault(folder, []).append(
            f'<div class="card" data-line="{html.escape(line)}" '
            f'data-cat="{html.escape(folder)}" onclick="tg(this)">'
            f'<img src="data:image/svg+xml;base64,{b64}">'
            f'<div class="nm">{html.escape(name)}</div>'
            f'<div class="rs">{html.escape(note)}</div></div>')
    page = REVIEW_PAGE.replace("__SECTIONS__", "".join(
        f'<h2>{html.escape(s)} <span class="cnt" data-cat="{html.escape(s)}">'
        f'</span></h2><div class="grid">{"".join(cards[s])}</div>'
        for s in sections))
    (output / OUTPUTS[2]).write_text(page, encoding="utf-8")
    write_index(output, rows)

    counts = {s: sum(r["set"] == s for r in rows) for s in "SML"}
    print(f"sets: S {counts['S']}, M {counts['S'] + counts['M']}, "
          f"L {len(rows)}")


def main():
    with build_workspace(ROOT) as staging:
        build_core(ROOT, staging, read_index(ROOT))
        publish(ROOT, staging, OUTPUTS)
    print("wrote index.csv, styles/emoji_san_core.xml, review_core.html")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, ValueError) as error:
        sys.exit(f"ERROR: {error}")
