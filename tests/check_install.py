# -*- coding: utf-8 -*-
"""EmOji-san install check — run in the QGIS Python console after install.

    import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())

or, from a local clone:

    exec(open('/path/to/emoji-san/tests/check_install.py', 'rb').read())

Checks, each printed as PASS / FAIL / SKIP:
  1. the EmOji-san folder exists with its category folders and SVGs
  2. it is registered as an SVG path and QGIS lists it
  3. index.csv is present, every row points at a real file, and it has a
     name column in this QGIS's language (unless English)
  4. QGIS resolves a relative SVG path the way projects store it
  5. QGIS actually RENDERS an emoji SVG marker (not the "?" shown for a
     missing SVG)
  6. (if imported) the core style symbols are in the style library and
     every one renders from its embedded SVG
Then, with DEMO = True (the default), adds a small "EmOji-san demo" layer
around the map centre so you can see the markers on your map.

Set DEMO = False first to skip the demo layer:
    DEMO = False; exec(...)
"""
import csv
import os

from qgis.core import (QgsApplication, QgsCategorizedSymbolRenderer,
                       QgsFeature, QgsField, QgsGeometry, QgsMarkerSymbol,
                       QgsPointXY, QgsProject, QgsRendererCategory,
                       QgsSettings, QgsStyle, QgsSvgMarkerSymbolLayer,
                       QgsSymbolLayerUtils, QgsVectorLayer)
from qgis.PyQt.QtCore import QSize
try:  # QGIS 3.x (Qt5)
    from qgis.PyQt.QtCore import QVariant
    STRING = QVariant.String
except (ImportError, AttributeError):  # QGIS 4 (Qt6)
    from qgis.PyQt.QtCore import QMetaType
    STRING = QMetaType.Type.QString

DEMO = bool(globals().get("DEMO", True))
SAMPLE = "Travel and Places/convenience_store.svg"

results = []


def report(ok, label, detail=""):
    tag = {True: "PASS", False: "FAIL", None: "SKIP"}[ok]
    results.append(ok)
    print("  [%s] %s%s" % (tag, label, ("  — " + detail) if detail else ""))


def _image(symbol):
    s = symbol.clone()
    s.setSize(12)  # same size for every check
    return s.asImage(QSize(64, 64))


def _svg_symbol(path):
    s = QgsMarkerSymbol()
    s.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(path, 12))
    return s


# What QGIS draws when an SVG cannot be found or read (a "?" mark).
# A symbol rendered OK = its image differs from this placeholder.
PLACEHOLDER = _image(_svg_symbol("/nonexistent/emoji-san-check.svg"))


def _visible(img):
    for y in range(0, img.height(), 2):
        for x in range(0, img.width(), 2):
            if img.pixelColor(x, y).alpha() > 128:
                return True
    return False


def renders(symbol):
    """Drawn, and not the placeholder (missing file) or blank (bad SVG)."""
    img = _image(symbol)
    return not img.isNull() and img != PLACEHOLDER and _visible(img)


print("EmOji-san install check")
profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
root = os.path.join(os.path.dirname(os.path.dirname(profile)), "EmOji-san")

# 1. folder, categories, files -------------------------------------------
idx = os.path.join(root, "index.csv")
rows, cols = [], []
if os.path.isfile(idx):
    with open(idx, encoding="utf-8") as f:
        rd = csv.DictReader(f)
        rows = list(rd)
        cols = rd.fieldnames or []
sets = sorted({r.get("set", "") for r in rows},
              key=lambda x: ["basic", "advanced", "full"].index(x)
              if x in ("basic", "advanced", "full") else 9)
installed = sets[-1] if sets else "?"
if os.path.isdir(root):
    want_cats = sorted({r["path"].split("/")[0] for r in rows})
    cats = [c for c in want_cats if os.path.isdir(os.path.join(root, c))]
    svgs = sum(len([f for f in fs if f.endswith(".svg")])
               for _, _, fs in os.walk(root))
    report(bool(rows) and len(cats) == len(want_cats) and svgs == len(rows),
           "folder: set '%s', %d SVGs in %d categories" % (
               installed, svgs, len(cats)),
           root if svgs == len(rows) else
           "index.csv lists %d -> run install.py again" % len(rows))
else:
    svgs = 0
    report(False, "folder exists", "not found: " + root)

legacy = os.path.join(profile, "svg", "EmOji-san")
report(not os.path.isdir(legacy), "no leftover from the old svg/ location",
       "" if not os.path.isdir(legacy) else "delete " + legacy)

# 2. registered as an SVG path -------------------------------------------
norm = os.path.normpath
setting = QgsSettings().value("svg/searchPathsForSVG", [])
if isinstance(setting, str):
    setting = [setting] if setting else []
in_settings = any(norm(p) == norm(root) for p in (setting or []) if p)
in_qgis = any(norm(p) == norm(root) for p in QgsApplication.svgPaths())
report(in_settings and in_qgis, "registered as an SVG path",
       "settings=%s, QgsApplication.svgPaths()=%s%s" % (
           in_settings, in_qgis,
           "" if in_settings and in_qgis else
           " -> run install.py again to re-register (or add the folder "
           "under Settings > Options > System > SVG paths)"))

# 3. index.csv -----------------------------------------------------------
if rows:
    bad = [r["path"] for r in rows
           if not os.path.isfile(os.path.join(root, *r["path"].split("/")))]
    report(not bad and len(rows) >= 200,
           "index.csv: %d rows, all paths exist" % len(rows),
           ("missing e.g. %s" % bad[:3]) if bad else "")
    local = [c for c in cols if c.startswith("name_")]
    lang = (QgsApplication.locale() or "en")[:2]
    if lang == "en":
        report(None, "local-language names", "QGIS is in English")
    else:
        filled = sum(1 for r in rows if local and r.get(local[0]))
        report(bool(local) and filled > 0.9 * len(rows),
               "local-language names: %s" % (local[0] if local else "none"),
               "%d/%d filled, e.g. %s = %s" % (
                   filled, len(rows), rows[0]["emoji"],
                   rows[0].get(local[0], "") if local else "-"))
else:
    report(False, "index.csv present", "not found: " + idx)

# 4. relative path resolves like in a saved project ----------------------
resolved = QgsSymbolLayerUtils.svgSymbolNameToPath(
    SAMPLE, QgsProject.instance().pathResolver())
report(norm(resolved) == norm(os.path.join(root, *SAMPLE.split("/"))),
       "relative path resolves: " + SAMPLE, resolved)

# 5. QGIS renders an SVG marker in colour --------------------------------
report(renders(_svg_symbol(os.path.join(root, *SAMPLE.split("/")))),
       "QGIS renders an SVG marker from the folder", SAMPLE)

# 6. core style symbols (only if imported) -------------------------------
style = QgsStyle.defaultStyle()
tag_id = style.tagId("EmOji-san")
SYMBOL = getattr(QgsStyle, "SymbolEntity", None) or \
    QgsStyle.StyleEntity.SymbolEntity
names = (style.symbolsWithTag(SYMBOL, tag_id)
         if tag_id > 0 else [])
if not names:
    report(None, "core style symbols",
           "not imported (Style Manager > Import > emoji_san_core.xml)")
else:
    plain = [s for s in names if s.isascii()]
    broken = [s for s in names if not renders(style.symbol(s))]
    report(len(names) >= 200 and not plain,
           "core style: %d symbols tagged EmOji-san" % len(names),
           ("old names without emoji, delete them: %s" % plain[:3])
           if plain else "e.g. %s" % names[0])
    report(not broken, "core style: every symbol renders (embedded SVG)",
           ("%d broken, e.g. %s" % (len(broken), broken[:3])) if broken
           else "%d/%d" % (len(names), len(names)))

# demo layer ---------------------------------------------------------------
if DEMO and svgs:
    from qgis.utils import iface
    demo = [("☕", "Food and Drink/hot_beverage.svg"),
            ("🏪", "Travel and Places/convenience_store.svg"),
            ("🏥", "Travel and Places/hospital.svg"),
            ("♨️", "Travel and Places/hot_springs.svg"),
            ("🚌", "Travel and Places/bus.svg"),
            ("🌸", "Animals and Nature/cherry_blossom.svg"),
            ("⚠️", "Symbols/warning.svg"),
            ("⚽", "Activities/soccer_ball.svg")]
    crs = QgsProject.instance().crs()
    lyr = QgsVectorLayer("Point?crs=" + crs.authid(), "EmOji-san demo",
                         "memory")
    lyr.dataProvider().addAttributes([QgsField("emoji", STRING)])
    lyr.updateFields()
    if iface and iface.mapCanvas().extent().width() > 0:
        ext = iface.mapCanvas().extent()
        c, r = ext.center(), min(ext.width(), ext.height()) * 0.3
    else:
        c, r = QgsPointXY(0, 0), 1.0
    import math
    feats = []
    for i, (e, _) in enumerate(demo):
        a = 2 * math.pi * i / len(demo)
        f = QgsFeature(lyr.fields())
        f.setGeometry(QgsGeometry.fromPointXY(
            QgsPointXY(c.x() + r * math.cos(a), c.y() + r * math.sin(a))))
        f["emoji"] = e
        feats.append(f)
    lyr.dataProvider().addFeatures(feats)
    cats = []
    for e, path in demo:
        s = QgsMarkerSymbol()
        s.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(
            os.path.join(root, *path.split("/")), 10))  # saved relative
        cats.append(QgsRendererCategory(e, s, e))
    lyr.setRenderer(QgsCategorizedSymbolRenderer("emoji", cats))
    QgsProject.instance().addMapLayer(lyr)
    if iface:
        iface.mapCanvas().refresh()
    print("  demo layer 'EmOji-san demo' added (8 emoji around the map "
          "centre; delete it when done)")

fails = results.count(False)
print("Result: %s (%d passed, %d failed, %d skipped)" % (
    "ALL GOOD" if not fails else "PROBLEMS FOUND",
    results.count(True), fails, results.count(None)))
