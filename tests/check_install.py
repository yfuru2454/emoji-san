# -*- coding: utf-8 -*-
# EmOji-san: check the install.
#
# Run it from the QGIS Python console with the one-line command in
# README.md.
#
# Each check prints PASS, FAIL or SKIP, and the last line is the verdict:
#   - the EmOji-san folder holds index.csv and every file it lists
#   - the folder is one of the SVG paths
#   - index.csv has names in the language of this QGIS (not for English)
#   - a path as projects store it ("Category/name.svg") leads to the file
#   - QGIS draws an emoji, not the "?" it draws for a missing SVG
#   - symbols imported from emoji_san_core.xml all draw
#   - embedding on save, if it is switched on, really embeds
# Then it adds a layer "EmOji-san demo" with 8 emoji around the centre of
# the map. DEMO=False; in front of the command leaves that out.
#
# Nothing is changed apart from the demo layer.


def _emoji_san_check(ns):
    import builtins
    import csv
    import math
    import os

    from qgis.core import (Qgis, QgsApplication,
                           QgsCategorizedSymbolRenderer, QgsFeature,
                           QgsGeometry, QgsMarkerSymbol, QgsPointXY,
                           QgsProject, QgsReadWriteContext,
                           QgsRendererCategory, QgsSettings, QgsStyle,
                           QgsSvgMarkerSymbolLayer, QgsSymbolLayerUtils,
                           QgsVectorLayer)
    from qgis.PyQt.QtCore import QSize, QStandardPaths
    from qgis.PyQt.QtXml import QDomDocument

    FOLDER = "EmOji-san"
    BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
    demo = bool(ns.pop("DEMO", True))
    results = []

    def report(ok, label, detail=""):
        results.append(ok)
        print("  [%s] %s" % ({True: "PASS", False: "FAIL", None: "SKIP"}[ok],
                             label))
        if detail:
            print("         %s" % detail)

    def same(a, b):
        return (os.path.normcase(os.path.normpath(a))
                == os.path.normcase(os.path.normpath(b)))

    def svg_symbol(path):
        symbol = QgsMarkerSymbol()
        symbol.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(path, 12))
        return symbol

    def image(symbol):
        symbol = symbol.clone()
        symbol.setSize(12)  # every symbol at the same size
        return symbol.asImage(QSize(64, 64))

    # What QGIS draws for an SVG it cannot find. A symbol counts as drawn
    # when its image differs from this and is not empty either.
    placeholder = image(svg_symbol("/nonexistent/emoji-san-check.svg"))

    def draws(symbol):
        img = image(symbol)
        if img.isNull() or img == placeholder:
            return False
        return any(img.pixelColor(x, y).alpha() > 128
                   for y in range(0, img.height(), 2)
                   for x in range(0, img.width(), 2))

    print("EmOji-san install check (QGIS %s)" % Qgis.version())
    profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
    root = os.path.join(os.path.dirname(os.path.dirname(profile)), FOLDER)
    again = "run the install line again"

    registered = QgsSettings().value("svg/searchPathsForSVG", [])
    if isinstance(registered, str):
        registered = [registered]
    registered = [p for p in (registered or []) if p]

    # --- the folder and its index.csv -------------------------------------
    rows, columns = [], []
    try:
        with open(os.path.join(root, "index.csv"), encoding="utf-8",
                  newline="") as f:
            reader = csv.DictReader(f)
            rows = [r for r in reader if r.get("path")]
            columns = reader.fieldnames or []
    except (OSError, ValueError, csv.Error):
        pass

    def file_of(row):
        return os.path.join(root, *row["path"].split("/"))

    present = [r for r in rows if os.path.isfile(file_of(r))]
    if not os.path.isdir(root):
        other = [p for p in registered if not same(p, root)
                 and os.path.basename(os.path.normpath(p)) == FOLDER]
        report(False, "EmOji-san folder", "not found: %s%s; run the install "
               "line" % (root, " (this QGIS still uses %s)" % other[0]
                         if other else ""))
    elif not rows:
        report(False, "EmOji-san folder", "no index.csv in %s; %s" % (
            root, again))
    else:
        sets = [s for s in "SML" if any(r.get("set") == s for r in rows)]
        report(len(present) == len(rows),
               "folder: set %s, %d emoji in %d categories" % (
                   sets[-1] if sets else "?", len(rows),
                   len({r["path"].split("/")[0] for r in rows})),
               root if len(present) == len(rows) else
               "%d files are missing; %s" % (len(rows) - len(present), again))

    # --- the SVG path -----------------------------------------------------
    in_settings = any(same(p, root) for p in registered)
    in_qgis = any(same(p, root) for p in QgsApplication.svgPaths())
    if not os.path.isdir(root):
        report(None, "the folder is an SVG path", "no folder")
    else:
        report(in_settings and in_qgis, "the folder is an SVG path",
               "" if in_settings and in_qgis else
               "in the settings: %s, in use: %s; %s, or add the folder "
               "under Settings > Options > System > SVG Paths" % (
                   in_settings, in_qgis, again))

    # --- names in the language of this QGIS -------------------------------
    local = [c for c in columns if c.startswith("name_")]
    ui = str(QgsSettings().value("locale/userLocale", "")
             or QgsApplication.locale() or "en").replace("_", "-")
    if ui.split("-")[0].lower() in ("en", "c", ""):
        report(None, "names in the QGIS language", "QGIS is in English")
    elif not rows:
        report(None, "names in the QGIS language", "no index.csv")
    elif not local:
        report(None, "names in the QGIS language",
               "none in index.csv: installed with LOCALE='en', or the names "
               "could not be downloaded (%s to retry)" % again)
    else:
        filled = sum(1 for r in rows if r.get(local[0]))
        report(filled > 0.9 * len(rows),
               "names in the QGIS language: column %s" % local[0],
               "%d of %d filled, e.g. %s = %s" % (
                   filled, len(rows), rows[0]["emoji"], rows[0][local[0]]))

    # --- one emoji, the way a project uses it -----------------------------
    sample = None
    if present:
        likely = [r for r in present
                  if r["path"] == "Travel and Places/convenience_store.svg"]
        sample = (likely or present)[0]
        resolved = QgsSymbolLayerUtils.svgSymbolNameToPath(
            sample["path"], QgsProject.instance().pathResolver())
        report(same(os.path.realpath(resolved or "."),
                    os.path.realpath(file_of(sample))),
               "a project path leads to the file: %s" % sample["path"],
               resolved)
        report(draws(svg_symbol(file_of(sample))),
               "QGIS draws the SVG marker", sample["path"])
    else:
        report(None, "a project path leads to the file", "no files")
        report(None, "QGIS draws the SVG marker", "no files")

    # --- symbols imported from emoji_san_core.xml -------------------------
    style = QgsStyle.defaultStyle()
    try:  # QGIS 3
        entity = QgsStyle.SymbolEntity
    except AttributeError:  # QGIS 4
        entity = QgsStyle.StyleEntity.SymbolEntity
    tag = style.tagId(FOLDER)
    names = style.symbolsWithTag(entity, tag) if tag else []
    if not names:
        report(None, "symbols from emoji_san_core.xml", "not imported")
    else:
        broken = [n for n in names if not draws(style.symbol(n))]
        report(not broken,
               "symbols from emoji_san_core.xml: %d, all draw" % len(names)
               if not broken else "symbols from emoji_san_core.xml",
               "e.g. %s" % names[0] if not broken else
               "%d of %d do not draw, e.g. %s; import the file again" % (
                   len(broken), len(names), ", ".join(broken[:3])))

    # --- embedding on save ------------------------------------------------
    try:  # Qt 5
        where = QStandardPaths.AppDataLocation
    except AttributeError:  # Qt 6
        where = QStandardPaths.StandardLocation.AppDataLocation
    startup = os.path.normpath(os.path.join(
        QStandardPaths.writableLocation(where), "startup.py"))
    try:
        with open(startup, encoding="utf-8") as f:
            in_startup = BEGIN in f.read()
    except (OSError, ValueError):
        in_startup = False
    hook = getattr(builtins, "_emoji_san_embed_fn", None)
    if not in_startup and hook is None:
        report(None, "embedding on save",
               "off; EMBED=True; in front of the install line switches "
               "it on")
    else:
        embeds = False
        if hook is not None and sample:
            # what QGIS writes for a layer style, run through the hook
            doc = QDomDocument()
            element = QgsSymbolLayerUtils.saveSymbol(
                "check", svg_symbol(file_of(sample)), doc,
                QgsReadWriteContext())
            doc.appendChild(element)
            hook(None, element, doc)
            embeds = "base64:" in doc.toString()
        ok = in_startup and hook is not None and embeds
        report(ok, "embedding on save", "" if ok else
               "in startup.py: %s, connected: %s, embeds: %s; %s with "
               "EMBED=True; in front" % (in_startup, hook is not None,
                                         embeds, again))

    # --- demo layer -------------------------------------------------------
    if demo and present:
        from qgis.utils import iface
        first = ["Food and Drink/hot_beverage.svg",
                 "Travel and Places/convenience_store.svg",
                 "Travel and Places/hospital.svg",
                 "Travel and Places/hot_springs.svg",
                 "Travel and Places/bus.svg",
                 "Animals and Nature/cherry_blossom.svg",
                 "Symbols/warning.svg",
                 "Activities/soccer_ball.svg"]
        by_path = {r["path"]: r for r in present}
        picks = [by_path[p] for p in first if p in by_path]
        picks += [r for r in present if r["path"] not in first]
        picks = picks[:8]

        layer = QgsVectorLayer("Point?field=emoji:string", "EmOji-san demo",
                               "memory")
        if QgsProject.instance().crs().isValid():
            layer.setCrs(QgsProject.instance().crs())
        centre, radius = QgsPointXY(0, 0), 1.0
        if iface and iface.mapCanvas().extent().width() > 0:
            extent = iface.mapCanvas().extent()
            centre = extent.center()
            radius = min(extent.width(), extent.height()) * 0.3
        features, categories = [], []
        for i, r in enumerate(picks):
            angle = 2 * math.pi * i / len(picks)
            feature = QgsFeature(layer.fields())
            feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(
                centre.x() + radius * math.cos(angle),
                centre.y() + radius * math.sin(angle))))
            feature.setAttributes([r["emoji"]])
            features.append(feature)
            symbol = QgsMarkerSymbol()
            symbol.changeSymbolLayer(
                0, QgsSvgMarkerSymbolLayer(file_of(r), 10))
            categories.append(QgsRendererCategory(r["emoji"], symbol,
                                                  r["emoji"]))
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()
        layer.setRenderer(QgsCategorizedSymbolRenderer("emoji", categories))
        QgsProject.instance().addMapLayer(layer)
        if iface:
            iface.mapCanvas().refresh()
        print("  layer \"EmOji-san demo\" added: %d emoji around the centre "
              "of the map. Remove it when you have seen it." % len(picks))

    failed = results.count(False)
    print("Result: %s (%d passed, %d failed, %d skipped)" % (
        "PROBLEMS FOUND" if failed else "ALL GOOD",
        results.count(True), failed, results.count(None)))


try:
    _emoji_san_check(globals())
finally:
    del _emoji_san_check
