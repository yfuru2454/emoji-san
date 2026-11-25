# -*- coding: utf-8 -*-
"""EmOji-san: embed EmOji-san SVGs into project files as they are saved.

install.py with EMBED=True adds a few lines to startup.py that load this
file at every QGIS start. EMBED=False or uninstall.py removes them.

While QGIS writes a project, every layer style that points at a file in the
EmOji-san folder gets the SVG itself instead ("base64:..."). The saved
.qgs/.qgz then shows the emoji on computers without EmOji-san. Only the
saved file changes; the layers in the open project keep their file paths.

Covered: SVG markers and SVG fills, wherever they sit in a layer's symbols,
and SVG label backgrounds. Not covered: pictures in print layouts, and
annotations that are not on a layer of their own. SVGs from other folders
are left alone.
"""
import base64
import builtins
import os

from qgis.core import (QgsApplication, QgsMessageLog, QgsProject,
                       QgsSymbolLayerUtils)

# symbol layer class -> the property that holds its SVG path
SVG_PROPERTY = {"SvgMarker": "name", "SVGFill": "svgFile"}
# The connected function is kept on builtins, so that running this file
# again (install.py does, in a namespace of its own) finds the old hook.
HANDLE = "_emoji_san_embed_fn"


def _folder():
    profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
    return os.path.join(os.path.dirname(os.path.dirname(profile)),
                        "EmOji-san")


def _spots(node):
    """Yield (element, attribute) for each place under node that holds the
    SVG path of a marker, a fill or a label background."""
    layers = node.elementsByTagName("layer")
    for i in range(layers.count()):
        layer = layers.at(i).toElement()
        prop = SVG_PROPERTY.get(layer.attribute("class"))
        if not prop:
            continue
        child = layer.firstChildElement()
        while not child.isNull():
            if child.tagName() == "Option":  # QGIS 3.18 and later
                option = child.firstChildElement("Option")
                while not option.isNull():
                    if option.attribute("name") == prop:
                        yield option, "value"
                    option = option.nextSiblingElement("Option")
            elif child.tagName() == "prop" and child.attribute("k") == prop:
                yield child, "v"  # QGIS 3.16 and earlier
            child = child.nextSiblingElement()
    backgrounds = node.elementsByTagName("background")
    for i in range(backgrounds.count()):
        yield backgrounds.at(i).toElement(), "shapeSVGFile"


def embed_emoji_svgs(node):
    """Embed the EmOji-san SVGs referenced under a QDomElement or
    QDomDocument. Returns how many references were replaced."""
    folder = _folder()
    # QGIS hands back canonical paths, so compare against both spellings
    ours = tuple({os.path.normcase(p) + os.sep
                  for p in (os.path.normpath(folder),
                            os.path.realpath(folder))})
    resolver = QgsProject.instance().pathResolver()
    encoded = {}
    count = 0
    for element, attribute in _spots(node):
        value = element.attribute(attribute)
        if not value or value.startswith("base64:"):
            continue
        path = QgsSymbolLayerUtils.svgSymbolNameToPath(value, resolver)
        if not path or not os.path.isfile(path):
            continue
        if not (os.path.normcase(os.path.normpath(path)).startswith(ours)
                or os.path.normcase(os.path.realpath(path)).startswith(ours)):
            continue
        if path not in encoded:
            with open(path, "rb") as f:
                encoded[path] = "base64:" + base64.b64encode(
                    f.read()).decode("ascii")
        element.setAttribute(attribute, encoded[path])
        count += 1
    return count


def _on_write_layer(layer, element, document):
    # QgsProject.writeMapLayer: sent for each layer once its style is in
    # `element`. (writeProject comes before the layers are written.)
    try:
        embed_emoji_svgs(element)
    except Exception as ex:  # saving the project comes first
        QgsMessageLog.logMessage("embedding failed: %s" % ex, "EmOji-san")


def disable():
    """Disconnect the hook in this session, if it is connected."""
    hook = getattr(builtins, HANDLE, None)
    if hook is not None:
        try:
            QgsProject.instance().writeMapLayer.disconnect(hook)
        except (TypeError, RuntimeError):
            pass
        setattr(builtins, HANDLE, None)


def enable():
    """Connect the hook, replacing one connected earlier in this session."""
    disable()
    QgsProject.instance().writeMapLayer.connect(_on_write_layer)
    setattr(builtins, HANDLE, _on_write_layer)


if globals().get("EMOJI_SAN_EMBED", True):
    enable()
else:
    disable()
