#!/usr/bin/env python3
"""Maintainer test: install, switch sets, embed, check and uninstall.

    python3 tests/scenarios.py

Needs a Python that can import qgis (QGIS 3 or 4), for example inside the
qgis/qgis Docker image:

    docker run --rm -v "$PWD":/repo -w /repo -e QT_QPA_PLATFORM=offscreen \\
        qgis/qgis python3 tests/scenarios.py

Run it before tagging a release. It zips the working tree, gives QGIS an
empty settings folder (Qt's test location, ~/.qttest on Linux and macOS) and
runs the scripts the way the Python console runs the one-line installer.
Your own QGIS settings are not touched. Nothing is downloaded, so the name
column from Unicode CLDR is not covered.
"""
import contextlib
import csv
import io
import os
import pathlib
import re
import shutil
import sys
import tempfile
import unittest.mock
import zipfile

from qgis.core import (QgsApplication, QgsFillSymbol, QgsMarkerSymbol,
                       QgsPalLayerSettings, QgsPointPatternFillSymbolLayer,
                       QgsProject, QgsSettings, QgsStyle,
                       QgsSVGFillSymbolLayer, QgsSvgMarkerSymbolLayer,
                       QgsTextBackgroundSettings, QgsTextFormat,
                       QgsVectorLayer, QgsVectorLayerSimpleLabeling)
from qgis.PyQt.QtCore import QCoreApplication, QStandardPaths

REPO = pathlib.Path(__file__).resolve().parent.parent
BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
failures = []


def check(ok, what):
    print("  %s %s" % ("ok  " if ok else "FAIL", what))
    if not ok:
        failures.append(what)


def console(script, **options):
    """Run a script as the Python console would. Returns what it printed
    and the names it left behind in the console's namespace."""
    ns = {"__name__": "__console__", "__doc__": None}
    ns.update(options)
    path = str(REPO / script)
    with open(path, "rb") as f:
        code = compile(f.read(), path, "exec")
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        exec(code, ns)
    left = sorted(set(ns) - {"__name__", "__doc__", "__builtins__"})
    return printed.getvalue(), left


def svgs(folder):
    return sorted(
        os.path.relpath(os.path.join(path, name), folder).replace(os.sep, "/")
        for path, _, names in os.walk(folder)
        for name in names if name.endswith(".svg"))


def svg_paths():
    value = QgsSettings().value("svg/searchPathsForSVG", [])
    return [value] if isinstance(value, str) else list(value or [])


def main():
    QStandardPaths.setTestModeEnabled(True)
    QCoreApplication.setOrganizationName("QGIS")
    QCoreApplication.setApplicationName(QgsApplication.QGIS_APPLICATION_NAME)
    try:  # Qt 5
        where = QStandardPaths.AppDataLocation
    except AttributeError:  # Qt 6
        where = QStandardPaths.StandardLocation.AppDataLocation
    settings = QStandardPaths.writableLocation(where)
    shutil.rmtree(settings, ignore_errors=True)
    app = QgsApplication([], True,
                         os.path.join(settings, "profiles", "default"))
    app.initQgis()
    work = tempfile.mkdtemp(prefix="emoji-san-test-")
    try:
        scenarios(settings, work)
    finally:
        QgsProject.instance().clear()
        app.exitQgis()
        shutil.rmtree(settings, ignore_errors=True)
        shutil.rmtree(work, ignore_errors=True)
    if failures:
        print("\n%d FAILED:\n  %s" % (len(failures), "\n  ".join(failures)))
    else:
        print("\nAll scenarios passed.")
    return 1 if failures else 0


def scenarios(settings, work):
    root = os.path.join(settings, "EmOji-san")
    startup = os.path.join(settings, "startup.py")
    print("settings folder: %s" % settings)

    # The ZIP GitHub serves for a tag: everything under one top folder, and
    # without styles/, which .gitattributes keeps out of it.
    archive = os.path.join(work, "repo.zip")
    skip = {".git", ".github", "styles", "__pycache__", "review_core.html"}
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(REPO.rglob("*")):
            rel = path.relative_to(REPO)
            if path.is_file() and not skip.intersection(rel.parts):
                z.write(path, "emoji-san-test/%s" % rel.as_posix())
    with open(REPO / "index.csv", encoding="utf-8", newline="") as f:
        index = list(csv.DictReader(f))
    want = {s: sorted(r["path"] for r in index if r["set"] in sets)
            for s, sets in (("S", "S"), ("M", "SM"), ("L", "SML"))}

    print("\n0. the repository")
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    tag = re.search(r'TAG = "v([0-9.]+)"',
                    (REPO / "install.py").read_text(encoding="utf-8")).group(1)
    named = set(re.findall(r"emoji-san/v([0-9.]+)/", readme)
                + re.findall(r"tags/v([0-9.]+)\.zip", readme)
                + re.findall(r"emoji-san-([0-9.]+)\.zip", readme))
    check(named == {tag}, "README.md and install.py name the same version "
          "(%s, %s)" % (tag, sorted(named)))
    sizes = ["{:,}".format(len(want[s])) for s in "SML"]
    check(re.findall(r"^\| `([SML])` \| ([0-9,]+) \|", readme, flags=re.M)
          == list(zip("SML", sizes)) * 2
          and readme.count("(S %s, M %s, L %s)" % tuple(sizes)) == 2,
          "the set sizes in README.md are those of index.csv (%s)"
          % ", ".join(sizes))
    core = []
    for line in (REPO / "core_list.txt").read_text(
            encoding="utf-8").splitlines():
        if line.partition("#")[0].strip():
            core.append(line.partition("#")[0].strip() + ".svg")
    check(sorted(core) == want["S"], "the S set of index.csv is "
          "core_list.txt (run build/make_core.py after editing it)")
    style = (REPO / "styles" / "emoji_san_core.xml").read_text(
        encoding="utf-8")
    check(style.count("<symbol ") == len(core), "the style file has one "
          "symbol for each emoji of the S set")
    check(all((REPO / "collections" / ("noto_emoji_" + r["collection"])
               / "svg" / r["path"]).is_file() for r in index),
          "every emoji of index.csv has its SVG file")
    notice = (REPO / "LICENSE-noto-emoji.txt").read_text(encoding="utf-8")
    check("Version 2.0, January 2004" in notice and "Google" in notice,
          "LICENSE-noto-emoji.txt is the Apache License 2.0 with Google's "
          "notice")

    def install(**options):
        options.setdefault("ZIP", archive)
        options.setdefault("LOCALE", "en")  # no download of names
        return console("install.py", **options)

    print("\n1. first install")
    out, left = install()
    check(svgs(root) == want["S"], "the S set is installed (%d files)"
          % len(want["S"]))
    check(not left, "nothing is left in the console's namespace %s" % left)
    check(any(os.path.normpath(p) == root for p in svg_paths())
          and any(os.path.normpath(p) == root
                  for p in QgsApplication.svgPaths()),
          "the folder is an SVG path")
    check("+%d added, -0 removed" % len(want["S"]) in out
          and "registered as an SVG path" in out and "Next:" in out,
          "the report of a first install")
    with open(os.path.join(root, "index.csv"), encoding="utf-8",
              newline="") as f:
        installed = list(csv.DictReader(f))
    check(sorted(r["path"] for r in installed) == want["S"]
          and "name" in installed[0] and "collection" not in installed[0],
          "index.csv lists the installed emoji")
    check(all(os.path.isfile(os.path.join(root, name)) for name in (
        "LICENSE-noto-emoji.txt", "NOTICE", "UPSTREAM_COMMIT.txt",
        "embed_on_save.py", "README.txt")), "license files are alongside")
    check(not os.path.exists(startup), "startup.py is not created")

    print("\n2. the same line again")
    sample = os.path.join(root, *want["S"][0].split("/"))
    stamp = os.stat(sample).st_mtime_ns
    out, _ = install(ZIP=pathlib.Path(archive).as_uri())  # as a download
    check("+0 added, -0 removed)" in out and svgs(root) == want["S"]
          and os.stat(sample).st_mtime_ns == stamp
          and "registered" not in out and "Next:" not in out,
          "nothing changes, files are not rewritten")

    print("\n3. bigger sets")
    out, _ = install(SET="M")
    check(svgs(root) == want["M"] and "-0 removed" in out,
          "SET='M' adds up to M (%d files)" % len(want["M"]))
    out, _ = install()
    check(svgs(root) == want["M"], "without SET, M stays")
    out, _ = install(SET="L")
    check(svgs(root) == want["L"], "SET='L' adds up to L (%d files)"
          % len(want["L"]))

    print("\n4. a smaller set, with files of the user's own in the folder")
    own = [os.path.join(root, "Mine", "own.svg"),
           os.path.join(root, "Travel and Places", "zz_own.svg")]
    for path in own:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        shutil.copy(sample, path)
    open(os.path.join(root, "Flags", ".DS_Store"), "w").close()
    out, _ = install(SET="m")
    kept = ["Mine/own.svg", "Travel and Places/zz_own.svg"]
    check(svgs(root) == sorted(want["M"] + kept),
          "SET='m' goes down to M and keeps the user's files")
    check(not os.path.exists(os.path.join(root, "Flags")),
          "a category that is empty now is removed, .DS_Store or not")
    check("-%d removed" % (len(want["L"]) - len(want["M"])) in out
          and "show \"?\"" in out, "the report of a downgrade")
    for path in own:
        os.remove(path)
    os.rmdir(os.path.dirname(own[0]))

    print("\n5. wrong options and a ZIP that is not there")
    before = svgs(root)
    out, left = install(SET="XL")
    check("Nothing changed" in out and svgs(root) == before and not left,
          "SET='XL' is refused")
    out, left = install(EMBED="yes")
    check("Nothing changed" in out and not left, "EMBED='yes' is refused")
    out, left = console("install.py", ZIP=os.path.join(work, "no.zip"))
    check("could not get the files" in out and svgs(root) == before
          and not left, "a missing ZIP changes nothing")

    print("\n6. an install without usable index.csv (older installer)")
    os.remove(os.path.join(root, "index.csv"))
    out, _ = install()
    check(svgs(root) == want["M"] and "+0 added, -0 removed" in out,
          "the set is recognised from the files, M stays")

    print("\n7. embedding on save")
    with open(startup, "w", encoding="utf-8") as f:
        f.write("# my own start-up code\nMY_SETTING = 1\n")
    out, _ = install(EMBED=True)
    with open(startup, encoding="utf-8") as f:
        text = f.read()
    check(text.startswith("# my own start-up code\nMY_SETTING = 1\n")
          and text.count(BEGIN) == 1 and "embed_on_save.py" in text,
          "EMBED=True adds the lines to startup.py, after the user's own")
    compile(text, startup, "exec")
    check("on save: on" in out, "the report says it is on")
    saved = save_project(root, os.path.join(work, "on.qgs"))
    check(saved["ours"] == 0 and saved["embedded"] == 4,
          "marker, fill, nested marker and label background are embedded")
    check(saved["foreign"] >= 1, "an SVG from another folder is left alone")
    check(saved["in_memory_is_file"],
          "the layer in the open project keeps its file path")
    check(saved["reloaded_embedded"], "the saved project reopens with the "
          "SVG inside")
    install()
    with open(startup, encoding="utf-8") as f:
        check(f.read() == text, "without EMBED it stays on, startup.py is "
              "not rewritten")
    out, _ = install(EMBED=False)
    with open(startup, encoding="utf-8") as f:
        check(f.read() == "# my own start-up code\nMY_SETTING = 1\n",
              "EMBED=False removes the lines and nothing else")
    saved = save_project(root, os.path.join(work, "off.qgs"))
    check(saved["embedded"] == 0 and saved["ours"] == 4,
          "nothing is embedded any more")
    os.remove(startup)
    install(EMBED=True)
    with open(startup, encoding="utf-8") as f:
        check(f.read().startswith(BEGIN), "startup.py is created if needed")

    print("\n8. check_install.py and diagnose.py")
    style = QgsStyle.defaultStyle()
    style.importXml(str(REPO / "styles" / "emoji_san_core.xml"))
    out, left = console("tests/check_install.py")
    check("Result: ALL GOOD" in out and "[FAIL]" not in out, "check passes")
    check(out.count("[PASS]") == 6, "six checks pass, among them the "
          "imported symbols and the embedding")
    check(not left, "nothing is left in the console's namespace %s" % left)
    check(len(QgsProject.instance().mapLayersByName("EmOji-san demo")) == 1,
          "the demo layer is added")
    QgsProject.instance().clear()
    out, _ = console("tests/check_install.py", DEMO=False)
    check(not QgsProject.instance().mapLayers(), "DEMO=False adds no layer")
    with unittest.mock.patch("os.path.expanduser",
                             lambda path: path.replace("~", work)):
        out, left = console("tests/diagnose.py", BUDGET=5)
    check("Finished in" in out and not left
          and os.path.isfile(os.path.join(work, "emoji-san-diagnose.txt")),
          "diagnose runs and saves its report")

    print("\n9. the EmOji-san folder of another QGIS version is registered")
    other = os.path.join(work, "QGIS3", "EmOji-san")
    shutil.copytree(root, other)
    console("uninstall.py")
    QgsApplication.setSvgPaths([other.replace(os.sep, "/")])
    out, _ = console("tests/check_install.py", DEMO=False)
    check("this QGIS still uses" in out and "PROBLEMS FOUND" in out,
          "check says the folder is not here and points at the other one")
    with open(os.path.join(work, "QGIS3", "startup.py"), "w",
              encoding="utf-8") as f:
        f.write(text)  # embedding is on in that other QGIS
    out, _ = install()
    check(svgs(root) == want["M"], "the set of that folder is kept (M)")
    check([os.path.normpath(p) for p in svg_paths()] == [root]
          and "taken off the SVG paths" in out,
          "the new folder replaces it on the SVG paths")
    check(svgs(other) == want["M"], "the other folder's files stay")
    with open(startup, encoding="utf-8") as f:
        check(f.read().startswith(BEGIN) and "on save: on" in out,
              "embedding on save is kept as well")

    print("\n10. uninstall")
    install(EMBED=True)
    mine = os.path.join(root, "Mine", "own.svg")
    os.makedirs(os.path.dirname(mine))
    shutil.copy(sample, mine)
    open(os.path.join(root, "Symbols", ".DS_Store"), "w").close()
    out, left = console("uninstall.py")
    check(svgs(root) == ["Mine/own.svg"] and "Kept 1 file" in out
          and os.listdir(root) == ["Mine"]
          and [os.path.normpath(p) for p in svg_paths()] == [root],
          "a file of the user's own stays, and the folder with it")
    check(not os.path.exists(startup), "startup.py is gone (it held only "
          "our lines)")
    check("200 symbols tagged EmOji-san" in out, "the imported symbols are "
          "mentioned")
    check(not left, "nothing is left in the console's namespace %s" % left)
    out, _ = console("uninstall.py")
    check(svgs(root) == ["Mine/own.svg"] and "No index.csv" in out,
          "a second uninstall, now without index.csv, leaves it alone too")
    os.remove(mine)
    os.rmdir(os.path.dirname(mine))
    out, _ = console("uninstall.py")
    check(not os.path.exists(root) and not svg_paths(),
          "with the folder empty, it is removed and taken off the SVG paths")
    out, _ = console("uninstall.py")
    check("not installed" in out, "another uninstall has nothing to do")


def save_project(root, path):
    """Save a project that uses EmOji-san SVGs in every place the save hook
    covers, plus one SVG that is not ours. Returns counts from the file."""
    def shape(owner, name):  # QGIS 3 / QGIS 4 spelling of an enum
        return getattr(getattr(owner, "ShapeType", owner), name)

    def ours(name):
        return os.path.join(root, *name.split("/"))

    foreign = next(os.path.join(folder, name)
                   for folder, _, names in os.walk(
                       os.path.join(QgsApplication.pkgDataPath(), "svg"))
                   for name in sorted(names) if name.endswith(".svg"))
    project = QgsProject.instance()
    project.clear()

    points = QgsVectorLayer("Point?crs=EPSG:4326&field=n:string", "points",
                            "memory")
    marker = QgsMarkerSymbol()
    marker.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(
        ours("Travel and Places/bus.svg"), 8))
    marker.appendSymbolLayer(QgsSvgMarkerSymbolLayer(foreign, 4))
    points.renderer().setSymbol(marker)
    background = QgsTextBackgroundSettings()
    background.setEnabled(True)
    background.setType(shape(QgsTextBackgroundSettings, "ShapeSVG"))
    background.setSvgFile(ours("Symbols/warning.svg"))
    text = QgsTextFormat()
    text.setBackground(background)
    labels = QgsPalLayerSettings()
    labels.fieldName = "n"
    labels.setFormat(text)
    points.setLabeling(QgsVectorLayerSimpleLabeling(labels))
    points.setLabelsEnabled(True)

    polygons = QgsVectorLayer("Polygon?crs=EPSG:4326", "polygons", "memory")
    fill = QgsFillSymbol()
    fill.changeSymbolLayer(0, QgsSVGFillSymbolLayer(
        ours("Food and Drink/hot_beverage.svg"), 20, 0))
    # and a marker inside another symbol layer: a point pattern
    inner = QgsMarkerSymbol()
    inner.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(
        ours("Animals and Nature/cherry_blossom.svg"), 6))
    pattern = QgsPointPatternFillSymbolLayer()
    pattern.setSubSymbol(inner)
    fill.appendSymbolLayer(pattern)
    polygons.renderer().setSymbol(fill)

    project.addMapLayers([points, polygons])
    project.write(path)
    with open(path, encoding="utf-8") as f:
        xml = f.read()
    result = {
        "embedded": xml.count('"base64:'),
        "ours": sum(xml.count('"%s"' % name) for name in (
            "Travel and Places/bus.svg", "Symbols/warning.svg",
            "Food and Drink/hot_beverage.svg",
            "Animals and Nature/cherry_blossom.svg")),
        "foreign": xml.count(os.path.basename(foreign)),
        "in_memory_is_file": os.path.isfile(
            points.renderer().symbol().symbolLayer(0).path()),
    }
    project.clear()
    project.read(path)
    layer = project.mapLayersByName("points")[0]
    result["reloaded_embedded"] = layer.renderer().symbol().symbolLayer(
        0).path().startswith("base64:")
    project.clear()
    return result


if __name__ == "__main__":
    sys.exit(main())
