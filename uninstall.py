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
