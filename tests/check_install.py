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
#   - symbols imported from emoji_san_core.xml all draw (and whether they
#     are the drawings of the installed files)
#   - embedding on save, if it is switched on, really embeds
# Then it adds a layer "EmOji-san catalog": every installed emoji with its
# name, in a grid with one block per category, fitted into the view of the
# map. DEMO=False; in front of the command leaves that out.
#
# Nothing is changed apart from the catalog layer.


def _emoji_san_check(ns):
    import base64
    import builtins
    import csv
    import math
    import os

    from qgis.core import (Qgis, QgsApplication, QgsFeature,
                           QgsGeometry, QgsMarkerSymbol, QgsPointXY,
                           QgsProject, QgsReadWriteContext,
                           QgsSettings, QgsStyle,
                           QgsSvgMarkerSymbolLayer, QgsSymbolLayerUtils,
                           QgsVectorLayer)
    from qgis.PyQt.QtCore import QSize, QStandardPaths
    from qgis.PyQt.QtXml import QDomDocument

    FOLDER = "EmOji-san"
    BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
    EMBED_KEY = "emoji-san/embedOnSave"
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
        # Unicode CLDR does not have every emoji in every language
        filled = [r for r in rows if r.get(local[0])]
        report(bool(filled),
               "names in the QGIS language: column %s" % local[0],
               "%d of %d filled%s" % (
                   len(filled), len(rows), ", e.g. %s = %s" % (
                       filled[0]["emoji"], filled[0][local[0]])
                   if filled else ""))

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
        # A symbol is named "<emoji> <file name>" and carries its SVG. If
        # that is not the installed file, the symbol is from the style file
        # of another release.
        installed = {r["emoji"]: file_of(r) for r in present}
        other = 0
        for n in names:
            symbol = style.symbol(n)  # kept: its layers go when it goes
            layer = symbol.symbolLayer(0)
            inside = layer.path() if hasattr(layer, "path") else ""
            if n.split(" ")[0] in installed and inside.startswith("base64:"):
                with open(installed[n.split(" ")[0]], "rb") as f:
                    try:
                        other += base64.b64decode(inside[7:]) != f.read()
                    except ValueError:
                        other += 1
        # importing over symbols of the same name lasts only until QGIS is
        # closed, so the old ones have to go first
        replace = ("to replace them, delete them in the Style Manager, then "
                   "import the file again")
        if broken:
            report(False, "symbols from emoji_san_core.xml",
                   "%d of %d do not draw, e.g. %s; %s" % (
                       len(broken), len(names), ", ".join(broken[:3]),
                       replace))
        else:
            report(True,
                   "symbols from emoji_san_core.xml: %d, all draw"
                   % len(names),
                   "e.g. %s" % names[0] if not other else
                   "in %d of them the drawing is not that of the installed "
                   "file (a style file of another release); %s" % (
                       other, replace))

    # --- embedding on save ------------------------------------------------
    try:  # Qt 5
        where = QStandardPaths.AppDataLocation
    except AttributeError:  # Qt 6
        where = QStandardPaths.StandardLocation.AppDataLocation
    startup = os.path.normpath(os.path.join(
        QStandardPaths.writableLocation(where), "startup.py"))
    try:
        with open(startup, encoding="utf-8") as f:
            startup_text = f.read()
    except (OSError, ValueError):
        startup_text = ""
    in_startup = BEGIN in startup_text
    hook = getattr(builtins, "_emoji_san_embed_fn", None)
    settings = QgsSettings()
    if EMBED_KEY in startup_text or settings.contains(EMBED_KEY):
        enabled = settings.value(EMBED_KEY, False, type=bool)
    else:
        enabled = in_startup or hook is not None  # older installations
    if not enabled and hook is None:
        report(None, "embedding on save",
               "off; EMBED=True; in front of the install line switches "
               "it on")
    elif not enabled:
        report(False, "embedding on save",
               "off for this profile, but the save hook is connected; %s "
               "with EMBED=False; in front" % again)
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

    # --- catalog layer ----------------------------------------------------
    # Every installed emoji as a point with its name, in a grid with one
    # block per category, fitted into the current view of the map.
    if demo and present:
        from qgis.utils import iface
        from qgis.core import (QgsPalLayerSettings, QgsProperty,
                               QgsRuleBasedLabeling, QgsSymbolLayer,
                               QgsTextFormat)

        def enum(owner, scoped, old):  # QGIS 4 has only the scoped names
            try:
                return getattr(getattr(owner, scoped[0]), scoped[1])
            except AttributeError:
                return getattr(owner, old)

        MAP_UNITS = Qgis.RenderUnit.MapUnits
        WIDTH = 10  # emoji per row in a block
        name_column = local[0] if local else None
        blocks = {}
        for r in present:  # index.csv order: Unicode order within a category
            blocks.setdefault(r["path"].split("/")[0], []).append(r)
        heights = [1 + -(-len(rows_) // WIDTH) + 1 for rows_ in blocks.values()]

        view = None
        if iface and iface.mapCanvas().extent().width() > 0:
            view = iface.mapCanvas().extent()
        aspect = view.width() / view.height() if view else 16 / 9

        def stack(columns):
            """Blocks in category order, each into the shortest column."""
            tops, places = [0] * columns, []
            for height in heights:
                column = tops.index(min(tops))
                places.append((column, tops[column]))
                tops[column] += height
            return places, max(tops) - 1  # no gap after the last block

        best = None
        for columns in range(1, len(heights) + 1):
            places, height = stack(columns)
            width = columns * (WIDTH + 1) - 1
            score = abs(math.log(width / height / aspect))
            if best is None or score < best[0]:
                best = (score, places, width, height)
        _, places, grid_w, grid_h = best
        if view:
            cell = min(view.width() / grid_w, view.height() / grid_h)
            left = view.center().x() - cell * grid_w / 2
            top = view.center().y() + cell * grid_h / 2
        else:
            cell, left, top = 1.0, 0.0, 0.0

        layer = QgsVectorLayer(
            "Point?field=kind:string&field=emoji:string&field=name:string"
            "&field=label:string&field=category:string&field=set:string"
            "&field=path:string&field=file:string", "EmOji-san catalog",
            "memory")
        if QgsProject.instance().crs().isValid():
            layer.setCrs(QgsProject.instance().crs())

        def point(column, row):
            return QgsGeometry.fromPointXY(QgsPointXY(
                left + (column + 0.5) * cell, top - (row + 0.5) * cell))

        features = []
        for (category, members), (block, first_row) in zip(blocks.items(),
                                                          places):
            x0 = block * (WIDTH + 1)
            header = QgsFeature(layer.fields())
            header.setGeometry(point(x0 - 0.45, first_row))
            header.setAttributes(["category", "", "", "%s (%d)" % (
                category, len(members)), category, "", "", ""])
            features.append(header)
            for i, r in enumerate(members):
                feature = QgsFeature(layer.fields())
                feature.setGeometry(point(x0 + i % WIDTH,
                                          first_row + 1 + i // WIDTH))
                label = (r.get(name_column) if name_column else "") or r["name"]
                feature.setAttributes(["emoji", r["emoji"], r["name"], label,
                                       category, r.get("set", ""), r["path"],
                                       file_of(r)])
                features.append(feature)
        layer.dataProvider().addFeatures(features)
        layer.updateExtents()

        # one symbol for all: the SVG is the "file" of each point
        marker = QgsSvgMarkerSymbolLayer(file_of(present[0]), cell * 0.6)
        marker.setDataDefinedProperty(
            enum(QgsSymbolLayer, ("Property", "Name"), "PropertyName"),
            QgsProperty.fromField("file"))
        marker.setDataDefinedProperty(
            enum(QgsSymbolLayer, ("Property", "LayerEnabled"),
                 "PropertyLayerEnabled"),
            QgsProperty.fromExpression("\"kind\" = 'emoji'"))
        symbol = QgsMarkerSymbol()
        symbol.changeSymbolLayer(0, marker)
        symbol.setSizeUnit(MAP_UNITS)
        layer.renderer().setSymbol(symbol)

        def labels(size, quadrant, y_offset, bold=False, wrap=0):
            settings = QgsPalLayerSettings()
            settings.fieldName = "label"
            settings.placement = Qgis.LabelPlacement.OverPoint
            settings.quadOffset = quadrant
            settings.yOffset = y_offset
            settings.offsetUnits = MAP_UNITS
            settings.autoWrapLength = wrap
            settings.displayAll = True  # names stay with their emoji
            text = QgsTextFormat()
            text.setSize(size)
            text.setSizeUnit(MAP_UNITS)
            if bold:
                font = text.font()
                font.setBold(True)
                text.setFont(font)
            settings.setFormat(text)
            return settings

        Quadrant = Qgis.LabelQuadrantPosition
        root_rule = QgsRuleBasedLabeling.Rule(None)
        root_rule.appendChild(QgsRuleBasedLabeling.Rule(
            labels(cell * 0.12, Quadrant.Below, cell * 0.3, wrap=14),
            0, 0, "\"kind\" = 'emoji'"))
        root_rule.appendChild(QgsRuleBasedLabeling.Rule(
            labels(cell * 0.4, Quadrant.Right, 0, bold=True),
            0, 0, "\"kind\" = 'category'"))
        layer.setLabeling(QgsRuleBasedLabeling(root_rule))
        layer.setLabelsEnabled(True)
        QgsProject.instance().addMapLayer(layer)
        if iface:
            iface.mapCanvas().refresh()
        print("  layer \"EmOji-san catalog\" added: the %d emoji, by category "
              "and with their names, in the view of the map. Zoom in to read "
              "the names; remove the layer when you have seen it."
              % len(present))

    failed = results.count(False)
    print("Result: %s (%d passed, %d failed, %d skipped)" % (
        "PROBLEMS FOUND" if failed else "ALL GOOD",
        results.count(True), failed, results.count(None)))


try:
    _emoji_san_check(globals())
finally:
    del _emoji_san_check
