# -*- coding: utf-8 -*-
# EmOji-san: uninstall.
#
# Run it from the QGIS Python console with the one-line command in
# README.md.
#
# It deletes the files EmOji-san installed, takes the folder off the SVG
# paths and removes the EmOji-san lines from startup.py. Files in the folder
# that are not in its index.csv stay, and then so does the folder.
#
# Markers that point at the deleted SVGs show "?" afterwards. Symbols
# imported from emoji_san_core.xml carry their SVG inside and keep working;
# delete those in the Style Manager.


def _emoji_san_uninstall():
    import builtins
    import csv
    import os

    from qgis.core import QgsApplication, QgsProject, QgsSettings, QgsStyle
    from qgis.PyQt.QtCore import QStandardPaths

    FOLDER = "EmOji-san"
    SVG_PATHS = "svg/searchPathsForSVG"
    EXTRAS = ("index.csv", "README.txt", "LICENSE-noto-emoji.txt", "NOTICE",
              "UPSTREAM_COMMIT.txt", "embed_on_save.py")
    LITTER = (".DS_Store", "Thumbs.db", "desktop.ini")  # left by file managers
    BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
    END = "# <<< EmOji-san <<<"

    profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
    root = os.path.join(os.path.dirname(os.path.dirname(profile)), FOLDER)
    done = False

    def same(a, b):
        return (os.path.normcase(os.path.normpath(a))
                == os.path.normcase(os.path.normpath(b)))

    # the save hook: this session, then startup.py
    hook = getattr(builtins, "_emoji_san_embed_fn", None)
    if hook is not None:
        try:
            QgsProject.instance().writeMapLayer.disconnect(hook)
        except (TypeError, RuntimeError):
            pass
        builtins._emoji_san_embed_fn = None
    try:  # Qt 5
        where = QStandardPaths.AppDataLocation
    except AttributeError:  # Qt 6
        where = QStandardPaths.StandardLocation.AppDataLocation
    startup = os.path.normpath(os.path.join(
        QStandardPaths.writableLocation(where), "startup.py"))
    try:
        with open(startup, encoding="utf-8") as f:
            text = f.read()
    except (OSError, ValueError):
        text = ""
    head, begin, rest = text.partition(BEGIN)
    body, end, tail = rest.partition(END)
    if begin and end:
        text = (head.rstrip("\n") + tail).strip("\n")
        if text:
            with open(startup + ".tmp", "w", encoding="utf-8") as f:
                f.write(text + "\n")
            os.replace(startup + ".tmp", startup)
        else:
            os.remove(startup)  # nothing but our lines was in it
        print("EmOji-san lines removed from %s" % startup)
        done = True

    # the files: those index.csv lists, and the few written next to it
    left = 0
    if os.path.isdir(root):
        listed = None
        try:
            with open(os.path.join(root, "index.csv"), encoding="utf-8",
                      newline="") as f:
                listed = {r.get("path") or "" for r in csv.DictReader(f)}
        except (OSError, ValueError, csv.Error):
            pass
        for folder, _, names in os.walk(root, topdown=False):
            for name in names:
                path = os.path.join(folder, name)
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                if rel in EXTRAS or rel in (listed or ()) or name in LITTER:
                    os.remove(path)
                else:
                    left += 1
            if not os.listdir(folder):
                os.rmdir(folder)
        if not left:
            print("Removed %s" % root)
        elif listed is None:
            print("No index.csv in %s, so there is no telling which of its "
                  "%d file(s) are EmOji-san's. They were left alone. Run "
                  "the install line once more and then this one, or delete "
                  "the folder by hand." % (root, left))
        else:
            print("Kept %d file(s) that are not in index.csv; the folder "
                  "stays an SVG path: %s" % (left, root))
        done = True

    # the SVG path, and EmOji-san folders registered from another QGIS
    # version's settings (those folders are not ours to delete)
    registered = QgsSettings().value(SVG_PATHS, [])
    if isinstance(registered, str):
        registered = [registered]
    registered = [p for p in (registered or []) if p]
    keep = []
    for p in registered:
        if same(p, root):
            if left:
                keep.append(p)
        elif os.path.basename(os.path.normpath(p)) == FOLDER and (
                not os.path.isdir(p)
                or os.path.isfile(os.path.join(p, "index.csv"))):
            print("Taken off the SVG paths: %s (the EmOji-san folder of "
                  "another QGIS version; its files are still there)" % p)
        else:
            keep.append(p)
    if keep != registered:
        if hasattr(QgsApplication, "setSvgPaths"):  # QGIS 3.18 and later
            QgsApplication.setSvgPaths(keep)
        else:
            QgsSettings().setValue(SVG_PATHS, keep)
        done = True

    if not done:
        print("EmOji-san is not installed here (%s)." % root)
        return

    style = QgsStyle.defaultStyle()
    try:  # QGIS 3
        entity = QgsStyle.SymbolEntity
    except AttributeError:  # QGIS 4
        entity = QgsStyle.StyleEntity.SymbolEntity
    tag = style.tagId(FOLDER)
    tagged = len(style.symbolsWithTag(entity, tag)) if tag else 0
    if tagged:
        print("%d symbols tagged EmOji-san are still in the Style Manager. "
              "They carry their SVG inside and work without the folder."
              % tagged)
    print("EmOji-san uninstalled.")
    try:
        from qgis.utils import iface
        if iface:
            iface.messageBar().pushSuccess("EmOji-san", "Uninstalled")
    except Exception:
        pass


try:
    _emoji_san_uninstall()
finally:
    del _emoji_san_uninstall
