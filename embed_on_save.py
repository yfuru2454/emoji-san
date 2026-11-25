# -*- coding: utf-8 -*-
"""EmOji-san: embed EmOji-san SVGs into project files when they are saved.

Loaded at QGIS start-up by a few lines that install.py adds to
<QGIS3 settings folder>/startup.py, which QGIS runs at every start
(remove them with EMBED=False or uninstall).

When QGIS writes a project, every SVG path in a layer's symbology that
points into the EmOji-san folder is replaced by the SVG itself
("base64:..."), so the
saved .qgs/.qgz shows the emoji on any computer, with or without
EmOji-san. Only the saved file changes; the layers you are editing keep
their file paths. SVGs from other folders are left alone.
"""
import base64
import os

from qgis.core import QgsApplication, QgsProject, QgsSymbolLayerUtils

# SVG options in the project XML: SVG marker ("name"), SVG fill ("svgFile")
_KEYS = ("name", "svgFile")


def _root():
    profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
    return os.path.join(os.path.dirname(os.path.dirname(profile)),
                        "EmOji-san")


def embed_emoji_svgs(node):
    """Replace EmOji-san SVG paths under a QDomDocument/QDomElement."""
    root = os.path.normcase(os.path.normpath(_root())) + os.sep
    resolver = QgsProject.instance().pathResolver()
    cache = {}
    n = 0
    for tag, key_attr, val_attr in (("Option", "name", "value"),
                                    ("prop", "k", "v")):
        nodes = node.elementsByTagName(tag)
        for i in range(nodes.count()):
            el = nodes.at(i).toElement()
            if el.attribute(key_attr) not in _KEYS:
                continue
            value = el.attribute(val_attr)
            if not value or value.startswith(("base64:", "http")):
                continue
            path = QgsSymbolLayerUtils.svgSymbolNameToPath(value, resolver)
            norm = os.path.normcase(os.path.normpath(path or ""))
            if not norm.startswith(root) or not os.path.isfile(path):
                continue
            if path not in cache:
                with open(path, "rb") as f:
                    cache[path] = "base64:" + base64.b64encode(
                        f.read()).decode("ascii")
            el.setAttribute(val_attr, cache[path])
            n += 1
    return n


def _on_write_layer(layer, elem, doc):
    # QgsProject.writeMapLayer: emitted per layer with its symbology already
    # in `elem` (writeProject fires before the layers are written).
    try:
        embed_emoji_svgs(elem)
    except Exception as ex:  # never block saving a project
        try:
            from qgis.core import QgsMessageLog
            QgsMessageLog.logMessage("embed failed: %s" % ex, "EmOji-san")
        except Exception:
            pass


def disable():
    """Disconnect the hook in this session, if connected."""
    import builtins
    fn = getattr(builtins, "_emoji_san_embed_fn", None)
    if fn is not None:
        try:
            QgsProject.instance().writeMapLayer.disconnect(fn)
        except (TypeError, RuntimeError):
            pass
        builtins._emoji_san_embed_fn = None


def enable():
    """Connect once per QGIS session (re-running replaces the old hook)."""
    import builtins
    disable()
    QgsProject.instance().writeMapLayer.connect(_on_write_layer)
    builtins._emoji_san_embed_fn = _on_write_layer


if globals().get("EMOJI_SAN_EMBED", True):
    enable()
else:
    disable()
