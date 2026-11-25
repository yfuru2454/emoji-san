# -*- coding: utf-8 -*-
"""EmOji-san diagnostics: why is the SVG browser slow or hanging?

Run in the QGIS Python console (Windows, macOS or Linux):

    exec(open(r'C:\\path\\to\\emoji-san\\tests\\diagnose.py', 'rb').read())

It takes up to about a minute and the console looks frozen meanwhile.
It never changes anything. It prints a report and saves the same text
to emoji-san-diagnose.txt in your home folder, to paste into an issue.

What it measures, from cheapest to most expensive:
  A. environment: QGIS / OS / where the settings folder lives
  B. the EmOji-san folder: local disk? network share? OneDrive / cloud
     placeholder files? (Windows: drive type and file attributes)
  C. every registered SVG path: how many SVGs QGIS has to walk through
     each time the SVG browser opens, and how long the walk takes
  D. reading files: time to read SVG bytes from disk (antivirus and
     network storage show up here as milliseconds per file)
  E. parsing + drawing: Qt's SVG renderer on the same files
  F. QGIS itself: building the SVG group tree, and QGIS's SVG cache
"""
import os
import platform
import sys
import time

from qgis.core import Qgis, QgsApplication, QgsSettings
from qgis.PyQt.QtCore import QSize, Qt
from qgis.PyQt.QtGui import QColor, QImage, QPainter

try:
    from qgis.PyQt.QtSvg import QSvgRenderer
except ImportError:
    QSvgRenderer = None

BUDGET = float(globals().get("BUDGET", 20))  # max seconds per heavy step
lines = []


def out(s=""):
    lines.append(s)
    print(s)


def ms(sec):
    return "%.1f ms" % (sec * 1000)


def is_win():
    return sys.platform.startswith("win")


def win_drive_info(path):
    """(drive type name, attributes note) for a Windows path."""
    import ctypes
    kinds = {0: "unknown", 1: "no root", 2: "removable", 3: "local disk",
             4: "NETWORK", 5: "cd-rom", 6: "ram disk"}
    if path.startswith("\\\\"):
        return "NETWORK (UNC path)"
    root = os.path.splitdrive(path)[0] + "\\"
    t = ctypes.windll.kernel32.GetDriveTypeW(root)
    return kinds.get(t, str(t))


def win_attr_flags(path):
    import ctypes
    a = ctypes.windll.kernel32.GetFileAttributesW(path)
    if a == 0xFFFFFFFF:
        return []
    flags = []
    if a & 0x400:
        flags.append("REPARSE_POINT")
    if a & 0x1000:
        flags.append("OFFLINE")
    if a & 0x400000:
        flags.append("RECALL_ON_DATA_ACCESS (cloud placeholder)")
    if a & 0x40000:
        flags.append("RECALL_ON_OPEN (cloud placeholder)")
    return flags


def walk_svgs(root, budget):
    """Count SVGs under root, stopping after `budget` seconds."""
    t0, n, dirs, files = time.perf_counter(), 0, 0, []
    for dp, dn, fn in os.walk(root):
        dirs += 1
        for f in fn:
            if f.lower().endswith(".svg"):
                n += 1
                if len(files) < 400:
                    files.append(os.path.join(dp, f))
        if time.perf_counter() - t0 > budget:
            return n, dirs, time.perf_counter() - t0, files, True
    return n, dirs, time.perf_counter() - t0, files, False


start = time.perf_counter()
out("EmOji-san diagnostics  (%s)" % time.strftime("%Y-%m-%d %H:%M"))
out("=" * 60)

# A. environment -----------------------------------------------------------
out("A. Environment")
out("  QGIS %s | Python %s | %s %s" % (
    Qgis.version(), platform.python_version(), platform.system(),
    platform.release()))
profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
root = os.path.join(os.path.dirname(os.path.dirname(profile)), "EmOji-san")
out("  profile:   " + profile)
out("  EmOji-san: " + root + ("" if os.path.isdir(root) else "  (MISSING)"))
for var in ("APPDATA", "OneDrive", "OneDriveCommercial"):
    if os.environ.get(var):
        out("  %%%s%% = %s" % (var, os.environ[var]))
hints = []

# B. where the folder lives --------------------------------------------------
out("")
out("B. Storage of the EmOji-san folder")
if is_win() and os.path.isdir(root):
    kind = win_drive_info(root)
    out("  drive type: " + kind)
    if "NETWORK" in kind:
        hints.append("The QGIS settings folder is on a NETWORK drive "
                     "(roaming profile / folder redirection). Every SVG "
                     "is read over the network.")
    od = [os.environ.get(v) for v in ("OneDrive", "OneDriveCommercial")]
    if any(o and os.path.normcase(root).startswith(os.path.normcase(o))
           for o in od):
        out("  inside OneDrive: YES")
        hints.append("The folder is inside OneDrive.")
    sample = None
    for dp, _, fn in os.walk(root):
        svgs = [f for f in fn if f.endswith(".svg")]
        if svgs:
            sample = os.path.join(dp, svgs[0])
            break
    for p in (root, sample):
        if p:
            fl = win_attr_flags(p)
            out("  attributes of %s: %s" % (os.path.basename(p),
                                           ", ".join(fl) or "normal"))
            if any("cloud" in f or "OFFLINE" in f for f in fl):
                hints.append("Files are cloud placeholders (OneDrive "
                             "Files On-Demand or similar): each one is "
                             "downloaded when QGIS opens it.")
elif not is_win():
    out("  (drive checks are Windows-only; skipped)")

# C. registered SVG paths ----------------------------------------------------
out("")
out("C. SVG paths QGIS scans each time the SVG browser opens")
setting = QgsSettings().value("svg/searchPathsForSVG", [])
if isinstance(setting, str):
    setting = [setting] if setting else []
paths = QgsApplication.svgPaths()
total = 0
ours = []
for p in paths:
    if not os.path.isdir(p):
        out("  [missing] " + p)
        if p in (setting or []):
            hints.append("Registered SVG path no longer exists (harmless, "
                         "but can be removed): %s" % p)
        continue
    n, dirs, dt, files, cut = walk_svgs(p, BUDGET / 2)
    total += n
    out("  %6d SVGs %5d folders %9s  %s%s" % (
        n, dirs, ms(dt), p, "  (STOPPED: too big)" if cut else ""))
    if os.path.normcase(os.path.normpath(p)) == os.path.normcase(root):
        ours = files
    if is_win():
        kind = win_drive_info(p)
        pn = os.path.normcase(p).replace("/", "\\")
        shared = pn.startswith(("c:\\mac\\", "\\\\psf\\",
                                "\\\\mac\\"))  # Parallels shares
        if "NETWORK" in kind or shared:
            out("           ^ on %s" % ("a Parallels shared folder (Mac "
                                        "files)" if shared else kind))
            hints.append("SVG path %s is on %s: every preview is read "
                         "across it. Move it to a local folder or remove "
                         "it under Settings > Options > System > SVG "
                         "paths." % (p, "a Parallels shared folder"
                                     if shared else "a network drive"))
    if n > 2000 and os.path.normcase(os.path.normpath(p)) != \
            os.path.normcase(root):
        hints.append("SVG path %s holds %d SVGs. The SVG browser lists "
                     "the SVGs of ALL paths when it opens, so this is "
                     "loaded every time. If it is an older full Noto Emoji "
                     "copy, EmOji-san replaces it: remove it under "
                     "Settings > Options > System > SVG paths." % (p, n))
    elif cut or n > 5000:
        hints.append("SVG path %s holds %s SVGs: QGIS walks all of it "
                     "every time the SVG browser opens. Remove it under "
                     "Settings > Options > System > SVG paths."
                     % (p, ">%d" % n if cut else n))
    if dt > 2:
        hints.append("Just listing %s took %.1f s." % (p, dt))
out("  total: %d SVGs across %d paths" % (total, len(paths)))
dupes = [p for p in paths
         if sum(os.path.normcase(os.path.normpath(q)) ==
                os.path.normcase(os.path.normpath(p)) for q in paths) > 1]
if dupes:
    hints.append("Some SVG paths are listed twice: %s" % sorted(set(dupes)))
nested = [p for p in paths for q in paths
          if p != q and os.path.normcase(os.path.normpath(p)).startswith(
              os.path.normcase(os.path.normpath(q)) + os.sep)]
if nested:
    hints.append("Some SVG paths are inside other SVG paths (scanned "
                 "twice): %s" % sorted(set(nested)))

# D. reading files -------------------------------------------------------------
out("")
out("D. Reading SVG files from disk (EmOji-san folder)")
if not ours and os.path.isdir(root):
    _, _, _, ours, _ = walk_svgs(root, BUDGET / 2)
if ours:
    sample = ours[:200]
    times, t0 = [], time.perf_counter()
    for f in sample:
        a = time.perf_counter()
        with open(f, "rb") as fh:
            fh.read()
        times.append(time.perf_counter() - a)
        if time.perf_counter() - t0 > BUDGET:
            break
    t_first = sum(times)
    times2 = []
    for f in sample[:len(times)]:
        a = time.perf_counter()
        with open(f, "rb") as fh:
            fh.read()
        times2.append(time.perf_counter() - a)
    srt = sorted(times)
    out("  first read : %d files, %s total, median %s, worst %s" % (
        len(times), ms(t_first), ms(srt[len(srt) // 2]), ms(srt[-1])))
    out("  second read: %s total (file cache warm)" % ms(sum(times2)))
    per = t_first / max(1, len(times))
    est = per * 1058
    out("  -> reading all 1,058 would take about %.1f s" % est)
    if per > 0.002:
        hints.append("Reading one SVG takes %s on average (normal: well "
                     "under 1 ms). Typical causes: antivirus scanning "
                     "each file, network or cloud storage. Try excluding "
                     "%s from real-time scanning, or moving it to a "
                     "local folder." % (ms(per), root))
else:
    out("  no SVGs found to test")

# E. Qt SVG parse + draw ---------------------------------------------------------
out("")
out("E. Parsing + drawing with Qt's SVG renderer (64 px previews)")
if ours and QSvgRenderer:
    res, t0 = [], time.perf_counter()
    for f in ours[:200]:
        a = time.perf_counter()
        r = QSvgRenderer(f)
        img = QImage(64, 64, QImage.Format_ARGB32_Premultiplied)
        img.fill(Qt.transparent)
        p = QPainter(img)
        r.render(p)
        p.end()
        res.append((time.perf_counter() - a, f))
        if time.perf_counter() - t0 > BUDGET:
            break
    res.sort()
    tot = sum(t for t, _ in res)
    out("  %d files, %s total, median %s, slowest %s (%s)" % (
        len(res), ms(tot), ms(res[len(res) // 2][0]), ms(res[-1][0]),
        os.path.basename(res[-1][1])))
    est = tot / max(1, len(res)) * 1058
    out("  -> previews for all 1,058 would take about %.1f s" % est)
    if est > 15:
        hints.append("Drawing the previews themselves is slow (%.0f s for "
                     "all). Pick a category folder in the SVG browser, not "
                     "the top 'EmOji-san' group, which lists every "
                     "category at once." % est)
elif not QSvgRenderer:
    out("  QtSvg not available; skipped")

# F. QGIS itself -------------------------------------------------------------------
out("")
out("F. QGIS: SVG group tree and SVG cache")
try:
    from qgis.gui import QgsSvgSelectorGroupsModel
    a = time.perf_counter()
    model = QgsSvgSelectorGroupsModel(None)
    out("  building the SVG group tree: %s (%d top-level groups)" % (
        ms(time.perf_counter() - a), model.rowCount()))
    if time.perf_counter() - a > 3:
        hints.append("Building the SVG group tree alone takes %.1f s: "
                     "too many folders in the SVG paths (section C)."
                     % (time.perf_counter() - a))
except Exception as ex:
    out("  group tree: skipped (%s)" % ex)
if ours:
    cache = QgsApplication.svgCache()
    a = time.perf_counter()
    done = 0
    for f in ours[:50]:
        r = cache.svgAsImage(f, 64, QColor(0, 0, 0), QColor(0, 0, 0), 1, 1,
                             0, True)
        done += 1
    out("  QGIS SVG cache, 50 previews: %s" % ms(time.perf_counter() - a))

# summary ----------------------------------------------------------------------------
out("")
out("=" * 60)
out("Finished in %.1f s." % (time.perf_counter() - start))
if hints:
    out("LIKELY CAUSES:")
    for i, h in enumerate(hints, 1):
        out("  %d. %s" % (i, h))
else:
    out("Nothing obviously slow was measured. If the SVG browser still "
        "hangs, note which group you click when it hangs (the top "
        "'EmOji-san' group or a category) and include this report.")

report = os.path.join(os.path.expanduser("~"), "emoji-san-diagnose.txt")
try:
    with open(report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("Report saved to: " + report)
except OSError as ex:
    print("Could not save the report: %s" % ex)
