# -*- coding: utf-8 -*-
# EmOji-san: why is the SVG browser slow, or why does it hang?
#
# Run it from the QGIS Python console with the one-line command in
# README.md.
#
# It can take a minute, and QGIS does not respond until it is done. Nothing
# is changed. The report is printed and also saved as
# emoji-san-diagnose.txt in your home folder, ready to paste into an issue.
#
# What it measures, cheapest first:
#   A. QGIS, the operating system and where the settings folder is
#   B. where the EmOji-san folder is stored (Windows only): local disk,
#      network drive, OneDrive, cloud placeholder files
#   C. each SVG path: how many SVGs the SVG browser has to list every time
#      it opens, and how long it takes to walk the folder
#   D. reading SVG files from disk (antivirus and network storage show up
#      here as milliseconds per file)
#   E. parsing and drawing them with Qt's SVG renderer
#   F. QGIS itself: building the folder tree of the SVG browser, and the
#      SVG cache
#
# BUDGET=60; in front of the command gives each slow step 60 seconds
# instead of 20.


def _emoji_san_diagnose(ns):
    import os
    import platform
    import sys
    import time

    from qgis.core import Qgis, QgsApplication, QgsSettings
    from qgis.PyQt.QtGui import QColor, QImage, QPainter
    try:
        from qgis.PyQt.QtSvg import QSvgRenderer
    except ImportError:
        QSvgRenderer = None

    FOLDER = "EmOji-san"
    budget = float(ns.pop("BUDGET", 20))  # seconds a slow step may take
    windows = sys.platform.startswith("win")
    lines, causes = [], []
    clock = time.perf_counter

    def out(text=""):
        lines.append(text)
        print(text)

    def ms(seconds):
        return "%.1f ms" % (seconds * 1000)

    def key(path):
        return os.path.normcase(os.path.normpath(path))

    def drive_type(path):
        """Kind of drive a Windows path is on."""
        import ctypes
        if path.startswith("\\\\"):
            return "NETWORK (UNC path)"
        kinds = {0: "unknown", 1: "no root", 2: "removable", 3: "local disk",
                 4: "NETWORK", 5: "cd-rom", 6: "ram disk"}
        kind = ctypes.windll.kernel32.GetDriveTypeW(
            os.path.splitdrive(path)[0] + "\\")
        return kinds.get(kind, str(kind))

    def cloud_flags(path):
        """Windows file attributes that mean the content is elsewhere."""
        import ctypes
        attributes = ctypes.windll.kernel32.GetFileAttributesW(path)
        if attributes in (-1, 0xFFFFFFFF):  # INVALID_FILE_ATTRIBUTES
            return []
        return [name for bit, name in (
            (0x400, "REPARSE_POINT"),
            (0x1000, "OFFLINE"),
            (0x40000, "RECALL_ON_OPEN (cloud placeholder)"),
            (0x400000, "RECALL_ON_DATA_ACCESS (cloud placeholder)"),
        ) if attributes & bit]

    def walk(folder, limit):
        """(SVG count, folder count, seconds, first 400 SVGs, cut short)."""
        start, count, folders, files = clock(), 0, 0, []
        for path, _, names in os.walk(folder):
            folders += 1
            for name in names:
                if name.lower().endswith(".svg"):
                    count += 1
                    if len(files) < 400:
                        files.append(os.path.join(path, name))
            if clock() - start > limit:
                return count, folders, clock() - start, files, True
        return count, folders, clock() - start, files, False

    started = clock()
    out("EmOji-san diagnostics  (%s)" % time.strftime("%Y-%m-%d %H:%M"))
    out("=" * 60)

    # A. environment -------------------------------------------------------
    out("A. Environment")
    out("  QGIS %s | Python %s | %s %s" % (
        Qgis.version(), platform.python_version(), platform.system(),
        platform.release()))
    profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
    root = os.path.join(os.path.dirname(os.path.dirname(profile)), FOLDER)
    setting = QgsSettings().value("svg/searchPathsForSVG", [])
    if isinstance(setting, str):
        setting = [setting]
    setting = [p for p in (setting or []) if p]
    out("  profile:   " + profile)
    if not os.path.isdir(root):
        out("  EmOji-san: " + root + "  (MISSING)")
        # QGIS 4 keeps using the folder of QGIS 3 after taking over a profile
        for p in setting:
            if os.path.basename(os.path.normpath(p)) == FOLDER \
                    and os.path.isdir(p):
                root = os.path.normpath(p)
                out("             measuring %s instead (an SVG path of "
                    "this QGIS)" % root)
                break
    else:
        out("  EmOji-san: " + root)
    for name in ("APPDATA", "OneDrive", "OneDriveCommercial"):
        if os.environ.get(name):
            out("  %%%s%% = %s" % (name, os.environ[name]))

    # B. where the folder is stored ----------------------------------------
    out("")
    out("B. Storage of the EmOji-san folder")
    if not windows:
        out("  (Windows only; skipped)")
    elif os.path.isdir(root):
        kind = drive_type(root)
        out("  drive type: " + kind)
        if "NETWORK" in kind:
            causes.append("The QGIS settings folder is on a NETWORK drive "
                          "(roaming profile or folder redirection). Every "
                          "SVG is read over the network.")
        cloud = [os.environ.get(v) for v in ("OneDrive",
                                             "OneDriveCommercial")]
        if any(c and key(root).startswith(key(c)) for c in cloud):
            out("  inside OneDrive: YES")
            causes.append("The EmOji-san folder is inside OneDrive.")
        first = None
        for path, _, names in os.walk(root):
            svgs = [n for n in names if n.lower().endswith(".svg")]
            if svgs:
                first = os.path.join(path, svgs[0])
                break
        for path in (root, first):
            if path:
                flags = cloud_flags(path)
                out("  attributes of %s: %s" % (
                    os.path.basename(path), ", ".join(flags) or "normal"))
                if any("cloud" in f or "OFFLINE" in f for f in flags):
                    causes.append("The files are cloud placeholders "
                                  "(OneDrive Files On-Demand or similar): "
                                  "each one is downloaded when QGIS opens "
                                  "it.")

    # C. the SVG paths -----------------------------------------------------
    out("")
    out("C. SVG paths the SVG browser lists each time it opens")
    remove = "Remove it under Settings > Options > System > SVG Paths."
    paths = QgsApplication.svgPaths()
    total, ours, n_ours = 0, [], 0
    for p in paths:
        if not os.path.isdir(p):
            out("  [missing] " + p)
            if p in setting:
                causes.append("SVG path %s no longer exists. Harmless, but "
                              "it can go. %s" % (p, remove))
            continue
        count, folders, seconds, files, cut = walk(p, budget / 2)
        total += count
        out("  %6d SVGs %5d folders %9s  %s%s" % (
            count, folders, ms(seconds), p,
            "  (STOPPED: too big)" if cut else ""))
        mine = key(p) == key(root)
        if mine:
            ours, n_ours = files, count
        if windows:
            kind = drive_type(p)
            shared = key(p).replace("/", "\\").startswith(
                ("c:\\mac\\", "\\\\psf\\", "\\\\mac\\"))  # Parallels
            if "NETWORK" in kind or shared:
                where = "a Parallels shared folder" if shared else \
                    "a network drive"
                out("           ^ on %s" % where)
                causes.append("SVG path %s is on %s, so every preview is "
                              "read across it. Move the folder to a local "
                              "disk, or: %s" % (p, where, remove))
        if not mine and (cut or count > 2000):
            causes.append("SVG path %s holds %s%d SVGs. The SVG browser "
                          "lists the SVGs of all paths when it opens, so "
                          "these are loaded every time. If it is an older "
                          "full copy of Noto Emoji, EmOji-san replaces it. "
                          "%s" % (p, "more than " if cut else "", count,
                                  remove))
        if seconds > 2:
            causes.append("Listing %s alone took %.1f s." % (p, seconds))
    out("  total: %d SVGs in %d paths" % (total, len(paths)))
    twice = sorted({p for p in paths
                    if sum(key(q) == key(p) for q in paths) > 1})
    if twice:
        causes.append("SVG paths listed twice: %s" % ", ".join(twice))
    nested = sorted({p for p in paths for q in paths
                     if p != q and key(p).startswith(key(q) + os.sep)})
    if nested:
        causes.append("SVG paths inside other SVG paths (listed twice): %s"
                      % ", ".join(nested))

    # D. reading files -----------------------------------------------------
    out("")
    out("D. Reading SVG files from disk (EmOji-san folder)")
    if not ours and os.path.isdir(root):
        n_ours, _, _, ours, _ = walk(root, budget / 2)
    if ours:
        sample = ours[:200]
        times, start = [], clock()
        for path in sample:
            t = clock()
            with open(path, "rb") as f:
                f.read()
            times.append(clock() - t)
            if clock() - start > budget:
                break
        again = clock()
        for path in sample[:len(times)]:
            with open(path, "rb") as f:
                f.read()
        again = clock() - again
        ordered = sorted(times)
        each = sum(times) / len(times)
        out("  first read : %d files, %s in all, median %s, slowest %s" % (
            len(times), ms(sum(times)), ms(ordered[len(ordered) // 2]),
            ms(ordered[-1])))
        out("  second read: %s in all (served from memory)" % ms(again))
        out("  -> reading all %d would take about %.1f s" % (
            n_ours, each * n_ours))
        if each > 0.002:
            causes.append("Reading one SVG takes %s on average; well under "
                          "1 ms is normal. The usual reasons are antivirus "
                          "scanning each file, or network or cloud storage. "
                          "Exclude %s from real-time scanning, or move it "
                          "to a local disk." % (ms(each), root))
    else:
        out("  no SVGs found to test")

    # E. parsing and drawing -----------------------------------------------
    out("")
    out("E. Parsing and drawing with Qt's SVG renderer (64 px previews)")
    if not QSvgRenderer:
        out("  QtSvg is not available; skipped")
    elif ours:
        try:  # Qt 5
            argb = QImage.Format_ARGB32_Premultiplied
        except AttributeError:  # Qt 6
            argb = QImage.Format.Format_ARGB32_Premultiplied
        drawn, start = [], clock()
        for path in ours[:200]:
            t = clock()
            image = QImage(64, 64, argb)
            image.fill(0)  # transparent
            painter = QPainter(image)
            QSvgRenderer(path).render(painter)
            painter.end()
            drawn.append((clock() - t, path))
            if clock() - start > budget:
                break
        drawn.sort()
        took = sum(t for t, _ in drawn)
        out("  %d files, %s in all, median %s, slowest %s (%s)" % (
            len(drawn), ms(took), ms(drawn[len(drawn) // 2][0]),
            ms(drawn[-1][0]), os.path.basename(drawn[-1][1])))
        estimate = took / len(drawn) * n_ours
        out("  -> previews of all %d would take about %.1f s" % (
            n_ours, estimate))
        if estimate > 15:
            causes.append("Drawing the previews is slow in itself (%.0f s "
                          "for all of them). In the SVG browser, click a "
                          "category and not the top EmOji-san folder, which "
                          "shows every category at once." % estimate)

    # F. QGIS itself -------------------------------------------------------
    out("")
    out("F. QGIS: folder tree of the SVG browser, and the SVG cache")
    try:
        from qgis.gui import QgsSvgSelectorGroupsModel
        t = clock()
        model = QgsSvgSelectorGroupsModel(None)
        took = clock() - t
        out("  building the folder tree: %s (%d top-level folders)" % (
            ms(took), model.rowCount()))
        if took > 3:
            causes.append("Building the folder tree alone takes %.1f s: "
                          "too many folders in the SVG paths (section C)."
                          % took)
    except Exception as ex:
        out("  folder tree: skipped (%s)" % ex)
    if ours:
        cache = QgsApplication.svgCache()
        black = QColor(0, 0, 0)
        t = clock()
        for path in ours[:50]:
            cache.svgAsImage(path, 64, black, black, 1, 1)
        out("  SVG cache, %d previews: %s" % (len(ours[:50]),
                                              ms(clock() - t)))

    # summary --------------------------------------------------------------
    out("")
    out("=" * 60)
    out("Finished in %.1f s." % (clock() - started))
    causes = list(dict.fromkeys(causes))  # each one once
    if causes:
        out("LIKELY CAUSES:")
        for number, cause in enumerate(causes, 1):
            out("  %d. %s" % (number, cause))
    else:
        out("Nothing measured here is slow. If the SVG browser still hangs, "
            "note which folder you clicked when it did (the top EmOji-san "
            "folder or a category) and send that with this report.")

    report = os.path.join(os.path.expanduser("~"), "emoji-san-diagnose.txt")
    try:
        with open(report, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        print("Report saved to: " + report)
    except OSError as ex:
        print("Could not save the report: %s" % ex)


try:
    _emoji_san_diagnose(globals())
finally:
    del _emoji_san_diagnose
