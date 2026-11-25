# -*- coding: utf-8 -*-
"""EmOji-san — install Google Noto Emoji as QGIS SVG marker symbols.

(Yes, there is an Oji-san hiding in the name.)

Paste into the QGIS Python console (Plugins > Python Console), or run
via the one-liner in README.md. No plugin, no dependencies, works on
Windows / macOS / Linux with any QGIS 3.x.

One HTTP request: downloads this repository's tagged archive (a few MB)
and extracts the emoji SVGs into your QGIS profile at
svg/EmOji-san/<Category>/ , which QGIS scans automatically.

Default: ~1,060 map-friendly emoji (Animals & Nature, Food & Drink,
Travel & Places, Activities, Objects, Symbols) — the standard set you
know from iPhone/Android keyboards, in Google's Noto design, without
skin-tone variants.

Full set (adds Smileys & Emotion, People & Body, 8 generic flags):

    FULL = True
    exec(<the same one-liner>)

License of the artwork: Apache-2.0 (a copy is installed alongside).
"""
import io
import os
import urllib.request
import zipfile

REPO = "yfuru2454/emoji-san"   # set your GitHub org/user
TAG = "v1.0.0"

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


def _dest_root():
    try:
        from qgis.core import QgsApplication
        profile = QgsApplication.qgisSettingsDirPath()
    except ImportError:  # outside QGIS: write to cwd for inspection
        profile = os.path.abspath("qgis_profile_svg_test")
    return os.path.join(profile, "svg", "EmOji-san")


def main():
    root = _dest_root()
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

    msg = "EmOji-san: %d files installed -> %s" % (n, root)
    print(msg)
    print("Use: layer symbology > Marker > SVG Marker > "
          "SVG Browser > 'EmOji-san' group.")
    if not FULL:
        print("(want faces & people too? run again after:  FULL = True )")
    try:
        from qgis.utils import iface
        if iface:
            iface.messageBar().pushSuccess("EmOji-san", msg)
    except Exception:
        pass


main()
