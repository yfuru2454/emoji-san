# -*- coding: utf-8 -*-
"""Remove the EmOji-san (Noto Emoji) SVGs installed by install.py.

Paste into the QGIS Python console. Deletes the whole
<profile>/svg/EmOji-san folder. Projects that reference these SVGs will
show a default marker afterwards.
"""
import os
import shutil

from qgis.core import QgsApplication

root = os.path.join(QgsApplication.qgisSettingsDirPath(), "svg", "EmOji-san")
if os.path.isdir(root):
    shutil.rmtree(root)
    print("Removed:", root)
else:
    print("Nothing to remove:", root)

try:
    from qgis.utils import iface
    if iface:
        iface.messageBar().pushSuccess("EmOji-san", "Uninstalled")
except Exception:
    pass
