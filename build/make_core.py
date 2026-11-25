#!/usr/bin/env python3
"""Maintainer tool: build everything that depends on the S set.

    python3 build/make_core.py

Reads core_list.txt (the S set, edited by hand) and index.csv, and writes:

  index.csv                    the "set" column: S for the emoji in
                               core_list.txt, M for the rest of the map
                               collection, L for the others
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
import csv
import html
import pathlib
import sys
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent
SIZE_MM = "5"
INDEX_FIELDS = ["emoji", "codepoint", "name", "category", "collection",
                "path", "noto_file", "set"]


def read_core():
    """[(path, note), ...] from core_list.txt, in the order of the file."""
    entries = []
    text = (ROOT / "core_list.txt").read_text(encoding="utf-8")
    for line in text.splitlines():
        entry, _, note = line.partition("#")
        if entry.strip():
            entries.append((entry.strip() + ".svg", note.strip()))
    return entries


def write_index(rows):
    with open(ROOT / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=INDEX_FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def svg_file(row):
    return (ROOT / "collections" / f"noto_emoji_{row['collection']}" / "svg"
            / row["path"])


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


def main():
    with open(ROOT / "index.csv", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    by_path = {r["path"]: r for r in rows}
    core = read_core()
    paths = [p for p, _ in core]
    unknown = [p for p in paths if p not in by_path]
    if unknown:
        sys.exit(f"ERROR: core_list.txt names emoji that index.csv does not "
                 f"have: {unknown}. Correct core_list.txt and run "
                 "build/make_core.py again.")
    twice = sorted({p for p in paths if paths.count(p) > 1})
    if twice:
        sys.exit(f"ERROR: listed twice in core_list.txt: {twice}")
    missing = [r["path"] for r in rows if not svg_file(r).exists()]
    if missing:
        sys.exit(f"ERROR: {len(missing)} SVG files named in index.csv are "
                 f"missing, e.g. {missing[:3]}. Run update_from_upstream.py.")

    # 1) index.csv: which set each emoji belongs to
    in_core = set(paths)
    for r in rows:
        r["set"] = ("S" if r["path"] in in_core else
                    "M" if r["collection"] == "map" else "L")
    write_index(rows)

    # 2) the style file. A symbol is named "<emoji> <file name>", e.g.
    # "✈️ airplane": a bare "airplane" or "bank" could collide with a symbol
    # the user already has, and QGIS then asks whether to overwrite it.
    commit = (ROOT / "UPSTREAM_COMMIT.txt").read_text().strip()
    symbols = []
    for path in paths:
        row = by_path[path]
        folder, name = path[:-len(".svg")].split("/")
        b64 = base64.b64encode(svg_file(row).read_bytes()).decode()
        symbols.append(symbol_xml(f"{row['emoji']} {name}",
                                  f"EmOji-san,Noto Emoji,{folder}", b64))
    xml = ("<!DOCTYPE qgis_style>\n"
           "<!-- EmOji-san S set: https://github.com/yfuru2454/emoji-san\n"
           "     Emoji artwork: Google Noto Emoji, Apache License 2.0,\n"
           "     https://github.com/googlefonts/noto-emoji (commit "
           f"{commit[:12]}).\n"
           "     The SVG files are embedded as the repository has them; its\n"
           "     NOTICE says which of Noto's files were changed, and how. -->\n"
           '<qgis_style version="2">\n<symbols>\n'
           + "\n".join(symbols)
           + "\n</symbols>\n<colorramps/>\n</qgis_style>\n")
    out = ROOT / "styles" / "emoji_san_core.xml"
    out.parent.mkdir(exist_ok=True)
    out.write_text(xml, encoding="utf-8")

    # 3) the review page
    sections, cards = [], {}
    width = max(len(p) for p in paths) - len(".svg") + 2
    for path, note in core:
        folder, name = path[:-len(".svg")].split("/")
        b64 = base64.b64encode(svg_file(by_path[path]).read_bytes()).decode()
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
    (ROOT / "review_core.html").write_text(page, encoding="utf-8")

    counts = {s: sum(r["set"] == s for r in rows) for s in "SML"}
    print(f"sets: S {counts['S']}, M {counts['S'] + counts['M']}, "
          f"L {len(rows)}")
    print(f"wrote index.csv, styles/emoji_san_core.xml "
          f"({len(xml) // 1024} KB), review_core.html")


if __name__ == "__main__":
    main()
