#!/usr/bin/env python3
r"""Maintainer test: install, switch sets, embed, check and uninstall.

    python3 tests/scenarios.py

Needs a Python that can import qgis (QGIS 3 or 4), for example inside the
qgis/qgis Docker image:

    docker run --rm -v "$PWD":/repo -w /repo -e QT_QPA_PLATFORM=offscreen \
        qgis/qgis python3 tests/scenarios.py

Run it before tagging a release. It zips the working tree, gives QGIS an
empty settings folder and runs the scripts the way the Python console runs
the one-line installer.

Each run uses a new folder under Qt's test location (~/.qttest on Linux
and macOS). The test stops if QGIS does not use the selected test profile.
It also starts separate QGIS processes to check shared profile settings
and recovery after an interrupted write.

Nothing is downloaded, unless you add --online: then it also fetches the
emoji names of four languages from Unicode CLDR, the way install.py does.

On Linux, run it once with MALLOC_PERTURB_=165 in the environment as well.
Freed memory is overwritten then, and a script that uses a QGIS object after
it was deleted crashes here, not in somebody's QGIS.
"""
import base64
import builtins
import contextlib
import csv
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest.mock
import urllib.error
import uuid
import warnings
import zipfile

from qgis.core import (QgsApplication, QgsExpression, QgsExpressionContext,
                       QgsFillSymbol, QgsMarkerSymbol, QgsPalLayerSettings,
                       QgsPointPatternFillSymbolLayer, QgsProject, QgsProperty,
                       QgsSettings, QgsStyle,
                       QgsSVGFillSymbolLayer, QgsSvgMarkerSymbolLayer,
                       QgsSymbolLayer, QgsTextBackgroundSettings, QgsTextFormat,
                       QgsUserProfile, QgsVectorLayer, QgsVectorLayerSimpleLabeling)
from qgis.PyQt.QtCore import QCoreApplication, QSettings, QSize, QStandardPaths

REPO = pathlib.Path(__file__).resolve().parent.parent
BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
END = "# <<< EmOji-san <<<"
EMBED_KEY = "emoji-san/embedOnSave"
CRASH_EXIT = 73
failures = []


def check(ok, what):
    print("  %s %s" % ("ok  " if ok else "FAIL", what))
    if not ok:
        failures.append(what)


def console(source, **options):
    """Run a script of the repository, or one line as it is typed, the way
    the Python console would. Returns what it printed and the names it left
    behind in the console's namespace."""
    ns = {"__name__": "__console__", "__doc__": None}
    ns.update(options)
    if source.endswith(".py"):
        path = str(REPO / source)
        with open(path, "rb") as f:
            code = compile(f.read(), path, "exec")
    else:
        code = compile(source, "<console>", "single")
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


def test_app(organization, profile_name):
    """Use the same per-profile settings initialization as QGIS Desktop."""
    if not re.fullmatch(r"EmOji-san-test-[0-9a-f]{32}", organization):
        sys.exit("ERROR: invalid test organization")
    profiles = {
        "default": ("", "default"),
        "second profile": ("", "second profile"),
        "recovery": ("", "recovery"),
        "custom root": ("custom profile settings", "default"),
        "migrated profile": ("version migration/QGIS4", "default"),
        "destination profile": ("version migration/QGIS4", "second profile"),
    }
    if profile_name not in profiles:
        sys.exit("ERROR: invalid test profile")
    os.environ.pop("QGIS_CUSTOM_CONFIG_PATH", None)
    QStandardPaths.setTestModeEnabled(True)
    QCoreApplication.setOrganizationName(organization)
    QCoreApplication.setApplicationName(QgsApplication.QGIS_APPLICATION_NAME)
    try:  # Qt 5
        where = QStandardPaths.AppDataLocation
    except AttributeError:  # Qt 6
        where = QStandardPaths.StandardLocation.AppDataLocation
    settings = pathlib.Path(QStandardPaths.writableLocation(where)).resolve()
    if organization not in settings.parts or not any(
            p.lower().lstrip(".") == "qttest" for p in settings.parts):
        sys.exit("ERROR: Qt's test mode gives %s, which does not look like "
                 "a test folder. Nothing was touched." % settings)
    subdirectory, profile_name = profiles[profile_name]
    profile = settings / subdirectory / "profiles" / profile_name
    profile.mkdir(parents=True, exist_ok=True)
    user_profile = QgsUserProfile(str(profile))
    user_profile.initSettings()
    app = QgsApplication([], True, str(profile), "desktop")
    app.initQgis()
    user_profile.initSettings()
    active = pathlib.Path(QgsApplication.qgisSettingsDirPath()).resolve()
    appdata = pathlib.Path(QStandardPaths.writableLocation(where)).resolve()
    ini = pathlib.Path(QSettings().fileName()).resolve()
    if active != profile or appdata != settings or profile not in ini.parents:
        app.exitQgis()
        sys.exit("ERROR: QGIS does not use the selected test profile %s."
                 % profile)
    return app, str(settings)


def main():
    organization = "EmOji-san-test-" + uuid.uuid4().hex
    app, settings = test_app(organization, "default")
    work = tempfile.mkdtemp(prefix="emoji-san-test-")
    try:
        scenarios(settings, work, "--online" in sys.argv, organization)
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


def scenarios(settings, work, online, organization):
    root = os.path.join(settings, "EmOji-san")
    startup = os.path.join(settings, "startup.py")
    print("settings folder: %s" % settings)
    QgsSettings().setValue("locale/userLocale", "ja")

    # The ZIP GitHub serves for a tag: everything under one top folder
    # named after the tag, and without styles/, which .gitattributes keeps
    # out of it.
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    tag = re.search(r'TAG = "v([0-9.]+)"',
                    (REPO / "install.py").read_text(encoding="utf-8")).group(1)
    archive = os.path.join(work, "emoji-san-%s.zip" % tag)
    skip = {".git", ".github", "styles", "__pycache__", "review_core.html"}
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(REPO.rglob("*")):
            rel = path.relative_to(REPO)
            if path.is_file() and not skip.intersection(rel.parts):
                z.write(path, "emoji-san-%s/%s" % (tag, rel.as_posix()))
    with open(REPO / "index.csv", encoding="utf-8", newline="") as f:
        index = list(csv.DictReader(f))
    want = {s: sorted(r["path"] for r in index if r["set"] in sets)
            for s, sets in (("S", "S"), ("M", "SM"), ("L", "SML"))}

    print("\n0. the repository")
    named = set(re.findall(r"emoji-san/v([0-9.]+)/", readme)
                + re.findall(r"tags/v([0-9.]+)\.zip", readme)
                + re.findall(r"releases/download/v([0-9.]+)/", readme)
                + re.findall(r"emoji-san-([0-9.]+)\.zip", readme)
                + re.findall(r"emoji-san-([0-9.]+)/install", readme))
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
    # What Qt's SVG renderer gets wrong (black hands, black patches);
    # build/update_from_upstream.py rewrites the files that have it.
    qt_cannot = re.compile(r"<clipPath|Gradient[^>]*xlink:href|rgba\(")
    wrong = [r["path"] for r in index if qt_cannot.search(
        (REPO / "collections" / ("noto_emoji_" + r["collection"]) / "svg"
         / r["path"]).read_text(encoding="utf-8"))]
    check(not wrong, "no SVG file has clip paths, linked gradients or "
          "rgba() colors, which QGIS draws wrong %s" % wrong[:5])
    notice = (REPO / "LICENSE-noto-emoji.txt").read_text(encoding="utf-8")
    check("Version 2.0, January 2004" in notice and "Google" in notice,
          "LICENSE-noto-emoji.txt is the Apache License 2.0 with Google's "
          "notice")

    def install(**options):
        options.setdefault("ZIP", archive)
        options.setdefault("LOCALE", "en")  # no download of names
        return console("install.py", **options)

    def no_network(url, timeout=None):
        raise urllib.error.URLError("no network in this test")

    print("\n1. first install, with the line of README.md for a computer "
          "without internet access")
    placeholder = "'/path/to/emoji-san-%s.zip'" % tag
    lines = re.findall(r"^ZIP=" + re.escape(placeholder) + r"; .+$",
                       readme, flags=re.M)
    check(len(lines) == 2 and len(set(lines)) == 1,
          "README.md has the line, the same in both languages")

    def source_install(path, options=""):
        return console(options + lines[0].replace(placeholder, repr(str(path)), 1))

    with unittest.mock.patch("urllib.request.urlopen") as network:
        out, left = source_install(archive)
    check(svgs(root) == want["S"], "the S set is installed (%d files)"
          % len(want["S"]))
    check(not left and not network.called,
          "the offline line leaves no names or network requests on Japanese QGIS")
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
        "LICENSE-noto-emoji.txt", "LICENSE-gemoji.txt", "NOTICE",
        "UPSTREAM_COMMIT.txt", "README.txt")), "license files are alongside")
    check(not os.path.exists(os.path.join(root, "embed_on_save.py")),
          "the installation contains no separate Python save hook")
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
    out, _ = install(ZIP=pathlib.Path(archive))
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

    print("\n4a. a user SVG has the same name as a larger set's SVG")
    collision = pathlib.Path(root, min(set(want["L"]) - set(want["M"])))
    had_category = collision.parent.is_dir()
    collision.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(sample, collision)
    before = inventory(root)
    install(SET="M")
    check(collision.is_file()
          and collision.read_bytes() == pathlib.Path(sample).read_bytes(),
          "installing M preserves the user's same-named L SVG")
    install(SET="L")
    check(inventory(root) == before,
          "an installation with a conflicting user SVG changes nothing")
    if collision.is_file():
        collision.unlink()
    install(SET="M")
    if (not had_category and collision.parent.is_dir()
            and not any(collision.parent.iterdir())):
        collision.parent.rmdir()

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
    with unittest.mock.patch("urllib.request.urlopen", no_network):
        out, left = console("install.py", ZIP=pathlib.Path(archive).as_uri())
    check("could not get the files (URLError" in out
          and svgs(root) == before and not left,
          "a failed local ZIP read changes nothing")

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
          and text.count(BEGIN) == 1 and EMBED_KEY in text,
          "EMBED=True adds the lines to startup.py, after the user's own")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        exec(compile(text, startup, "exec"), {"__name__": "startup"})
    check(not caught, "startup.py runs as QGIS runs it at a start, without "
          "a Python warning %s" % [str(w.message) for w in caught])
    check("on save: on" in out
          and QgsSettings().value(EMBED_KEY, False, type=bool),
          "the report and active profile setting say it is on")
    saved = save_project(root, os.path.join(work, "on.qgs"))
    check(saved["ours"] == 0 and saved["embedded"] == 4,
          "marker, fill, nested marker and label background are embedded")
    check(saved["foreign"] >= 1, "an SVG from another folder is left alone")
    check(saved["in_memory_is_file"],
          "the layer in the open project keeps its file path")
    check(saved["reloaded_embedded"], "the saved project reopens with the "
          "SVG inside")
    check_mixed_svg_project(root, os.path.join(work, "fixed-and-expression.qgz"))
    install()
    with open(startup, encoding="utf-8") as f:
        check(f.read() == text, "without EMBED it stays on, startup.py is "
              "not rewritten")
    with open(startup, "w", encoding="utf-8") as f:  # as an older release
        f.write(text.replace(EMBED_KEY, "old-embed-key"))
    install()
    with open(startup, encoding="utf-8") as f:
        check(f.read() == text, "lines written by an older release are "
              "brought up to date")
    out, _ = install(EMBED=False)
    with open(startup, encoding="utf-8") as f:
        check(f.read() == text
              and not QgsSettings().value(EMBED_KEY, False, type=bool),
              "EMBED=False keeps other profiles' startup code and disables "
              "the active profile")
    saved = save_project(root, os.path.join(work, "off.qgs"))
    check(saved["embedded"] == 0 and saved["ours"] == 4,
          "nothing is embedded any more")
    out, _ = console("tests/check_install.py", DEMO=False)
    check("[SKIP] embedding on save" in out,
          "the install check recognizes the active profile has opted out")
    os.remove(startup)
    install(EMBED=True)
    with open(startup, encoding="utf-8") as f:
        check(f.read().startswith(BEGIN), "startup.py is created if needed")

    print("\n8. emoji names from Unicode CLDR")

    def cldr(files, status=404):
        """A stand-in for urlopen that serves these CLDR files and answers
        every other request with an HTTP error."""
        def urlopen(url, timeout=None):
            for name, content in files.items():
                if url.endswith(name):
                    return io.BytesIO(json.dumps(content).encode("utf-8"))
            raise urllib.error.HTTPError(url, status, "status %d" % status,
                                         {}, io.BytesIO())
        return urlopen

    def names(*pairs):
        return {"annotations": {"annotations": {
            emoji: {"tts": [name]} for emoji, name in pairs}}}

    def index_csv():
        with open(os.path.join(root, "index.csv"), encoding="utf-8",
                  newline="") as f:
            return {r["path"]: r for r in csv.DictReader(f)}

    parents = {"supplemental": {"parentLocales": {"parentLocale": {
        "es-MX": "es-419"}}}}
    # as CLDR has it: a regional file holds only what differs from its
    # parent, and most emoji are listed without U+FE0F
    spanish = {
        "supplemental/parentLocales.json": parents,
        "/annotations/es/annotations.json": names(
            ("\U0001F68C", "autobus"), ("\u2615", "bebida caliente"),
            ("\u2668", "aguas termales")),
        "/annotations/es-419/annotations.json": names(
            ("\U0001F68C", "bus")),
        "/annotations/es-MX/annotations.json": names(
            ("\u2615", "cafe")),
    }
    with unittest.mock.patch("urllib.request.urlopen", cldr(spanish)):
        out, _ = install(LOCALE="es_MX")
    listed = index_csv()
    check("(+ name_es-MX)" in out
          and listed["Travel and Places/bus.svg"].get("name_es-MX") == "bus"
          and listed["Food and Drink/hot_beverage.svg"]["name_es-MX"]
          == "cafe"
          and listed["Travel and Places/hot_springs.svg"]["name_es-MX"]
          == "aguas termales",
          "es_MX takes the names of es, then es-419, then es-MX")
    for urlopen, said, what in (
            (cldr({"supplemental/parentLocales.json": parents}),
             "has no emoji names", "a language CLDR does not have"),
            (cldr({"supplemental/parentLocales.json": parents}, 503),
             "HTTPError", "a server error"),
            (no_network, "URLError", "no network")):
        with unittest.mock.patch("urllib.request.urlopen", urlopen):
            out, _ = install(LOCALE="xx")
        check("no second name column" in out and said in out
              and not any(c.startswith("name_") for c in next(iter(
                  index_csv().values())))
              and svgs(root) == want["M"],
              "%s: no second name column, and the report says why" % what)
    if online:
        for locale, column in (("ja", "name_ja"), ("es_MX", "name_es-MX"),
                               ("nb", "name_no"), ("zh_TW", "name_zh-Hant")):
            install(SET="L", LOCALE=locale)
            named = [r.get(column) for r in index_csv().values()]
            check(len(named) == len(want["L"]) and all(named),
                  "downloaded: LOCALE=%r gives every emoji a name in %s"
                  % (locale, column))
        install(SET="M", LOCALE="en")

    print("\n9. check_install.py and diagnose.py")
    style = QgsStyle.defaultStyle()
    style.importXml(str(REPO / "styles" / "emoji_san_core.xml"))
    out, left = console("tests/check_install.py")
    check("Result: ALL GOOD" in out and "[FAIL]" not in out, "check passes")
    check(out.count("[PASS]") == 6 and "all draw" in out
          and "of another release" not in out, "six checks pass, among "
          "them the imported symbols and the embedding")
    check(not left, "nothing is left in the console's namespace %s" % left)
    check(len(QgsProject.instance().mapLayersByName("EmOji-san demo")) == 1,
          "the demo layer is added")
    QgsProject.instance().clear()
    out, _ = console("tests/check_install.py", DEMO=False)
    check(not QgsProject.instance().mapLayers(), "DEMO=False adds no layer")
    # a style file in which the first symbol has the drawing of the second
    xml = (REPO / "styles" / "emoji_san_core.xml").read_text(encoding="utf-8")
    drawings = re.findall(r'v="(base64:[^"]+)"', xml)
    other = os.path.join(work, "other_release.xml")
    with open(other, "w", encoding="utf-8") as f:
        f.write(xml.replace(drawings[0], drawings[1], 1))
    style.importXml(other)
    out, _ = console("tests/check_install.py", DEMO=False)
    check("in 1 of them the drawing is not that of the installed file" in out
          and "Result: ALL GOOD" in out, "check points out a symbol from "
          "the style file of another release")
    style.importXml(str(REPO / "styles" / "emoji_san_core.xml"))
    with unittest.mock.patch("os.path.expanduser",
                             lambda path: path.replace("~", work)):
        out, left = console("tests/diagnose.py", BUDGET=5)
    check("Finished in" in out and not left
          and os.path.isfile(os.path.join(work, "emoji-san-diagnose.txt")),
          "diagnose runs and saves its report")

    version_migration_scenario(settings, root, archive, work, organization, want)

    print("\n11. uninstall")
    install(EMBED=True)
    mine = os.path.join(root, "Mine", "own.svg")
    os.makedirs(os.path.dirname(mine))
    shutil.copy(sample, mine)
    open(os.path.join(root, "Symbols", ".DS_Store"), "w").close()
    out, left = console("uninstall.py")
    check(not os.path.exists(startup),
          "uninstall removes its lines, and startup.py that held only them")
    check(svgs(root) == ["Mine/own.svg"] and "Kept files" in out
          and os.listdir(root) == ["Mine"]
          and [os.path.normpath(p) for p in svg_paths()] == [root],
          "a file of the user's own stays, and the folder with it")
    check(not QgsSettings().value(EMBED_KEY, False, type=bool)
          and getattr(builtins, "_emoji_san_embed_fn", None) is None,
          "uninstall disables embedding in this profile")
    check("200 symbols tagged EmOji-san" in out, "the imported symbols are "
          "mentioned")
    check(not left, "nothing is left in the console's namespace %s" % left)
    out, _ = console("uninstall.py")
    check(svgs(root) == ["Mine/own.svg"],
          "a second uninstall, now without index.csv, leaves it alone too")
    os.remove(mine)
    os.rmdir(os.path.dirname(mine))
    out, _ = console("uninstall.py")
    check(not os.path.exists(root) and not svg_paths(),
          "with the folder empty, it is removed and taken off the SVG paths")
    out, _ = console("uninstall.py")
    check("not installed" in out, "another uninstall has nothing to do")

    profile_scenarios(organization, root, archive, work, want, install)
    recovery_scenarios(organization, root, archive, work, want)
    migrated_profile_scenario(settings, root, install)
    set_upgrade_scenario(pathlib.Path(root), archive, work, want, install)
    release_scenario(root, archive, work, tag, readme, want)
    source_zip_layout_scenario(root, archive, work, source_install, want)
    offline_library_scenario(root, work, install)
    separate_legacy_embed_scenario(settings, root, archive, work, organization, install)
    old_index_recovery_scenario(root, want, install)
    startup_scenarios(settings, root, install)
    pre_registry_scenario(settings, organization, archive, work, install)


def pre_registry_scenario(settings, organization, archive, work, install):
    print("\n22. a pre-registry startup block used by two settings roots")
    startup = pathlib.Path(settings, "startup.py")
    install(EMBED=True)
    custom = "custom root"
    run_worker(organization, custom, "embed", archive, work)
    lines = startup.read_text(encoding="utf-8").splitlines(keepends=True)
    startup.write_text("".join(line for line in lines
                               if not line.startswith("# EmOji-san folders: ")),
                       encoding="utf-8")
    install(EMBED=True)
    console("uninstall.py")
    state = run_worker(organization, custom, "save", archive, work)
    check(state["enabled"] and state["connected"] and state["embedded"] == 4,
          "uninstall preserves embedding in the custom root after a fresh QGIS start")
    run_worker(organization, custom, "uninstall", archive, work)


def startup_scenarios(settings, root, install):
    print("\n21. startup.py: other folders' lines, and a file EmOji-san cannot edit")
    startup = pathlib.Path(settings, "startup.py")
    install(EMBED=True)
    other = str(pathlib.Path(settings, "custom profiles", "EmOji-san"))
    prefix = "# EmOji-san folders: "
    text = startup.read_text(encoding="utf-8")
    line = next(l for l in text.splitlines() if l.startswith(prefix))
    check(eval(line[len(prefix):]) == [str(root)], "the block records this folder")
    startup.write_text(text.replace(line, prefix + repr([str(root), other])),
                       encoding="utf-8")
    out, _ = console("uninstall.py")
    text = startup.read_text(encoding="utf-8") if startup.is_file() else ""
    check(BEGIN in text and prefix + repr([other]) in text,
          "uninstall keeps the block another EmOji-san folder still needs")
    startup.unlink()

    for label, before in (
            ("without a final newline", b"MY_SETTING = 1"),
            ("with trailing CRLF blank lines", b"MY_SETTING = 1\r\n\r\n"),
            ("with trailing LF blank lines", b"MY_SETTING = 1\n\n"),
            ("with only user whitespace", b" \n\n")):
        startup.write_bytes(before)
        install(EMBED=True)
        install(EMBED=True)
        out, _ = console("uninstall.py")
        check("EmOji-san uninstalled." in out and startup.is_file()
              and startup.read_bytes() == before,
              "last uninstall restores the original startup.py bytes " + label)
        startup.unlink()

    # the release before wrote its loader after one blank line
    before = b"MY_SETTING = 1\n"
    startup.write_bytes(before + b"\n" + legacy_startup_block(pathlib.Path(root)).encode())
    install()
    out, _ = console("uninstall.py")
    check("EmOji-san uninstalled." in out and startup.is_file()
          and startup.read_bytes() == before,
          "after an update from the release before, uninstall restores the "
          "user's lines without the blank line it added")
    startup.unlink()

    user_text = "# -*- coding: cp932 -*-\n# \u8a2d\u5b9a\nMY_SETTING = 1\n"
    cases = [("a startup.py that is not UTF-8",
              lambda: startup.write_bytes(user_text.encode("cp932")))]
    target = pathlib.Path(settings, "dotfiles", "startup.py")

    def link():
        target.parent.mkdir(exist_ok=True)
        target.write_text("MY_SETTING = 1\n", encoding="utf-8")
        startup.symlink_to(target)
    try:
        link()
        startup.unlink()
        cases.append(("a startup.py that is a link", link))
    except (OSError, NotImplementedError):
        print("  (no symbolic links here; that case is skipped)")
    for what, make in cases:
        make()
        before = startup.read_bytes()
        out, _ = install()
        check("could not be set up" not in out and svgs(root)
              and startup.read_bytes() == before,
              "%s: the install neither complains nor touches it" % what)
        out, _ = install(EMBED=True)
        check("could not be set up" in out and startup.read_bytes() == before,
              "%s: EMBED=True says why it cannot switch on" % what)
        out, _ = console("uninstall.py")
        check("uninstall stopped" not in out and "EmOji-san uninstalled." in out
              and not svgs(root).count("Travel and Places/bus.svg")
              and startup.read_bytes() == before,
              "%s: uninstall completes and leaves it as it was" % what)
        startup.unlink()


def legacy_startup_block(root):
    return ("%s\ntry:\n    with open(%r, 'rb') as _emoji_san:\n"
            "        pass\nexcept Exception:\n    pass\n%s\n"
            % (BEGIN, str(root / "embed_on_save.py"), END))


def offline_library_scenario(root, work, install):
    print("\n18. leave an independent SVG library registered")
    parent = pathlib.Path(work, "external library")
    library = parent / "EmOji-san"
    library.mkdir(parents=True)
    (library / "index.csv").write_text("another library\n", encoding="utf-8")
    icon = library / "Maps" / "custom_marker.svg"
    icon.parent.mkdir()
    shutil.copyfile(REPO / "collections/noto_emoji_map/svg/Travel and Places/bus.svg", icon)
    QgsApplication.setSvgPaths([library.as_posix()])
    qsettings = QgsSettings()
    qsettings.sync()
    saved = pathlib.Path(work, "external.qgz")
    write_relative_marker(icon, saved)
    install()
    check(library.as_posix() in svg_paths() and read_marker_path(saved).samefile(icon),
          "a same-named library with an unrelated index keeps its registration")
    disconnected = parent.with_name("disconnected library")
    parent.rename(disconnected)
    try:
        install()
        check(library.as_posix() in svg_paths(),
              "installation preserves a temporarily unavailable SVG path")
        console("uninstall.py")
        check(svg_paths() == [library.as_posix()] and not inventory(root),
              "uninstall removes only the current EmOji-san path")
    finally:
        disconnected.rename(parent)
    check(read_marker_path(saved).samefile(icon),
          "an existing QGZ finds its SVG when the independent library returns")
    QgsApplication.setSvgPaths([])
    qsettings.sync()


def separate_legacy_embed_scenario(settings, root, archive, work, organization, install):
    print("\n19. preserve old embedding when another settings root installs")
    install(EMBED=False)
    qsettings = QgsSettings()
    qsettings.remove(EMBED_KEY)
    qsettings.sync()
    startup = pathlib.Path(settings, "startup.py")
    startup.write_text("# user startup code\n" + legacy_startup_block(pathlib.Path(root)),
                       encoding="utf-8")

    def other(action):
        return run_worker(organization, "custom root", action, archive, work)

    state = other("install")
    text = startup.read_text(encoding="utf-8")
    check(state["registered"] and not state["enabled"] and not state["connected"]
          and text.startswith("# user startup code\n") and "embed_on_save.py" not in text,
          "an unrelated install stays opted out and keeps user startup code")
    state = run_worker(organization, "default", "startup-only", archive, work)
    check(state["enabled"] and state["connected"],
          "the old profile still has its opted-in hook when it starts")
    state = other("embed")
    check(state["enabled"] and state["connected"],
          "the unrelated profile can still opt in explicitly")
    other("uninstall")
    state = run_worker(organization, "default", "startup-only", archive, work)
    check(state["enabled"] and state["connected"],
          "uninstall in another settings root leaves the old opt-in working")
    qsettings.sync()
    console("uninstall.py")


def old_index_recovery_scenario(root, want, install):
    print("\n20. recover the original installation's missing CSV")
    install(SET="M", EMBED=False)
    folder = pathlib.Path(root)
    (folder / ".emoji-san-owned.json").unlink()
    (folder / "index.csv").unlink()
    # This is the generated pre-manifest README and Noto metadata footprint.
    custom_rel = min(set(want["L"]) - set(want["M"]))
    custom = folder / custom_rel
    custom.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(folder / want["S"][0], custom)
    custom_data = custom.read_bytes()
    out, _ = install()
    with (folder / "index.csv").open(encoding="utf-8", newline="") as stream:
        rebuilt = sorted(row["path"] for row in csv.DictReader(stream))
    record = json.loads((folder / ".emoji-san-owned.json").read_text(encoding="utf-8"))
    check("recovered the legacy set" in out and record["selected_set"] == "M"
          and rebuilt == want["M"] and custom_rel not in record["files"],
          "an old M install recovers its index without claiming an unrelated SVG")
    console("uninstall.py")
    check(custom.read_bytes() == custom_data and svgs(root) == [custom_rel],
          "uninstall removes recovered stock SVGs and preserves the user's SVG")
    custom.unlink()
    custom.parent.rmdir()
    console("uninstall.py")


def write_relative_marker(marker, saved):
    project = QgsProject.instance()
    project.clear()
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "legacy marker", "memory")
    symbol = QgsMarkerSymbol()
    symbol.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(str(marker), 8))
    layer.renderer().setSymbol(symbol)
    project.addMapLayer(layer)
    try:
        assert project.write(str(saved)), saved
    finally:
        project.clear()
    with zipfile.ZipFile(saved) as archive:
        xml = archive.read(next(n for n in archive.namelist() if n.endswith(".qgs")))
    ref = "%s/%s" % (marker.parent.name, marker.name)
    assert b'"base64:' not in xml and ('"%s"' % ref).encode() in xml, ref


def read_marker_path(saved):
    project = QgsProject.instance()
    project.clear()
    try:
        assert project.read(str(saved)), saved
        layer = project.mapLayersByName("legacy marker")[0]
        return pathlib.Path(layer.renderer().symbol().symbolLayer(0).path())
    finally:
        project.clear()


def version_migration_scenario(settings, root, archive, work, organization, want):
    print("\n10. a migrated QGIS profile keeps M when its destination already has S")
    versions = pathlib.Path(settings, "version migration")
    legacy = versions / "QGIS3" / "EmOji-san"
    destination = versions / "QGIS4" / "EmOji-san"
    legacy.parent.mkdir(parents=True)
    shutil.copytree(root, legacy)
    # P1's ownership record did not record the selected set.
    manifest = legacy / ".emoji-san-owned.json"
    record = json.loads(manifest.read_text(encoding="utf-8"))
    record.pop("selected_set")
    manifest.write_text(json.dumps(record), encoding="utf-8")
    (legacy.parent / "startup.py").write_text(legacy_startup_block(legacy),
                                              encoding="utf-8")
    original = inventory(legacy)
    rel = pathlib.Path("Animals and Nature", "dog.svg")
    saved = pathlib.Path(work, "migration marker.qgz")
    qsettings = QgsSettings()
    embedding = qsettings.value(EMBED_KEY, False, type=bool)
    qsettings.setValue(EMBED_KEY, False)
    try:
        write_relative_marker(pathlib.Path(root) / rel, saved)
    finally:
        qsettings.setValue(EMBED_KEY, embedding)

    def migrated(action):
        return run_worker(organization, "migrated profile", action, archive, work)

    state = migrated("migration-check")
    check(state["check_reports_old"] and state["marker"] == str(legacy / rel),
          "check points at the older copy and the old QGZ still opens from it")
    run_worker(organization, "destination profile", "install-small", archive, work)
    check(svgs(destination) == want["S"] and not (destination / rel).exists(),
          "another profile has already installed S in the new settings folder")
    state = migrated("migrate")
    check(state["paths"] == [destination.as_posix()] and svgs(destination) == want["M"],
          "migration installs M and re-registers the new copy for this profile")
    check(state["marker"] == str(destination / rel)
          and (destination / rel).read_bytes() == (legacy / rel).read_bytes()
          and inventory(legacy) == original,
          "the old QGZ resolves the original marker and the old files stay")
    check(state["enabled"] and state["connected"],
          "the legacy embedding opt-in survives migration into a populated root")
    personal = legacy / "Mine" / "own.svg"
    personal.parent.mkdir()
    shutil.copyfile(legacy / rel, personal)
    migrated("migration-check")
    state = migrated("migrate")
    check(state["paths"] == [destination.as_posix(), legacy.as_posix()]
          and personal.is_file() and state["marker"] == str(destination / rel),
          "a migrated path with unmanaged SVGs remains available as a fallback")
    migrated("uninstall")
    run_worker(organization, "destination profile", "uninstall", archive, work)


def migrated_profile_scenario(settings, root, install):
    print("\n14. a migrated QGIS profile still uses the older SVG path")
    home = pathlib.Path(settings)
    peer_version = "QGIS4" if home.name == "QGIS3" else "QGIS3"
    peer_home = home.with_name(peer_version)
    assert not peer_home.exists(), peer_home
    profile = pathlib.Path(QgsApplication.qgisSettingsDirPath()).resolve()
    relative_ini = pathlib.Path(QSettings().fileName()).resolve().relative_to(profile)
    peer_ini = peer_home / "profiles" / "migrated" / relative_ini.with_name(
        peer_version + ".ini")
    peer_ini.parent.mkdir(parents=True)
    try:
        peer = QSettings(str(peer_ini), QSettings.Format.IniFormat)
        peer.setValue("svg/searchPathsForSVG", [root.replace(os.sep, "/")])
        peer.sync()
        install(SET="M")
        before = inventory(root)
        out, _ = install(SET="S")
        check(bool(before) and inventory(root) == before and "shared SVGs" in out,
              "downgrade preserves assets referenced by a migrated profile")
        console("uninstall.py")
        check(not svg_paths() and inventory(root) == before,
              "uninstall preserves assets referenced by a migrated profile")
    finally:
        shutil.rmtree(str(peer_home))
    console("uninstall.py")
    check(not inventory(root), "the unreferenced old copy can be removed")


def set_upgrade_scenario(root, archive, work, want, install):
    print("\n15. an older project's SVGs and selected set survive an update")
    demoted = "Travel and Places/bus.svg"
    removed = "Symbols/warning.svg"
    installed_fields = ["emoji", "codepoint", "name", "category", "path",
                        "set", "noto_file"]
    future = os.path.join(work, "next-release.zip")
    with zipfile.ZipFile(archive) as previous:
        index_name = next(name for name in previous.namelist()
                          if name.endswith("/index.csv"))
        top = index_name[:-len("index.csv")]
        catalog = csv.DictReader(io.StringIO(
            previous.read(index_name).decode("utf-8")))
        rows = list(catalog)
        old = [row for row in rows if row["set"] == "S"]
        root.mkdir()
        for row in old:
            dst = root / row["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(previous.read("%scollections/noto_emoji_%s/svg/%s"
                                          % (top, row["collection"], row["path"])))
        # The original installer recorded the deployed rows without a chosen
        # set field or a separate ownership manifest.
        with (root / "index.csv").open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, installed_fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(old)

        updated = io.StringIO(newline="")
        writer = csv.DictWriter(updated, catalog.fieldnames)
        writer.writeheader()
        removed_member = next("%scollections/noto_emoji_%s/svg/%s"
                              % (top, row["collection"], removed)
                              for row in old if row["path"] == removed)
        for row in rows:
            if row["path"] == demoted:
                row["set"] = "L"
            if row["path"] != removed:
                writer.writerow(row)
        with zipfile.ZipFile(future, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr(index_name, updated.getvalue())
            for name in previous.namelist():
                if name not in (index_name, removed_member):
                    output.writestr(name, previous.read(name))

    QgsApplication.setSvgPaths([root.as_posix()])
    QgsSettings().sync()
    project = QgsProject.instance()
    project.clear()
    saved = os.path.join(work, "older-project.qgz")
    expected = {}
    for rel in (demoted, removed):
        path = root / rel
        layer = QgsVectorLayer("Point?crs=EPSG:4326", rel, "memory")
        symbol = QgsMarkerSymbol()
        symbol.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(str(path), 8))
        layer.renderer().setSymbol(symbol)
        project.addMapLayer(layer)
        expected[rel] = (path.read_bytes(), symbol.asImage(QSize(64, 64)))
    assert project.write(saved), saved
    project.clear()
    with zipfile.ZipFile(saved) as project_zip:
        xml = project_zip.read(next(n for n in project_zip.namelist()
                                    if n.endswith(".qgs"))).decode("utf-8")
    check("base64:" not in xml and all('"%s"' % rel in xml for rel in expected),
          "the old QGZ stores unembedded, relative SVG references")

    def paths_resolve():
        if not project.read(saved):
            return False
        try:
            for rel, (data, image) in expected.items():
                layers = project.mapLayersByName(rel)
                if not layers:
                    return False
                symbol = layers[0].renderer().symbol()
                path = pathlib.Path(symbol.symbolLayer(0).path())
                original = root / rel
                if (not original.is_file() or not path.is_file()
                        or not path.samefile(original)
                        or path.read_bytes() != data
                        or symbol.asImage(QSize(64, 64)) != image):
                    return False
            return True
        finally:
            project.clear()

    def selection():
        manifest = root / ".emoji-san-owned.json"
        if manifest.is_file():
            return json.loads(manifest.read_text(encoding="utf-8")).get("selected_set")
        return None

    new_small = sorted(set(want["S"]) - set(expected))
    install(ZIP=future)
    with (root / "index.csv").open(encoding="utf-8", newline="") as file:
        listed = sorted(row["path"] for row in csv.DictReader(file))
    check(selection() == "S" and listed == new_small and svgs(root) == want["S"],
          "omitting SET keeps the selection inferred from the previous index")
    check(paths_resolve(),
          "reopening the older QGZ resolves and draws both original SVGs")
    before = inventory(root)
    install(ZIP=future)
    install(ZIP=future, SET="S")
    check(inventory(root) == before and paths_resolve(),
          "repeating the update and specifying the same set preserve SVGs")
    install(ZIP=future, SET="L")
    check(selection() == "L" and svgs(root) == want["L"] and paths_resolve(),
          "explicitly upgrading keeps the legacy SVG missing from the archive")
    install(ZIP=future, SET="S")
    check(selection() == "S" and svgs(root) == new_small,
          "only a requested downgrade removes compatibility SVGs")
    console("uninstall.py")
    check(not inventory(root), "the updated installation can be uninstalled")


def release_scenario(root, archive, work, tag, readme, want):
    print("\n16. the published one-line installer verifies the release data")
    release_dir = pathlib.Path(work, "release-assets")
    subprocess.run([sys.executable, str(REPO / "build" / "make_release.py"),
                    str(release_dir)], check=True, timeout=120)
    release = "https://github.com/yfuru2454/emoji-san/releases/download/v%s/" % tag
    install_url = release + "install.py"
    data_url = release + "emoji_san_data.zip"
    payload = (release_dir / "emoji_san_data.zip").read_bytes()
    with zipfile.ZipFile(io.BytesIO(payload)) as data:
        check(not any(name.endswith(".py") for name in data.namelist()),
              "the generated release data ZIP has no Python code")
    installer = (release_dir / "install.py").read_bytes()
    lines = re.findall(r"^ {0,3}(import urllib\.request as u; exec\(.*"
                       + re.escape(install_url) + r".*)$", readme, flags=re.M)
    check(len(lines) == 2 and len(set(lines)) == 1,
          "both README sections have the same one-line release installer")
    if not lines:
        return

    def request_release(asset, options=""):
        responses = {install_url: installer, data_url: asset}
        visited = []

        def download(request, timeout=None):
            url = getattr(request, "full_url", request)
            visited.append(url)
            response = responses[url]
            if response is None:
                raise urllib.error.URLError("no network in this test")
            return io.BytesIO(response)

        with unittest.mock.patch("urllib.request.urlopen", download):
            out, left = console("LOCALE='en'; " + options + lines[0])
        return out, left, visited

    _, left, visited = request_release(payload)
    check(visited == [install_url, data_url] and left == ["u"]
          and svgs(root) == want["S"],
          "the one-liner installs the matching release data")
    before = inventory(root)
    # Another valid archive still must match the checksum in the installer.
    out, _, visited = request_release(pathlib.Path(archive).read_bytes(), "SET='L'; ")
    check(visited == [install_url, data_url]
          and "sha-256" in out.lower() and inventory(root) == before,
          "a different valid ZIP is refused without changing the installation")
    out, _, visited = request_release(None, "SET='L'; ")
    check(visited == [install_url, data_url] and inventory(root) == before
          and "could not get the files (URLError" in out
          and "#without-internet-access-from-qgis" in out
          and "\n## Without internet access from QGIS\n" in readme,
          "a download failure preserves the installation and points to the offline steps")
    offline = re.findall(r"^from pathlib import Path; ZIP='/path/to/emoji_san_data\.zip'; .+$",
                         readme, flags=re.M)
    check(len(offline) == 2 and len(set(offline)) == 1,
          "both README sections have the same offline release installer")
    if offline:
        line = offline[0].replace("'/path/to/emoji_san_data.zip'",
                                  repr(str(release_dir / "emoji_san_data.zip")))
        line = line.replace("'/path/to/install.py'", repr(str(release_dir / "install.py")))
        with unittest.mock.patch("urllib.request.urlopen") as network:
            out, left = console(line)
        check(not network.called and left == ["Path"]
              and "EmOji-san S:" in out and inventory(root) == before,
              "the documented offline command verifies the downloaded release data")
    console("uninstall.py")
    check(not inventory(root), "the generated release can be uninstalled")


def source_zip_layout_scenario(root, archive, work, install, want):
    print("\n17. the documented offline line accepts repacked source ZIPs")

    def repack(filename, prefixes):
        path = pathlib.Path(work, filename)
        with zipfile.ZipFile(archive) as source, zipfile.ZipFile(
                path, "w", zipfile.ZIP_DEFLATED) as target:
            for member in source.namelist():
                _, _, relative = member.partition("/")
                data = source.read(member)
                for prefix in prefixes:
                    target.writestr(prefix + relative, data)
        return path

    renamed = repack("絵文字 ソース.zip", ("絵文字 改名フォルダ/",))
    with unittest.mock.patch("urllib.request.urlopen") as network:
        out, left = install(renamed, "SET='M'; EMBED=True; ")
    check(not network.called and not left and "EmOji-san M:" in out
          and svgs(root) == want["M"] and "on save: on" in out
          and QgsSettings().value(EMBED_KEY, False, type=bool),
          "the renamed folder installs offline with SET and EMBED preserved")
    console("uninstall.py")

    flat = repack("flat source.zip", ("",))
    with unittest.mock.patch("urllib.request.urlopen") as network:
        out, left = install(flat)
    check(not network.called and not left and "EmOji-san S:" in out
          and svgs(root) == want["S"],
          "the offline line installs with the installer at the ZIP root")

    original = inventory(root)
    paths = svg_paths()
    ambiguous = repack("two source copies.zip", ("source one/", "source two/"))
    error = ""
    with unittest.mock.patch("urllib.request.urlopen") as network:
        try:
            install(ambiguous)
        except ValueError as exception:
            error = str(exception)
    check("Expected one install.py" in error and not network.called
          and inventory(root) == original and svg_paths() == paths,
          "two source copies are refused before changing the installation")
    console("uninstall.py")


def inventory(root):
    """Files and their bytes, including the CSV and ownership metadata."""
    root = pathlib.Path(root)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).digest()
            for p in root.rglob("*") if p.is_file()}


def run_worker(organization, profile, action, archive, work, expected=0):
    result = subprocess.run(
        [sys.executable, str(pathlib.Path(__file__).resolve()), "--worker",
         organization, profile, action, archive, work],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        encoding="utf-8", timeout=120,
        env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if result.returncode != expected:
        raise RuntimeError("QGIS worker %s/%s exited %d (expected %d):\n%s"
                           % (profile, action, result.returncode, expected,
                              result.stdout))
    if expected == 0:
        for line in result.stdout.splitlines():
            if line.startswith("Worker state: "):
                return json.loads(line.split(": ", 1)[1])
        raise RuntimeError("No state from QGIS worker:\n" + result.stdout)
    return {}


def profile_scenarios(organization, root, archive, work, want, install):
    print("\n12. two user profiles share SVGs, with independent embedding")
    install(SET="M", EMBED=False)

    def second(action):
        return run_worker(organization, "second profile", action,
                          archive, work)

    state = second("install")
    check(state["registered"] and not state["connected"]
          and not state["enabled"] and svgs(root) == want["M"],
          "the second profile shares M and has not opted in")
    state = second("embed")
    check(state["enabled"] and state["connected"]
          and not QgsSettings().value(EMBED_KEY, False, type=bool)
          and getattr(builtins, "_emoji_san_embed_fn", None) is None,
          "enabling embedding only changes the second profile")
    state = second("save")
    check(state["connected"] and state["embedded"] == 4,
          "a fresh QGIS process in the second profile embeds on save")

    before = inventory(root)
    install(SET="S")
    check(inventory(root) == before,
          "a downgrade preserves the SVGs used by the second profile")
    console("uninstall.py")
    state = second("save")
    check(not svg_paths() and state["registered"] and state["enabled"]
          and state["connected"] and state["embedded"] == 4
          and inventory(root) == before,
          "uninstall in the first profile keeps the second profile working")
    check(not QgsSettings().value(EMBED_KEY, False, type=bool),
          "the first profile stays opted out")
    state = second("uninstall")
    check(not state["registered"] and not state["connected"]
          and not state["enabled"] and not inventory(root),
          "uninstall in the last profile removes the shared installation")


def recovery_scenarios(organization, root, archive, work, want):
    print("\n13. recover an interrupted update")

    def recovery(action, expected=0):
        return run_worker(organization, "recovery", action, archive, work,
                          expected)

    recovery("install-small")
    before = inventory(root)
    check(svgs(root) == want["S"], "recovery starts with a complete S set")
    for action in ("io-error", "interrupt"):
        state = recovery(action)
        check(state["injected"] and state["registered"]
              and inventory(root) == before,
              "%s after a live write restores every file and the old index"
              % action)

    recovery("process-exit", CRASH_EXIT)
    interrupted = inventory(root)
    check(interrupted["index.csv"] != before["index.csv"]
          and svgs(root) == want["L"],
          "the process stopped after writing the new SVGs and index")
    state = recovery("install")
    check(state["registered"] and inventory(root) == before,
          "a fresh QGIS run recovers the interrupted update and keeps S")
    recovery("install-large")
    check(svgs(root) == want["L"],
          "the same profile can complete an upgrade after recovery")
    recovery("uninstall")
    check(not inventory(root), "a recovered install can be uninstalled")


def profile_worker(organization, profile, action, archive, work):
    app, settings = test_app(organization, profile)
    root = pathlib.Path(QgsApplication.qgisSettingsDirPath()).parent.parent / "EmOji-san"
    startup = pathlib.Path(settings, "startup.py")
    state = {}
    try:
        if startup.is_file():
            exec(compile(startup.read_bytes(), str(startup), "exec"),
                 {"__name__": "startup"})
        if action == "uninstall":
            console("uninstall.py")
        elif action == "migration-check":
            legacy = root.parent.with_name("QGIS3") / "EmOji-san"
            QgsApplication.setSvgPaths([legacy.as_posix()])
            QgsSettings().sync()
            out, _ = console("tests/check_install.py", DEMO=False)
            state["check_reports_old"] = ("this QGIS still uses" in out
                                          and "PROBLEMS FOUND" in out)
            state["marker"] = str(read_marker_path(pathlib.Path(work, "migration marker.qgz")))
        elif action == "migrate":
            console("install.py", ZIP=archive, LOCALE="en")
            state["marker"] = str(read_marker_path(pathlib.Path(work, "migration marker.qgz")))
        elif action == "save":
            saved = save_project(str(root), os.path.join(work, "profile.qgs"))
            state["embedded"] = saved["embedded"]
        elif action in ("io-error", "interrupt", "process-exit"):
            replacements = 0
            injected = False
            replace = os.replace

            def replace_with_interruption(source, dest, *args, **kwargs):
                nonlocal replacements, injected
                path = pathlib.Path(dest)
                active_svg = path.suffix == ".svg" and root in path.parents
                if active_svg and replacements and not injected:
                    injected = True
                    if action == "io-error":
                        raise OSError("simulated write failure")
                    if action == "interrupt":
                        raise KeyboardInterrupt()
                replace(source, dest, *args, **kwargs)
                if active_svg:
                    replacements += 1
                if action == "process-exit" and path == root / "index.csv":
                    os._exit(CRASH_EXIT)

            with unittest.mock.patch("os.replace", replace_with_interruption):
                try:
                    console("install.py", ZIP=archive, LOCALE="en", SET="L")
                except (OSError, KeyboardInterrupt):
                    if not injected:
                        raise
            state["injected"] = injected and replacements > 0
        elif action != "startup-only":
            console("install.py", ZIP=archive, LOCALE="en",
                    SET={"install-small": "S", "install-large": "L"}.get(action),
                    EMBED={"embed": True, "disable": False}.get(action))
        state.update(
            registered=any(pathlib.Path(p) == root for p in svg_paths()),
            paths=svg_paths(),
            enabled=QgsSettings().value(EMBED_KEY, False, type=bool),
            connected=getattr(builtins, "_emoji_san_embed_fn", None) is not None)
        QgsSettings().sync()
    finally:
        QgsProject.instance().clear()
        app.exitQgis()
    print("Worker state: " + json.dumps(state))


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


def check_mixed_svg_project(root, path):
    """Save and reopen a QGZ with a fixed marker and an expression marker."""
    project = QgsProject.instance()
    project.clear()
    fixed = pathlib.Path(root, "Travel and Places", "bus.svg")
    external = pathlib.Path(root, "Symbols", "warning.svg")
    expression = QgsExpression.quotedString(external.as_posix())
    try:  # QGIS 3.36 and later
        name_property = QgsSymbolLayer.Property.Name
    except AttributeError:  # QGIS 3.34
        name_property = QgsSymbolLayer.PropertyName
    dynamic = QgsSvgMarkerSymbolLayer("", 8)
    dynamic.setDataDefinedProperty(name_property,
                                   QgsProperty.fromExpression(expression))
    symbol = QgsMarkerSymbol()
    symbol.changeSymbolLayer(0, QgsSvgMarkerSymbolLayer(str(fixed), 8))
    symbol.appendSymbolLayer(dynamic)
    layer = QgsVectorLayer("Point?crs=EPSG:4326", "mixed SVG markers", "memory")
    layer.renderer().setSymbol(symbol)
    project.addMapLayer(layer)
    try:
        assert project.write(path), path
        project.clear()
        with zipfile.ZipFile(path) as saved:
            xml = saved.read(next(n for n in saved.namelist() if n.endswith(".qgs")))
        assert project.read(path), path
        layer = project.mapLayersByName("mixed SVG markers")[0]
        reloaded = layer.renderer().symbol()
        first = reloaded.symbolLayer(0).path()
        second = reloaded.symbolLayer(1).dataDefinedProperties().property(name_property)
        value, ok = second.valueAsString(QgsExpressionContext())
        check(xml.count(b'"base64:') == 1 and first.startswith("base64:")
              and base64.b64decode(first[len("base64:"):]) == fixed.read_bytes(),
              "the QGZ embeds the fixed SVG and reopens with the correct drawing")
        check(second.isActive() and second.expressionString() == expression and ok
              and pathlib.Path(value).is_file() and pathlib.Path(value).samefile(external),
              "the QGZ preserves the active expression and its external SVG path")
    finally:
        project.clear()


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--worker":
        profile_worker(*sys.argv[2:])
        sys.exit(0)
    sys.exit(main())
