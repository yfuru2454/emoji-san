# -*- coding: utf-8 -*-
"""Remove EmOji-san (Noto Emoji SVGs) installed by install.py.

Paste into the QGIS Python console. Deletes <QGIS3 settings folder>/
EmOji-san and removes it from the SVG paths. Projects that reference
these SVGs will show a default marker afterwards. (Symbols imported
from emoji_san_core.xml embed their SVGs and keep working.)
"""
import os
import shutil

from qgis.core import QgsApplication, QgsSettings

profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
root = os.path.join(os.path.dirname(os.path.dirname(profile)), "EmOji-san")
legacy = os.path.join(profile, "svg", "EmOji-san")

# switch off and remove the save hook from <QGIS3>/startup.py
hook = os.path.join(root, "embed_on_save.py")
if os.path.isfile(hook):
    exec(open(hook, "rb").read(), {"__name__": "emoji_san_embed",
                                   "EMOJI_SAN_EMBED": False})
startup = os.path.join(os.path.dirname(root), "startup.py")
BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
END = "# <<< EmOji-san <<<"
if os.path.isfile(startup):
    with open(startup, encoding="utf-8") as f:
        text = f.read()
    if BEGIN in text and END in text:
        a, rest = text.split(BEGIN, 1)
        text = (a.rstrip("\n") + rest.split(END, 1)[1]).strip("\n")
        with open(startup, "w", encoding="utf-8") as f:
            f.write(text + ("\n" if text else ""))
        print("Removed the EmOji-san lines from:", startup)

for d in (root, legacy):
    if os.path.isdir(d):
        shutil.rmtree(d)
        print("Removed:", d)

s = QgsSettings()
cur = s.value("svg/searchPathsForSVG", [])
if isinstance(cur, str):
    cur = [cur] if cur else []
keep = [p for p in (cur or [])
        if p and os.path.normpath(p) != os.path.normpath(root)]
s.setValue("svg/searchPathsForSVG", keep)
print("SVG paths now:", keep)

try:
    from qgis.utils import iface
    if iface:
        iface.messageBar().pushSuccess("EmOji-san", "Uninstalled")
except Exception:
    pass
