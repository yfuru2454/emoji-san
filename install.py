# -*- coding: utf-8 -*-
"""EmOji-san — install Google Noto Emoji as QGIS SVG marker symbols.

(Yes, there is an Oji-san hiding in the name.)

Paste into the QGIS Python console (Plugins > Python Console), or run
via the one-liner in README.md. No plugin, no dependencies, works on
Windows / macOS / Linux with any QGIS 3.x.

One HTTP request: downloads this repository's tagged archive (a few MB),
extracts the emoji SVGs into <QGIS3 settings folder>/EmOji-san/<Category>/
and registers that folder as an SVG path (Settings > Options > System >
SVG paths). The SVG browser then shows an "EmOji-san" group with one
sub-group per category, loading one category at a time.

Default: ~1,060 map-friendly emoji (Animals & Nature, Food & Drink,
Travel & Places, Activities, Objects, Symbols) — the standard set you
know from iPhone/Android keyboards, in Google's Noto design, without
skin-tone variants.

Full set (adds Smileys & Emotion, People & Body, 8 generic flags) —
the QGIS console takes ONE line at a time, so join with a semicolon:

    FULL = True; import urllib.request as u; exec(...)  # same line

Also installs index.csv next to the SVGs: one row per emoji with its
codepoint, English name, a name in your QGIS language (Unicode CLDR,
~100 languages), category and path. Scripts and AI agents (e.g. QGIS
assistants) can look an emoji up there instead of guessing file names.

License of the artwork: Apache-2.0 (a copy is installed alongside).
"""
import csv
import io
import json
import os
import shutil
import urllib.request
import zipfile

REPO = "yfuru2454/emoji-san"
TAG = "v1.0.0"
SETTINGS_KEY = "svg/searchPathsForSVG"
CLDR = ("https://raw.githubusercontent.com/unicode-org/cldr-json/49.0.0/"
        "cldr-json/")

# --- options (set as variables before exec'ing, if you like) ----------
_g = globals()
FULL = bool(_g.get("FULL", False))      # FULL=True -> people/faces too
LOCALE = _g.get("LOCALE", None)         # e.g. "de"; default: QGIS's own
ZIP_URL = _g.get("ZIP_URL",             # override for testing/mirrors
                 "https://github.com/%s/archive/refs/tags/%s.zip"
                 % (REPO, TAG))
# ----------------------------------------------------------------------

MARKERS = ["/collections/noto_emoji_map/svg/"]
if FULL:
    MARKERS.append("/collections/noto_emoji_people/svg/")


def _paths():
    """(install root, legacy location inside the profile's svg folder)."""
    try:
        from qgis.core import QgsApplication
        profile = QgsApplication.qgisSettingsDirPath()
    except ImportError:  # outside QGIS: write to cwd for inspection
        profile = os.path.abspath(os.path.join("qgis_test", "profiles",
                                               "default"))
    profile = os.path.normpath(profile)
    # <QGIS3>/profiles/<name>  ->  <QGIS3>/EmOji-san
    # Outside the profile, so the SVG browser labels the group "EmOji-san"
    # (paths inside a profile are all shown as "User Symbols"), and one
    # copy serves every profile.
    qgis3 = os.path.dirname(os.path.dirname(profile))
    return (os.path.join(qgis3, "EmOji-san"),
            os.path.join(profile, "svg", "EmOji-san"))


def _register(root):
    """Add root to the SVG search paths, once. Returns True if added."""
    try:
        from qgis.core import QgsSettings
    except ImportError:
        return False
    s = QgsSettings()
    cur = s.value(SETTINGS_KEY, [])
    if isinstance(cur, str):
        cur = [cur] if cur else []
    cur = [p for p in (cur or []) if p]
    norm = [os.path.normpath(p) for p in cur]
    if os.path.normpath(root) in norm:
        return False
    s.setValue(SETTINGS_KEY, cur + [root])
    return True


def _qgis_locale():
    if LOCALE:
        return str(LOCALE)
    try:
        from qgis.core import QgsApplication
        loc = QgsApplication.locale()
        if loc:
            return loc
    except Exception:
        pass
    try:
        from qgis.PyQt.QtCore import QLocale
        return QLocale().name()
    except Exception:
        return "en"


def _cldr_names(loc):
    """{emoji: name} in the given locale from Unicode CLDR, or {}."""
    loc = loc.replace("_", "-")
    lang = loc.split("-")[0].lower()
    if lang == "en":
        return lang, {}
    tries = [loc, lang]
    if lang == "zh" and loc.upper().endswith(("TW", "HK", "MO", "HANT")):
        tries.insert(0, "zh-Hant")
    for code in tries:
        names = {}
        try:
            for pkg, key in (("annotations-full", "annotations"),
                             ("annotations-derived-full",
                              "annotationsDerived")):
                url = "%scldr-%s/%s/%s/annotations.json" % (CLDR, pkg, key,
                                                            code)
                d = json.loads(urllib.request.urlopen(url, timeout=60).read())
                for k, v in d[key]["annotations"].items():
                    if v.get("tts"):
                        names[k] = v["tts"][0]
        except Exception:
            continue
        if names:
            return code, names
    return lang, {}


def _write_index(root, index_bytes):
    """index.csv for the files actually installed, + local-language names."""
    rows = list(csv.DictReader(io.StringIO(index_bytes.decode("utf-8"))))
    rows = [r for r in rows
            if os.path.exists(os.path.join(root, *r["path"].split("/")))]
    code, names = _cldr_names(_qgis_locale())
    fields = ["emoji", "codepoint", "name"]
    if names:
        col = "name_" + code
        fields.append(col)
        for r in rows:
            e = r["emoji"]
            r[col] = names.get(e) or names.get(e.replace("️", "")) or ""
    fields += ["category", "path", "noto_file"]
    with open(os.path.join(root, "index.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(root, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            "EmOji-san: Google Noto Emoji (Apache-2.0) as QGIS SVG markers.\n"
            "This folder is registered as a QGIS SVG path. index.csv lists\n"
            "every emoji: 'path' is relative to this folder, the same form\n"
            "QGIS stores in projects (e.g. 'Food and Drink/hot_beverage.svg')."
            "\n%s\nhttps://github.com/%s\n" % (
                ("'%s' holds names in this QGIS's language (Unicode CLDR)."
                 % ("name_" + code)) if names else "", REPO))
    return len(rows), ("name_" + code) if names else None


def main():
    root, legacy = _paths()
    if os.path.isdir(legacy):  # v0 test installs put it inside svg/
        shutil.rmtree(legacy)
        print("  removed old location:", legacy)

    print("EmOji-san — downloading %s ..." % ZIP_URL)
    data = urllib.request.urlopen(ZIP_URL, timeout=120).read()
    print("  %.1f MB, extracting ..." % (len(data) / 1e6))

    n, index_bytes = 0, None
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir() or ".." in name:
                continue
            if name.count("/") == 1 and name.endswith("/index.csv"):
                index_bytes = z.read(info)  # top-level index.csv
                continue
            if name.endswith("/LICENSE-noto-emoji.txt") or \
                    name.endswith("/UPSTREAM_COMMIT.txt"):
                rel = os.path.basename(name)
            else:
                for m in MARKERS:
                    if m in name and name.endswith(".svg"):
                        rel = name.split(m, 1)[1]
                        break
                else:
                    continue
            dest = os.path.join(root, *rel.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "wb") as f:
                f.write(z.read(info))
            n += 1

    added = _register(root)
    msg = "EmOji-san: %d files installed -> %s" % (n, root)
    print(msg)
    if index_bytes:
        rows, col = _write_index(root, index_bytes)
        print("  index.csv: %d emoji%s" % (
            rows, (" (+ %s)" % col) if col else ""))
    if added:
        print("  registered as an SVG path (Settings > Options > System)")
    print("Use: layer symbology > Marker > SVG Marker > SVG Browser > "
          "'EmOji-san' group (reopen the dialog if it was open).")
    if not FULL:
        print("Want faces & people too? Paste:  FULL = True; "
              "<the same one-liner>")
    try:
        from qgis.utils import iface
        if iface:
            iface.messageBar().pushSuccess("EmOji-san", msg)
    except Exception:
        pass


main()
