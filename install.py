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

    FULL = True; exec(<the same one-liner>)

License of the artwork: Apache-2.0 (a copy is installed alongside).
"""
import io
import os
import shutil
import urllib.request
import zipfile

REPO = "yfuru2454/emoji-san"
TAG = "v1.0.0"
SETTINGS_KEY = "svg/searchPathsForSVG"

# --- options (set as variables before exec'ing, if you like) ----------
_g = globals()
FULL = bool(_g.get("FULL", False))      # FULL=True -> people/faces too
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


def main():
    root, legacy = _paths()
    if os.path.isdir(legacy):  # v0 test installs put it inside svg/
        shutil.rmtree(legacy)
        print("  removed old location:", legacy)

    print("EmOji-san — downloading %s ..." % ZIP_URL)
    data = urllib.request.urlopen(ZIP_URL, timeout=120).read()
    print("  %.1f MB, extracting ..." % (len(data) / 1e6))

    n = 0
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir() or ".." in name:
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
