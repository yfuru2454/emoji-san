# -*- coding: utf-8 -*-
"""EmOji-san — install Google Noto Emoji as QGIS SVG marker symbols.

(Yes, there is an Oji-san hiding in the name.)

Paste into the QGIS Python console (Plugins > Python Console). Works on
Windows / macOS / Linux with any QGIS 3.x. No plugin, no dependencies.

Choose a size (the QGIS console takes ONE line, so join with ";"):

    import urllib.request as u; exec(...)            # S:   200 (default)
    SET='M'; import urllib.request as u; exec(...)   # M: 1,109
    SET='L'; import urllib.request as u; exec(...)   # L: 1,595

The sets nest (S < M < L), so you can run it again with another SET at
any time:
  - upgrade:   adds the missing emoji, keeps everything you have
  - downgrade: removes the emoji that are not in the smaller set
               (maps using those show a "?" marker until you upgrade)

Files go to <QGIS3 settings folder>/EmOji-san/<Category>/, which is
registered as an SVG path (Settings > Options > System > SVG paths).
index.csv lists every installed emoji with its codepoint, English name,
a name in your QGIS language (Unicode CLDR), category, path and set.

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
SETS = ["S", "M", "L"]
DEFAULT_SET = "S"
ALIASES = {"s": "S", "basic": "S", "lite": "S", "small": "S",
           "m": "M", "advanced": "M", "map": "M", "medium": "M",
           "l": "L", "full": "L", "large": "L"}

# --- options (set as variables before exec'ing, if you like) ----------
_g = globals()
SET = str(_g.get("SET") or ("L" if _g.get("FULL") else DEFAULT_SET))
SET = ALIASES.get(SET.strip().lower(), SET.strip())
LOCALE = _g.get("LOCALE", None)         # e.g. "de"; default: QGIS's own
ZIP_URL = _g.get("ZIP_URL",             # override for testing/mirrors
                 "https://github.com/%s/archive/refs/tags/%s.zip"
                 % (REPO, TAG))
# ----------------------------------------------------------------------

SVG_DIRS = ("/collections/noto_emoji_map/svg/",
            "/collections/noto_emoji_people/svg/")


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
    if os.path.normpath(root) in [os.path.normpath(p) for p in cur]:
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
    """(code, {emoji: name}) in the given locale from Unicode CLDR."""
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


def _write_index(root, rows):
    """index.csv for the installed emoji, + local-language names."""
    code, names = _cldr_names(_qgis_locale())
    fields = ["emoji", "codepoint", "name"]
    col = None
    if names:
        col = "name_" + code
        fields.append(col)
        for r in rows:
            e = r["emoji"]
            r[col] = names.get(e) or names.get(e.replace("️", "")) or ""
    fields += ["category", "path", "set", "noto_file"]
    with open(os.path.join(root, "index.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(root, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            "EmOji-san: Google Noto Emoji (Apache-2.0) as QGIS SVG markers.\n"
            "Installed set: %s (%d emoji). This folder is registered as a\n"
            "QGIS SVG path. index.csv lists every installed emoji: 'path'\n"
            "is relative to this folder, the same form QGIS stores in\n"
            "projects (e.g. 'Food and Drink/hot_beverage.svg').\n%s"
            "https://github.com/%s\n" % (
                SET, len(rows),
                ("'%s' holds names in this QGIS's language (Unicode CLDR)."
                 "\n" % col) if col else "", REPO))
    return col


def main():
    if SET not in SETS:
        print("EmOji-san: unknown SET %r — use 'S', 'M' or 'L'" % SET)
        return
    root, legacy = _paths()
    if os.path.isdir(legacy):  # early test installs put it inside svg/
        shutil.rmtree(legacy)
        print("  removed old location:", legacy)

    print("EmOji-san — downloading %s ..." % ZIP_URL)
    data = urllib.request.urlopen(ZIP_URL, timeout=120).read()
    z = zipfile.ZipFile(io.BytesIO(data))

    # which emoji belong to the chosen set (sets nest: basic < adv < full)
    names = z.namelist()
    index_name = next(n for n in names
                      if n.count("/") == 1 and n.endswith("/index.csv"))
    rows = list(csv.DictReader(
        io.StringIO(z.read(index_name).decode("utf-8"))))
    rank = SETS.index(SET)
    rows = [r for r in rows if SETS.index(r["set"]) <= rank]
    want = {r["path"] for r in rows}

    # zip members by their path relative to the install root
    members = {}
    for n in names:
        for d in SVG_DIRS:
            if d in n and n.endswith(".svg") and ".." not in n:
                members[n.split(d, 1)[1]] = n
    for n in names:
        if n.count("/") == 1 and n.endswith(("/LICENSE-noto-emoji.txt",
                                             "/UPSTREAM_COMMIT.txt")):
            members[os.path.basename(n)] = n

    # add what is missing (and refresh what is there)
    added = 0
    for rel in sorted(want) + ["LICENSE-noto-emoji.txt",
                               "UPSTREAM_COMMIT.txt"]:
        dest = os.path.join(root, *rel.split("/"))
        if rel not in members:
            continue
        existed = os.path.exists(dest)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(z.read(members[rel]))
        added += 0 if existed or not rel.endswith(".svg") else 1

    # remove SVGs that are not in the chosen set (downgrade), then
    # empty category folders. Only .svg files inside our own folder.
    removed = 0
    for dp, dn, fn in os.walk(root, topdown=False):
        for f in fn:
            if not f.endswith(".svg"):
                continue
            rel = os.path.relpath(os.path.join(dp, f), root).replace(
                os.sep, "/")
            if rel not in want:
                os.remove(os.path.join(dp, f))
                removed += 1
        if dp != root and not os.listdir(dp):
            os.rmdir(dp)

    col = _write_index(root, rows)
    newly = _register(root)
    msg = "EmOji-san %s: %d emoji (+%d added, -%d removed) -> %s" % (
        SET, len(rows), added, removed, root)
    print(msg)
    print("  index.csv%s" % ((" (+ %s)" % col) if col else ""))
    if newly:
        print("  registered as an SVG path (Settings > Options > System)")
    if removed:
        print("  note: maps that used the removed emoji show '?' until you "
              "install a larger set again")
    print("Use: layer symbology > SVG Marker > SVG browser > EmOji-san > "
          "a category (reopen the dialog if it was open).")
    bigger = SETS[rank + 1:]
    if bigger:
        print("More emoji: put  SET='%s';  in front of the same line "
              "(S 200 / M 1,109 / L 1,595)." % bigger[0])
    try:
        from qgis.utils import iface
        if iface:
            iface.messageBar().pushSuccess("EmOji-san", msg)
    except Exception:
        pass


main()
