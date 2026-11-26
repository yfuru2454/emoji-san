# -*- coding: utf-8 -*-
# Unregister EmOji-san in this profile and remove unused managed files.


def _emoji_san_storage():
    import csv
    import json
    import os
    import re
    import stat
    import sys

    from qgis.core import QgsApplication
    from qgis.PyQt.QtCore import QLockFile, QSettings

    profile = os.path.abspath(QgsApplication.qgisSettingsDirPath())
    profiles = os.path.dirname(profile)
    if os.path.basename(profiles).lower() != "profiles":
        raise ValueError("unexpected QGIS profile path: %s" % profile)
    root = os.path.join(os.path.dirname(profiles), "EmOji-san")
    manifest = ".emoji-san-owned.json"
    extras = {"LICENSE-noto-emoji.txt", "LICENSE-gemoji.txt", "NOTICE",
              "UPSTREAM_COMMIT.txt", "README.txt", "index.csv", "embed_on_save.py"}
    settings_key = "svg/searchPathsForSVG"
    svg_pattern = re.compile(r"[A-Za-z][A-Za-z0-9 _-]*/[a-z0-9_]+\.svg")
    reserved = re.compile(r"CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9]", re.I)

    def svg_path(rel):
        if not isinstance(rel, str) or not svg_pattern.fullmatch(rel):
            return False
        category, name = rel[:-4].split("/")
        return (not category.endswith(" ") and not reserved.fullmatch(category)
                and not reserved.fullmatch(name))

    def registered_paths(value):
        if isinstance(value, str):
            return [value] if value else []
        return [path for path in (value or []) if isinstance(path, str) and path]

    def same(a, b):
        if os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b)):
            return True
        try:
            return os.path.samefile(a, b)
        except OSError:
            return False

    if os.name == "nt" and sys.version_info < (3, 8):
        # Older Windows Python can follow junctions even in lstat().
        import ctypes
        from ctypes import wintypes

        attributes = ctypes.WinDLL("kernel32", use_last_error=True).GetFileAttributesW
        attributes.argtypes = (wintypes.LPCWSTR,)
        attributes.restype = wintypes.DWORD
    else:
        attributes = None

    def path_info(path):
        if attributes is not None:
            flags = attributes(path)
            if flags == 0xffffffff:
                error = ctypes.get_last_error()
                if error in (2, 3):  # file or path not found
                    return None
                raise ctypes.WinError(error)
            if flags & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                raise ValueError("unsafe linked path: %s" % path)
        try:
            info = os.lstat(path)
        except FileNotFoundError:
            return None
        if (stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError("unsafe linked path: %s" % path)
        return info

    def plain(path, directory=False):
        """Check each existing component before any filesystem operation."""
        info = path_info(path)
        if info is None:
            return False
        expected = stat.S_ISDIR if directory else stat.S_ISREG
        if not expected(info.st_mode):
            raise ValueError("unsafe file or folder: %s" % path)
        return True

    def target(rel, base=root):
        if rel not in extras and rel != manifest and not svg_path(rel):
            raise ValueError("unexpected EmOji-san file name: %r" % rel)
        plain(base, directory=True)
        parent = base
        parts = rel.split("/")
        for part in parts[:-1]:
            parent = os.path.join(parent, part)
            plain(parent, directory=True)
        path = os.path.join(parent, parts[-1])
        plain(path)
        canonical_base = os.path.normcase(os.path.realpath(base))
        canonical_path = os.path.normcase(os.path.realpath(path))
        if os.path.commonpath([canonical_base, canonical_path]) != canonical_base:
            raise ValueError("file is outside EmOji-san: %s" % path)
        return path

    def owned_files():
        path = target(manifest)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as file:
                record = json.load(file)
            if (not isinstance(record, dict) or record.get("format") != 1
                    or not isinstance(record.get("files"), list)
                    or any(not isinstance(rel, str) or
                           (rel not in extras and not svg_path(rel))
                           for rel in record["files"])):
                raise ValueError("invalid EmOji-san ownership record: %s" % path)
            return set(record["files"]) | {manifest}

        path = target("index.csv")
        if not os.path.isfile(path):
            return set()
        # Previous versions recorded only SVGs in their installed CSV.
        with open(path, encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            fields = [name for name in (reader.fieldnames or [])
                      if not name.startswith("name_")]
            if fields != ["emoji", "codepoint", "name", "category", "path",
                          "set", "noto_file"]:
                raise ValueError("unrecognized EmOji-san index: %s" % path)
            rows = list(reader)
        if not rows or any(not svg_path(row["path"]) or row["set"] not in ("S", "M", "L")
                           for row in rows):
            raise ValueError("invalid EmOji-san index: %s" % path)
        return {row["path"] for row in rows} | extras

    def other_profiles():
        # Use the same INI location within each profile as the active QGIS.
        current_file = os.path.abspath(QSettings().fileName())
        current_base = os.path.normcase(profile)
        try:
            per_profile = (os.path.commonpath([current_base, os.path.normcase(current_file)])
                           == current_base)
        except ValueError:
            per_profile = False
        relative = os.path.relpath(current_file, profile) if per_profile else None
        folders = [(profiles, (relative,))]
        home = os.path.dirname(profiles)
        version = os.path.basename(home).lower()
        if version in ("qgis3", "qgis4") and relative:
            other_version = "QGIS4" if version == "qgis3" else "QGIS3"
            sibling = os.path.join(os.path.dirname(home), other_version, "profiles")
            # A migrated profile may still reference its previous version's SVGs.
            alternate = os.path.join(os.path.dirname(relative), other_version + ".ini")
            folders.append((sibling, {relative, alternate}))
        for directory, settings_names in folders:
            try:
                entries = os.listdir(directory)
            except FileNotFoundError:
                continue
            except OSError:
                return True
            for name in entries:
                peer = os.path.join(directory, name)
                if same(peer, profile):
                    continue
                try:
                    info = path_info(peer)
                    if info is None or not stat.S_ISDIR(info.st_mode):
                        continue
                    if not relative:
                        return True
                    for settings_name in settings_names:
                        config = os.path.join(peer, settings_name)
                        if plain(config):
                            other = QSettings(config, QSettings.Format.IniFormat)
                            other.sync()
                            paths = registered_paths(other.value(settings_key, []))
                            if (other.status() != QSettings.Status.NoError
                                    or any(same(p, root) for p in paths)):
                                return True
                except (OSError, ValueError):
                    return True  # cannot rule out another user of the shared copy
        return False

    def acquire():
        path = os.path.join(os.path.dirname(root), ".EmOji-san.lock")
        plain(path)
        lock = QLockFile(path)
        lock.setStaleLockTime(0)
        if not lock.tryLock(0):
            raise OSError("cannot lock EmOji-san; close any other installation or uninstall first")
        return lock

    def clean_categories(rels):
        # Only clean categories where this operation removed an owned SVG.
        for category in {rel.split("/")[0] for rel in rels if svg_path(rel)}:
            folder = os.path.join(root, category)
            if plain(root, directory=True) and plain(folder, directory=True):
                names = os.listdir(folder)
                if set(names) <= {".DS_Store", "Thumbs.db", "desktop.ini"}:
                    for name in names:
                        litter = os.path.join(folder, name)
                        if plain(litter):
                            os.unlink(litter)
                    os.rmdir(folder)

    return (root, manifest, settings_key, svg_path, registered_paths, same, plain,
            path_info, target, owned_files, other_profiles, acquire, clean_categories)


def _emoji_san_uninstall():
    import ast
    import builtins
    import csv
    import io
    import os
    import stat
    import tempfile

    from qgis.core import QgsApplication, QgsProject, QgsSettings, QgsStyle
    from qgis.PyQt.QtCore import QLockFile, QStandardPaths

    folder_name = "EmOji-san"
    embed_key = "emoji-san/embedOnSave"
    begin = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
    end = "# <<< EmOji-san <<<"

    def tidy_startup(root, same, unregister):
        """Take EmOji-san's lines out of startup.py when nothing needs them.

        The old loader of this folder always goes. The current block lists
        the EmOji-san folders that opted in; with unregister, this folder
        leaves the list, and the block goes when the list is empty. Returns
        (changed, note). A startup.py that EmOji-san cannot edit, or never
        wrote to, is left as it is and does not stop the uninstall.
        """
        try:  # Qt 5
            where = QStandardPaths.AppDataLocation
        except AttributeError:  # Qt 6
            where = QStandardPaths.StandardLocation.AppDataLocation
        location = QStandardPaths.writableLocation(where)
        if not location:
            return False, None
        app_data = os.path.realpath(location)
        startup = os.path.join(app_data, "startup.py")

        def read():
            """The text, None without our lines, or raise to leave it alone."""
            try:
                info = os.lstat(startup)
            except FileNotFoundError:
                return None, None
            try:
                if not (stat.S_ISREG(info.st_mode) or (stat.S_ISLNK(info.st_mode)
                                                      and stat.S_ISREG(os.stat(startup).st_mode))):
                    return None, None
                with open(startup, "rb") as file:
                    data = file.read()
            except OSError:
                return None, None
            if begin.encode("ascii") not in data and end.encode("ascii") not in data:
                return None, None
            reparse = (getattr(info, "st_file_attributes", 0)
                       & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            if reparse or not stat.S_ISREG(info.st_mode):
                raise ValueError("it is a link")
            return data.decode("utf-8"), info  # UnicodeDecodeError: ValueError

        try:
            text, _ = read()
        except ValueError as ex:
            return False, "Left the EmOji-san lines in %s as they are (%s)." % (startup, ex)
        if text is None:
            return False, None
        lock_path = os.path.join(app_data, ".emoji-san-startup.lock")
        plain(lock_path)
        lock = QLockFile(lock_path)
        if not lock.tryLock(2000):
            raise OSError("could not lock QGIS's startup.py")
        try:
            try:
                text, info = read()
            except ValueError as ex:
                return False, "Left the EmOji-san lines in %s as they are (%s)." % (startup, ex)
            if text is None:
                return False, None
            lines = io.StringIO(text, newline="").readlines()
            starts = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == begin]
            ends = [i for i, line in enumerate(lines) if line.rstrip("\r\n") == end]
            if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
                return False, ("Left %s as it is: its EmOji-san lines are incomplete."
                               % startup)
            first, last = starts[0], ends[0] + 1
            block = [line.rstrip("\r\n") for line in lines[first:last]]

            def literal(prefix):
                for line in block:
                    if line.startswith(prefix):
                        try:
                            return ast.literal_eval(line[len(prefix):])
                        except (ValueError, SyntaxError):
                            return None
                return None

            loader = "    with open("
            loaded = [line[len(loader):-len(", 'rb') as _emoji_san:")] for line in block
                      if line.startswith(loader) and line.endswith(", 'rb') as _emoji_san:")]
            remove = False
            if loaded:  # the old, unguarded loader
                try:
                    path = ast.literal_eval(loaded[0])
                except (ValueError, SyntaxError):
                    path = None
                remove = (isinstance(path, str) and os.path.isabs(path)
                          and same(path, os.path.join(root, "embed_on_save.py")))
                if not remove:
                    return False, None
            else:
                if not unregister:
                    return False, None
                prefix = "# EmOji-san folders: "
                roots = literal(prefix)
                if not isinstance(roots, list):
                    return False, None  # written before the list: keep it
                remaining = [r for r in roots if isinstance(r, str) and not same(r, root)]
                if remaining == roots:
                    return False, None
                if remaining or "# EmOji-san: keep pre-registry profile support" in block:
                    index = first + next(i for i, line in enumerate(block)
                                         if line.startswith(prefix))
                    newline = lines[index][len(lines[index].rstrip("\r\n")):]
                    lines[index] = "%s%r%s" % (prefix, remaining, newline)
                else:
                    remove = True
            if remove:
                before, after = "".join(lines[:first]), "".join(lines[last:])
                separator = literal("# EmOji-san inserted separator: ")
                if separator in ("\n", "\r\n") and before.endswith(separator) and not after:
                    before = before[:-len(separator)]
                text = before + after
            else:
                text = "".join(lines)
            if not text:
                os.unlink(startup)
                cache = os.path.join(app_data, "__pycache__")
                if plain(cache, directory=True):
                    for name in os.listdir(cache):
                        if name.startswith("startup.") and name.endswith(".pyc"):
                            pyc = os.path.join(cache, name)
                            if plain(pyc):
                                os.unlink(pyc)
                    if not os.listdir(cache):
                        os.rmdir(cache)
                return True, None
            scratch = None
            try:
                with tempfile.NamedTemporaryFile(
                        mode="w", encoding="utf-8", newline="", dir=app_data,
                        prefix=".emoji-san-startup-", delete=False) as file:
                    scratch = file.name
                    file.write(text)
                    file.flush()
                    os.fsync(file.fileno())
                os.chmod(scratch, stat.S_IMODE(info.st_mode))
                os.replace(scratch, startup)
                scratch = None
            finally:
                if scratch is not None:
                    os.unlink(scratch)
            return True, None
        finally:
            lock.unlock()

    try:
        (root, manifest, svg_paths_key, _, registered_paths, same, plain,
         _, target, owned_files, other_profiles, acquire, clean_categories) = _emoji_san_storage()
        lock = acquire()
    except (OSError, ValueError) as ex:
        print("EmOji-san: %s" % ex)
        return

    try:
        transaction = os.path.join(os.path.dirname(root), ".EmOji-san.transaction")
        if plain(transaction, directory=True):
            print("EmOji-san: run the install line again to recover the "
                  "interrupted update before uninstalling.")
            return

        settings = QgsSettings()
        settings.sync()
        registered = registered_paths(settings.value(svg_paths_key, []))
        used_here = any(same(path, root) for path in registered)
        root_exists = plain(root, directory=True)
        shared = root_exists and other_profiles()
        owned = owned_files() if root_exists and not shared else set()
        # Check all paths before touching any owned file. The ownership
        # record stays until last so a partially completed uninstall can retry.
        assets = sorted(owned - {manifest, "index.csv"})
        for rel in assets + sorted(owned & {manifest, "index.csv"}):
            target(rel)

        done = settings.value(embed_key, False, type=bool)
        hook = getattr(builtins, "_emoji_san_embed_fn", None)
        if hook is not None:
            try:
                QgsProject.instance().writeMapLayer.disconnect(hook)
            except (TypeError, RuntimeError):
                pass
            builtins._emoji_san_embed_fn = None
            done = True
        if done or used_here or settings.contains(embed_key):
            settings.setValue(embed_key, False)
            settings.sync()
        tidied, note = tidy_startup(root, same, not shared)
        if note:
            print(note)
        if tidied:
            print("Removed EmOji-san's lines from startup.py")
            if shared:
                print("The old embedding setting was shared. In each profile "
                      "that needs it, run the install line with EMBED=True.")
            done = True

        left = False
        if shared:
            print("Shared SVGs kept because another QGIS profile uses them: %s" % root)
        elif root_exists:
            for rel in assets:
                dest = target(rel)
                if os.path.isfile(dest):
                    os.unlink(dest)
            clean_categories(assets)
            for rel in ("index.csv", manifest):
                if rel in owned:
                    dest = target(rel)
                    if os.path.isfile(dest):
                        os.unlink(dest)
            remaining = os.listdir(root)
            left = bool(remaining)
            if left:
                print("Kept files that EmOji-san does not manage in %s" % root)
            else:
                os.rmdir(root)
                print("Removed %s" % root)
            done = True

        keep = registered if left else [path for path in registered if not same(path, root)]
        if keep != registered:
            if hasattr(QgsApplication, "setSvgPaths"):
                QgsApplication.setSvgPaths(keep)
            else:
                settings.setValue(svg_paths_key, keep)
            settings.sync()
            done = True
        if not done:
            print("EmOji-san is not installed here (%s)." % root)
            return
    except (OSError, ValueError, csv.Error) as ex:
        print("EmOji-san: uninstall stopped (%s)" % ex)
        return
    finally:
        lock.unlock()

    style = QgsStyle.defaultStyle()
    try:  # QGIS 3
        entity = QgsStyle.SymbolEntity
    except AttributeError:  # QGIS 4
        entity = QgsStyle.StyleEntity.SymbolEntity
    tag = style.tagId(folder_name)
    tagged = len(style.symbolsWithTag(entity, tag)) if tag else 0
    if tagged:
        print("%d symbols tagged EmOji-san are still in the Style Manager. "
              "They carry their SVG inside and work without the folder." % tagged)
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
    del _emoji_san_uninstall, _emoji_san_storage
