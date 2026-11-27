# -*- coding: utf-8 -*-
# EmOji-san: Google Noto Emoji as SVG markers in QGIS.
#
# Run it from the QGIS Python console (Plugins > Python Console) with the
# one-line command in README.md.
#
# The SVG files go to <QGIS settings folder>/EmOji-san/<Category>/ and that
# folder is added to the SVG paths (Settings > Options > System). index.csv
# in the same folder lists the installed emoji.
#
# Options are variables set in front of the command. The console runs one
# line at a time, so they go on the same line, separated by ";". An option
# counts for that run only.
#
#   SET='M';      the set to install: 'S', 'M' or 'L' (S is part of M, M of L)
#   EMBED=True;   embed fixed EmOji-san SVGs on save; False turns it off
#   LOCALE='de';  language of the second name column in index.csv
#   ZIP='...';    read the files from a ZIP on disk instead of downloading
#
# Without SET, the first run installs S and later runs keep the selected set
# and previously installed SVGs. An explicit smaller set can remove files.
#
# EMBED=True opts this profile into embedding SVGs when projects are
# saved. QGIS loads the installer's marked startup.py block on launch,
# and the block checks the active profile's setting.
#
# The entry point runs on the last lines and removes its helpers from the
# console namespace.


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

    def installed_state(base=root):
        path = target(manifest, base)
        owned, selected = set(), None
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as file:
                record = json.load(file)
            if (not isinstance(record, dict) or record.get("format") != 1
                    or record.get("selected_set") not in (None, "S", "M", "L")
                    or not isinstance(record.get("files"), list)
                    or any(not isinstance(rel, str) or
                           (rel not in extras and not svg_path(rel))
                           for rel in record["files"])):
                raise ValueError("invalid EmOji-san ownership record: %s" % path)
            owned = set(record["files"]) | {manifest}
            selected = record.get("selected_set")
            if selected:
                return owned, selected

        # Old releases recorded the ranks in their installed CSV. Compare
        # against those ranks before consulting any data in the new release.
        path = target("index.csv", base)
        if (not owned or "index.csv" in owned) and os.path.isfile(path):
            with open(path, encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file)
                fields = [name for name in (reader.fieldnames or [])
                          if not name.startswith("name_")]
                if fields != ["emoji", "codepoint", "name", "category", "path",
                              "set", "noto_file"]:
                    raise ValueError("unrecognized EmOji-san index: %s" % path)
                rows = list(reader)
            ranks = ("S", "M", "L")
            if not rows or any(not svg_path(row["path"]) or row["set"] not in ranks
                               for row in rows):
                raise ValueError("invalid EmOji-san index: %s" % path)
            selected = max((row["set"] for row in rows), key=ranks.index)
            return owned or ({row["path"] for row in rows} | extras), selected

        # The P1 manifest still establishes ownership if the CSV is missing.
        if "README.txt" in owned:
            path = target("README.txt", base)
            if os.path.isfile(path):
                with open(path, encoding="utf-8") as file:
                    file.readline()
                    recorded = re.match(r"Set ([SML]), \d+ emoji\.", file.readline())
                if recorded:
                    selected = recorded.group(1)
        return owned, selected

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

    def acquire(base=root):
        path = os.path.join(os.path.dirname(base), ".EmOji-san.lock")
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
            path_info, target, installed_state, other_profiles, acquire, clean_categories)


def _emoji_san_transaction(root, checked_target, path_info):
    """Stage an install beside its destination and recover interrupted writes.

    The caller holds the install lock and validates every destination with
    checked_target. A published plan owns a complete, immutable set of
    backups until either the install or its rollback has finished.
    """
    import errno
    import json
    import os
    import re
    import shutil
    import stat

    parent = os.path.dirname(root)
    work = os.path.join(parent, "." + os.path.basename(root) + ".transaction")
    marker_name = "emoji-san-update"
    plan_name = "plan.json"
    committed_name = "committed"

    def path_mode(path):
        info = path_info(path)
        return info.st_mode if info is not None else None

    def regular_file(path):
        mode = path_mode(path)
        if mode is None:
            return False
        if not stat.S_ISREG(mode):
            raise ValueError("expected an ordinary file: %s" % path)
        return True

    def directory(path):
        mode = path_mode(path)
        if mode is None:
            return False
        if not stat.S_ISDIR(mode):
            raise ValueError("expected an ordinary directory: %s" % path)
        return True

    def sync_directory(path):
        # Windows cannot open directory file descriptors with os.open.
        if os.name != "nt":
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(fd)
            except OSError as error:
                if error.errno not in (errno.EINVAL, errno.ENOTSUP):
                    raise
            finally:
                os.close(fd)

    def target(rel):
        dest = checked_target(rel)
        if dest is None:
            raise ValueError("invalid transaction destination: %r" % rel)
        return dest

    def relative_dirs(rel):
        parts = rel.split("/")
        return ("/".join(parts[:i]) for i in range(len(parts)))

    def destination_dir(rel):
        return os.path.join(root, *rel.split("/")) if rel else root

    def local(name):
        return os.path.join(work, name)

    def journal_files():
        if not directory(work):
            return None
        names = set(os.listdir(work))
        for name in names:
            if (name not in (marker_name, plan_name, committed_name, "pending-plan",
                             "pending-commit", "restore")
                    and not re.fullmatch(r"(?:old|new)-[0-9]+", name)):
                raise ValueError("unexpected transaction file: %s" % local(name))
            if not regular_file(local(name)):
                raise OSError("transaction file disappeared: %s" % local(name))
        if names and (marker_name not in names or os.path.getsize(local(marker_name))):
            raise ValueError("unrecognized EmOji-san transaction directory: %s" % work)
        return names

    def remove_local(name):
        path = local(name)
        if os.name == "nt":
            os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
        os.remove(path)

    def discard(names):
        # The plan must disappear durably before any backup can disappear.
        if plan_name in names:
            remove_local(plan_name)
            sync_directory(work)
        for name in names - {plan_name, marker_name}:
            remove_local(name)
        if marker_name in names:
            remove_local(marker_name)
        os.rmdir(work)
        sync_directory(parent)

    def write_file(path, data):
        with open(path, "xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())

    def copy_file(source, dest):
        with open(source, "rb") as source_stream, open(dest, "xb") as dest_stream:
            shutil.copyfileobj(source_stream, dest_stream)
            dest_stream.flush()
            shutil.copystat(source, dest)
            os.fsync(dest_stream.fileno())

    def same_content(first, second):
        if os.path.getsize(first) != os.path.getsize(second):
            return False
        with open(first, "rb") as a, open(second, "rb") as b:
            return all(block == b.read(len(block))
                       for block in iter(lambda: a.read(65536), b""))

    def recover():
        names = journal_files()
        if names is None:
            return False
        if plan_name not in names or committed_name in names:
            discard(names)
            return False
        with open(local(plan_name), "rb") as stream:
            plan = json.loads(stream.read().decode("utf-8"))
        if not isinstance(plan, dict) or plan.get("version") != 1:
            raise ValueError("unknown EmOji-san transaction version")
        items = plan.get("items")
        dirs = plan.get("dirs")
        if (not isinstance(items, list) or not isinstance(dirs, list)
                or any(not isinstance(folder, str) for folder in dirs)):
            raise ValueError("invalid EmOji-san transaction plan")
        paths = set()
        for number, item in enumerate(items):
            if not (isinstance(item, list) and len(item) == 2
                    and isinstance(item[0], str) and isinstance(item[1], bool)):
                raise ValueError("invalid EmOji-san transaction item: %r" % item)
            rel, had_file = item
            target(rel)
            if rel in paths:
                raise ValueError("duplicate EmOji-san transaction item: %r" % rel)
            paths.add(rel)
            if had_file and "old-%d" % number not in names:
                raise ValueError("missing EmOji-san transaction backup: %r" % rel)
        parents = {folder for rel in paths for folder in relative_dirs(rel)}
        if not set(dirs).issubset(parents):
            raise ValueError("invalid EmOji-san transaction folders")

        # Restore data before the former index; backups stay intact so this
        # can run again if interrupted at any step. Only dirs we created can
        # be removed, and only if still empty.
        restore = local("restore")
        for number, (rel, had_file) in enumerate(items):
            dest = target(rel)
            exists = regular_file(dest)
            if had_file:
                backup = local("old-%d" % number)
                if exists and same_content(backup, dest):
                    continue
                if regular_file(restore):
                    remove_local("restore")
                copy_file(backup, restore)
                os.replace(restore, dest)
            elif exists:
                os.remove(dest)
            else:
                continue
            sync_directory(os.path.dirname(dest))
        for rel in sorted(dirs, key=lambda path: (path.count("/"), path), reverse=True):
            dest = destination_dir(rel)
            if directory(dest):
                try:
                    os.rmdir(dest)
                except OSError as error:
                    if error.errno not in (errno.ENOTEMPTY, errno.EEXIST):
                        raise
                else:
                    sync_directory(os.path.dirname(dest))
        discard(journal_files())
        return True

    def apply(writes, deletes):
        recover()
        deletes = sorted(set(deletes))
        if set(writes).intersection(deletes):
            raise ValueError("the same file cannot be replaced and removed")
        items = []
        dirs = set()
        # Publish the file inventory only after all of its assets.
        metadata = ("index.csv", ".emoji-san-owned.json")
        paths = list(writes) + deletes
        paths = [rel for rel in paths if rel not in metadata] + [
            rel for rel in paths if rel in metadata]
        for rel in paths:
            dest = target(rel)
            exists = regular_file(dest)
            if rel in writes:
                if exists:
                    with open(dest, "rb") as stream:
                        if stream.read() == writes[rel]:
                            continue
                dirs.update(folder for folder in relative_dirs(rel)
                            if not directory(destination_dir(folder)))
            elif not exists:
                continue
            items.append((rel, exists))
        if not items:
            return
        dirs = sorted(dirs, key=lambda path: (path.count("/"), path))

        os.mkdir(work, 0o700)
        try:
            write_file(local(marker_name), b"")
            sync_directory(parent)
            for number, (rel, had_file) in enumerate(items):
                dest = target(rel)
                if regular_file(dest) != had_file:
                    raise OSError("file changed while preparing install: %s" % dest)
                if had_file:
                    copy_file(dest, local("old-%d" % number))
                if rel in writes:
                    write_file(local("new-%d" % number), writes[rel])
            write_file(local("pending-commit"), b"")
            write_file(local("pending-plan"), json.dumps({
                "version": 1, "items": items, "dirs": dirs,
            }).encode("utf-8"))
            os.replace(local("pending-plan"), local(plan_name))
            sync_directory(work)

            for rel in dirs:
                dest = destination_dir(rel)
                os.mkdir(dest)
                sync_directory(os.path.dirname(dest))
            for number, (rel, had_file) in enumerate(items):
                dest = target(rel)
                if regular_file(dest) != had_file:
                    raise OSError("file changed while installing: %s" % dest)
                if rel in writes:
                    os.replace(local("new-%d" % number), dest)
                else:
                    os.remove(dest)
                sync_directory(os.path.dirname(dest))
            os.replace(local("pending-commit"), local(committed_name))
            sync_directory(work)
        except BaseException:
            try:
                recover()
            except Exception as error:
                raise OSError("incomplete recovery; run the install line again: %s"
                              % error) from error
            raise
        discard(journal_files())

    return recover, apply


def _emoji_san_install(ns):
    import csv
    import hashlib
    import io
    import json
    import os
    import re
    import urllib.error
    import urllib.request
    import zipfile

    from qgis.core import QgsApplication, QgsSettings

    REPO = "yfuru2454/emoji-san"
    TAG = "v1.1.0"  # the release this script installs
    DATA_SHA256 = None
    CLDR = ("https://raw.githubusercontent.com/unicode-org/cldr-json/49.0.0/"
            "cldr-json/")
    SETS = ("S", "M", "L")
    FOLDER = "EmOji-san"
    EXTRAS = ("LICENSE-noto-emoji.txt", "LICENSE-gemoji.txt", "NOTICE",
              "UPSTREAM_COMMIT.txt")
    # what installs from before the ownership record have; for recognizing them
    LEGACY_EXTRAS = ("LICENSE-noto-emoji.txt", "NOTICE", "UPSTREAM_COMMIT.txt")
    README_START = "EmOji-san: Google Noto Emoji (Apache-2.0) as SVG markers for QGIS.\n"
    README_PATHS = ('\nindex.csv lists the emoji. "path" is relative to this folder, '
                    'which is\nalso how QGIS writes it into a project, for example '
                    '"Food and Drink/hot_beverage.svg".\n')
    README_END = "\nhttps://github.com/%s\n" % REPO
    LEGACY_HOOK_SHA256 = "05397913f1757cfcba4488b08e5861cf3a1f1894a38d374935dd1d17befaf65c"
    BEGIN = "# >>> EmOji-san: embed EmOji-san SVGs when saving projects >>>"
    END = "# <<< EmOji-san <<<"
    # The greeting is "ojisan-kobun" in a Japanese QGIS (the emoji-laden
    # way middle-aged men text) and signed like a dad elsewhere. The line
    # printed after it is the plain one to quote in a bug report.
    GREETINGS = {
        "ja": {
            "first": "EmOji-san👨‍💼参上❗ %(n)d個の絵文字をお届けしたヨ😃✨ "
                     "地図がにぎやかになるネ🗾💕",
            "up": "おっ、%(set)sサイズにアップグレードだネ❗ %(added)d個も"
                  "増えちゃった😆💕",
            "down": "%(set)sサイズに戻したんだネ😅 %(removed)d個とお別れ、"
                    "ちょっと寂しいけど了解だヨ💦",
            "update": "最新版にアップデート完了だヨ❗ 絵文字もピカピカだネ😆✨",
            "same": "特に変わりなしだヨ❗ 今日も地図作り、がんばってネ💪✨",
        },
        "en": {
            "first": "%(n)d emoji delivered❗ Have fun with your maps 😃✨🗺️💕 "
                     "Love, EmOji-san 👨‍💼😘",
            "up": "Upgraded to size %(set)s❗ %(added)d more emoji for you "
                  "😆👍🎉 Love, EmOji-san 👨‍💼😘",
            "down": "Back to size %(set)s 😅 %(removed)d emoji said goodbye "
                    "😢💦 Love, EmOji-san 👨‍💼",
            "update": "Updated to the latest❗ Shiny new emoji for you 😆✨ "
                      "Love, EmOji-san 👨‍💼😘",
            "same": "All up to date❗ Keep up the good work on your maps 💪✨😉 "
                    "Love, EmOji-san 👨‍💼",
        },
    }

    # --- options: taken out of the console's namespace --------------------
    size = ns.pop("SET", None)
    embed = ns.pop("EMBED", None)
    language = ns.pop("LOCALE", None)
    source = str(ns.pop("ZIP", None) or (
        "https://github.com/%s/releases/download/%s/emoji_san_data.zip" % (REPO, TAG)))
    if size is not None:
        if str(size).strip().upper() not in SETS:
            print("EmOji-san: SET is 'S', 'M' or 'L', not %r. "
                  "Nothing changed." % (size,))
            return
        size = str(size).strip().upper()
    if embed not in (None, True, False):
        print("EmOji-san: EMBED is True or False, not %r. Nothing changed."
              % (embed,))
        return

    # --- where things go --------------------------------------------------
    # <settings folder>/profiles/<profile>/  ->  <settings folder>/EmOji-san
    # Not inside the profile: the SVG browser files every SVG path inside a
    # profile under "User Symbols", and this way all profiles share one copy.
    try:
        (root, manifest, SVG_PATHS, svg_path, registered_paths, same, plain,
         path_info, target, installed_state, other_profiles, acquire,
         clean_categories) = _emoji_san_storage()
    except (OSError, ValueError) as ex:
        print("EmOji-san: %s" % ex)
        return

    # The language QGIS runs in, e.g. "ja" or "pt_BR". QGIS stores it in
    # locale/userLocale at every start, also when it just follows the system.
    ui = str(QgsSettings().value("locale/userLocale", "")
             or QgsApplication.locale() or "en")

    def read_archive():
        # Read all required members before updating live data. Only these
        # named data members are consumed, and archive size is bounded.
        max_zip = 64 * 1024 * 1024
        max_member = 8 * 1024 * 1024
        print("EmOji-san: getting %s" % source)
        if "://" in source:
            from urllib.parse import urlsplit

            url = urlsplit(source)
            local_file = url.scheme == "file" and url.netloc.lower() in ("", "localhost")
            if not local_file and (url.scheme != "https" or DATA_SHA256 is None):
                raise ValueError("use the release installer for HTTPS or provide a local ZIP")
            with urllib.request.urlopen(source, timeout=120) as reply:
                blob = reply.read(max_zip + 1)
        else:
            with open(source, "rb") as file:
                blob = file.read(max_zip + 1)
        if len(blob) > max_zip:
            raise ValueError("ZIP exceeds the download size limit")
        if DATA_SHA256 is not None and hashlib.sha256(blob).hexdigest() != DATA_SHA256:
            raise ValueError("release ZIP SHA-256 does not match the installer")
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            members = archive.namelist()
            indexes = [name for name in members if name == "index.csv" or
                       (name.count("/") == 1 and name.endswith("/index.csv"))]
            if len(indexes) != 1 or len(set(members)) != len(members):
                raise ValueError("ZIP must have one index.csv and unique member names")
            top = indexes[0][:-len("index.csv")]
            total = 0

            def data(name):
                nonlocal total
                item = archive.getinfo(top + name)
                total += item.file_size
                if item.file_size > max_member or total > 2 * max_zip:
                    raise ValueError("ZIP exceeds the expanded size limit")
                return archive.read(item)

            reader = csv.DictReader(io.StringIO(data("index.csv").decode("utf-8")))
            required = {"emoji", "codepoint", "name", "category", "path", "set",
                        "noto_file", "collection"}
            if set(reader.fieldnames or []) != required or len(reader.fieldnames) != len(required):
                raise ValueError("invalid ZIP index.csv header")
            rows = list(reader)
            if not rows or any(None in row or any(value is None for value in row.values())
                               or row["set"] not in SETS or not svg_path(row["path"])
                               or row["collection"] not in ("map", "people") for row in rows):
                raise ValueError("invalid ZIP index.csv rows")
            paths = {row["path"].casefold() for row in rows}
            if len(paths) != len(rows) or not any(row["set"] == "S" for row in rows):
                raise ValueError("ZIP index.csv must have unique paths and an S set")
            assets = {row["path"]: data("collections/noto_emoji_%s/svg/%s" %
                       (row["collection"], row["path"])) for row in rows}
            assets.update((name, data(name)) for name in EXTRAS)
        return rows, assets

    def restore_legacy_state(location, rows, assets):
        """Recover the pre-manifest receipt only when the release matches it."""
        receipt = target("README.txt", location)
        if not os.path.isfile(receipt):
            return set(), None
        with open(receipt, encoding="utf-8") as file:
            description = file.read(4097)
        pattern = (re.escape(README_START)
                   + r"Set ([SML]), ([1-9][0-9]{0,6}) emoji\. This folder is one of the QGIS SVG paths\.\n"
                   + re.escape(README_PATHS)
                   + r'(?:"name_[\w-]+" is the name in the language of this QGIS \(Unicode CLDR\)\.\n)?'
                   + re.escape(README_END))
        match = re.fullmatch(pattern, description)
        if not match:
            return set(), None
        selected, count = match.groups()
        rank = SETS.index(selected)
        candidates = {row["path"] for row in rows if SETS.index(row["set"]) <= rank}

        def matches_packaged_file(rel):
            path, content = target(rel, location), assets[rel]
            if not os.path.isfile(path):
                return False
            with open(path, "rb") as file:
                return file.read(len(content) + 1) == content

        if len(candidates) != int(count) or not all(matches_packaged_file(rel)
                                                     for rel in LEGACY_EXTRAS):
            raise ValueError("cannot recover the old index.csv from this release; use the "
                             "original matching ZIP or restore the old index.csv")
        owned = {rel for rel in candidates if matches_packaged_file(rel)}
        if not owned:
            raise ValueError("cannot recover the old index.csv without verified SVGs")
        owned.update(LEGACY_EXTRAS)
        owned.add("README.txt")
        # Only reclaim the known pre-manifest save hook. Never execute it.
        legacy_hook = target("embed_on_save.py", location)
        if os.path.isfile(legacy_hook):
            with open(legacy_hook, "rb") as file:
                if hashlib.sha256(file.read(65537)).hexdigest() == LEGACY_HOOK_SHA256:
                    owned.add("embed_on_save.py")
        return owned, selected

    def has_unmanaged_files(location, owned):
        def unreadable(error):
            raise error

        try:
            for parent, directories, files in os.walk(location, onerror=unreadable):
                if any(not plain(os.path.join(parent, name), directory=True)
                       for name in directories):
                    return True
                for name in files:
                    path = os.path.join(parent, name)
                    rel = os.path.relpath(path, location).replace(os.sep, "/")
                    if rel not in owned and name not in (".DS_Store", "Thumbs.db", "desktop.ini"):
                        return True
        except (OSError, ValueError):
            return True
        return False

    # --- embedding on save ------------------------------------------------
    # This source is part of the installer, and is also copied into the QGIS
    # startup block when a profile opts in. The data ZIP supplies no code.
    hook_source = '''\
import base64
import builtins
import os

from qgis.core import (QgsApplication, QgsMessageLog, QgsProject, QgsSettings,
                       QgsSymbolLayerUtils)


def _spots(node):
    """Yield XML elements and attributes containing static SVG references."""
    svg_property = {"SvgMarker": "name", "SVGFill": "svgFile"}
    layers = node.elementsByTagName("layer")
    for i in range(layers.count()):
        layer = layers.at(i).toElement()
        prop = svg_property.get(layer.attribute("class"))
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


def _on_write_layer(layer, element, document):
    # The layer style is already in the DOM. Change the saved project only.
    try:
        if not QgsSettings().value("emoji-san/embedOnSave", False, type=bool):
            return
        profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
        parent = os.path.realpath(os.path.dirname(os.path.dirname(profile)))
        folder = os.path.join(parent, "EmOji-san")
        root = os.path.normcase(folder)
        if os.path.normcase(os.path.realpath(folder)) != root:
            return
        resolver = QgsProject.instance().pathResolver()
        encoded = {}
        for node, attribute in _spots(element):
            value = node.attribute(attribute)
            if not value or value.startswith("base64:"):
                continue
            path = QgsSymbolLayerUtils.svgSymbolNameToPath(value, resolver)
            if not path or not path.lower().endswith(".svg"):
                continue
            path = os.path.realpath(path)
            if not os.path.normcase(path).startswith(root + os.sep):
                continue
            if not os.path.isfile(path):
                continue
            if path not in encoded:
                with open(path, "rb") as f:
                    encoded[path] = "base64:" + base64.b64encode(
                        f.read()).decode("ascii")
            node.setAttribute(attribute, encoded[path])
    except Exception as ex:  # saving the project comes first
        QgsMessageLog.logMessage("embedding failed: %s" % ex, "EmOji-san")


_signal = QgsProject.instance().writeMapLayer
_signal.connect(_on_write_layer)
_old_hook = getattr(builtins, "_emoji_san_embed_fn", None)
if _old_hook is not None:
    try:
        _signal.disconnect(_old_hook)
    except (TypeError, RuntimeError):
        pass
builtins._emoji_san_embed_fn = _on_write_layer
'''

    def set_embed(option):
        """Switch the active profile's save hook and return (was, now)."""
        import ast
        import builtins
        import stat
        import tempfile
        import textwrap

        from qgis.core import QgsProject
        from qgis.PyQt.QtCore import QLockFile, QStandardPaths

        key = "emoji-san/embedOnSave"
        settings = QgsSettings()
        was = settings.value(key, False, type=bool)
        stored = settings.contains(key)

        def disconnect():
            hook = getattr(builtins, "_emoji_san_embed_fn", None)
            if hook is not None:
                try:
                    QgsProject.instance().writeMapLayer.disconnect(hook)
                except (TypeError, RuntimeError):
                    pass
                builtins._emoji_san_embed_fn = None

        explicit_off = option is not None and not option
        if explicit_off:
            settings.setValue(key, False)
            settings.sync()
            disconnect()

        def regular_file(path):
            try:
                info = os.lstat(path)
            except FileNotFoundError:
                return None
            reparse = (getattr(info, "st_file_attributes", 0)
                       & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            if reparse or not stat.S_ISREG(info.st_mode):
                raise ValueError("expected a regular file: %s" % path)
            return info

        def startup_parts(path):
            """(head, block, tail, info) of a startup.py. info is None when
            there is no file, and "unusable" for one EmOji-san must not
            edit: a link, another kind of file, or text that is not UTF-8.
            Such a file is left alone unless it holds EmOji-san's lines."""
            try:
                info = os.lstat(path)
            except FileNotFoundError:
                return "", "", "", None
            reparse = (getattr(info, "st_file_attributes", 0)
                       & stat.FILE_ATTRIBUTE_REPARSE_POINT)
            data = b""
            try:
                if stat.S_ISREG(info.st_mode) or (stat.S_ISLNK(info.st_mode)
                                                  and stat.S_ISREG(os.stat(path).st_mode)):
                    with open(path, "rb") as f:
                        data = f.read()
                if reparse or not stat.S_ISREG(info.st_mode):
                    raise ValueError("not an ordinary file")
                text = data.decode("utf-8")
            except (OSError, ValueError):
                if BEGIN.encode("ascii") in data or END.encode("ascii") in data:
                    raise ValueError("EmOji-san cannot edit its lines in %s: "
                                     "it is a link or not UTF-8 text" % path)
                return "", "", "", "unusable"
            lines = io.StringIO(text, newline="").readlines()
            starts = [i for i, line in enumerate(lines)
                      if line.rstrip("\r\n") == BEGIN]
            ends = [i for i, line in enumerate(lines)
                    if line.rstrip("\r\n") == END]
            if not starts and not ends:
                return "".join(lines), "", "", info
            if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
                raise ValueError("incomplete EmOji-san startup block: %s"
                                 % path)
            start, end = starts[0], ends[0] + 1
            return ("".join(lines[:start]), "".join(lines[start:end]),
                    "".join(lines[end:]), info)

        registry_prefix = "# EmOji-san folders: "
        separator_prefix = "# EmOji-san inserted separator: "
        unlisted_profiles = "# EmOji-san: keep pre-registry profile support"

        def registry(block):
            """Folders recorded in a block, or None if it records none."""
            for line in block.splitlines():
                if line.startswith(registry_prefix):
                    try:
                        roots = ast.literal_eval(line[len(registry_prefix):])
                    except (ValueError, SyntaxError):
                        return None
                    if isinstance(roots, list) and all(
                            isinstance(r, str) and os.path.isabs(r) for r in roots):
                        return roots
                    return None
            return None

        def legacy_root(block):
            # Recognize the old loader and our inert path marker. The old
            # script and any other text from startup.py are never executed here.
            prefix = "    with open("
            suffix = ", 'rb') as _emoji_san:"
            marker = "    legacy_emoji_root = "
            for line in block.splitlines():
                loader = line.startswith(prefix) and line.endswith(suffix)
                if loader:
                    value = line[len(prefix):-len(suffix)]
                elif line.startswith(marker):
                    value = line[len(marker):]
                else:
                    continue
                try:
                    path = ast.literal_eval(value)
                except (ValueError, SyntaxError):
                    continue
                if not isinstance(path, str) or "\0" in path or not os.path.isabs(path):
                    continue
                path = os.path.normpath(path)
                if loader:
                    if os.path.basename(path) != "embed_on_save.py":
                        continue
                    path = os.path.dirname(path)
                if os.path.basename(path) == FOLDER:
                    return path
            return None

        try:  # Qt 5
            where = QStandardPaths.AppDataLocation
        except AttributeError:  # Qt 6
            where = QStandardPaths.StandardLocation.AppDataLocation
        app_data = QStandardPaths.writableLocation(where)
        if not app_data:
            raise ValueError("QGIS's startup folder could not be located")
        app_data = os.path.realpath(app_data)
        startup = os.path.join(app_data, "startup.py")
        _, existing, _, _ = startup_parts(startup)
        if not stored and not explicit_off:
            # Only a profile registered with an existing installation can
            # inherit a legacy opt-in from the old app-wide startup block.
            registered_here = any(same(path, root) for path in registered)
            previous_root = legacy_root(existing)
            was = (registered_here
                   and previous_root is not None and same(previous_root, root))
            if not was and option is None and not registered_here:
                for path in elsewhere:
                    other = os.path.join(os.path.dirname(path), "startup.py")
                    previous_root = legacy_root(startup_parts(other)[1])
                    if previous_root is not None and same(previous_root, path):
                        was = True
                        break
        on = was if option is None else bool(option)
        if not on and not explicit_off:
            disconnect()
            # A new registration in a legacy root is still an opt-out. On
            # restart it must not inherit the old app-wide default.
            if not stored:
                settings.setValue(key, False)
                settings.sync()

        # Keep the guarded block after disabling so it still works for other
        # profiles, including profiles under a custom --profiles-path.
        def startup_code(block, separator=""):
            # Uninstall removes the block once no recorded folder needs it.
            # A block from before this record could serve any folder.
            roots = registry(block)
            block_lines = block.splitlines()
            keep_unlisted = (unlisted_profiles in block_lines or
                             (roots is None and "def _emoji_san_startup():" in block_lines))
            if roots is None:
                roots = [root] if block else []
            # the folder of an old loader keeps its profiles' opt-in
            for folder in (legacy_root(block), root if on else None):
                if folder and not any(same(r, folder) for r in roots):
                    roots = roots + [folder]
            separator_line = next((line for line in block_lines
                                   if line in (separator_prefix + repr("\n"),
                                               separator_prefix + repr("\r\n"))), "")
            if separator:
                separator_line = separator_prefix + repr(separator)
            return (
                "%s\n"
                "%s%r\n"
                "%s"
                "%s"
                "def _emoji_san_startup():\n"
                "    import os\n"
                "    from qgis.core import QgsApplication, QgsSettings\n"
                "    legacy_emoji_root = %r\n"
                "    settings = QgsSettings()\n"
                "    enabled = settings.value(%r, False, type=bool)\n"
                "    if legacy_emoji_root and not settings.contains(%r):\n"
                "        profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())\n"
                "        folder = os.path.join(os.path.dirname(os.path.dirname(profile)), %r)\n"
                "        paths = settings.value(%r, []) or []\n"
                "        if isinstance(paths, str):\n"
                "            paths = [paths]\n"
                "        def same_path(path):\n"
                "            if not isinstance(path, str) or not path:\n"
                "                return False\n"
                "            try:\n"
                "                return os.path.samefile(path, legacy_emoji_root)\n"
                "            except OSError:\n"
                "                return False\n"
                "        enabled = same_path(folder) and any(same_path(path) for path in paths)\n"
                "        if enabled:\n"
                "            settings.setValue(%r, True)\n"
                "            settings.sync()\n"
                "    if enabled:\n"
                "%s"
                "try:\n"
                "    _emoji_san_startup()\n"
                "except Exception as _emoji_san_error:\n"
                "    from qgis.core import QgsMessageLog as _emoji_san_log\n"
                "    _emoji_san_log.logMessage(\n"
                "        'embedding on startup failed: %%s' %% _emoji_san_error,\n"
                "        'EmOji-san')\n"
                "    del _emoji_san_log\n"
                "finally:\n"
                "    del _emoji_san_startup\n"
                "%s\n" % (BEGIN, registry_prefix, roots,
                           unlisted_profiles + "\n" if keep_unlisted else "",
                           separator_line + "\n" if separator_line else "",
                           legacy_root(block), key, key,
                           FOLDER, SVG_PATHS, key,
                           textwrap.indent(hook_source, "        "), END))
        launch = startup_code(existing)
        if ((on or existing)
                and existing.replace("\r\n", "\n") != launch):
            os.makedirs(app_data, exist_ok=True)
            lock_path = os.path.join(app_data, ".emoji-san-startup.lock")
            regular_file(lock_path)
            lock = QLockFile(lock_path)
            lock.setStaleLockTime(0)
            if not lock.tryLock(2000):
                raise OSError("could not lock QGIS's startup.py")
            try:
                head, existing, tail, info = startup_parts(startup)
                if info == "unusable":
                    raise ValueError("cannot add the embedding lines to %s: it "
                                     "is a link or not UTF-8 text" % startup)
                newline = "\r\n" if "\r\n" in head + existing + tail else "\n"
                separator = newline if head and not head.endswith(("\n", "\r")) else ""
                # The loader of the release before put a blank line between
                # the user's lines and its own. Record it, so that uninstall
                # gives the user's file back without that line.
                record = separator
                old_loader = ("def _emoji_san_startup():" not in existing
                              and legacy_root(existing) is not None)
                if (not record and old_loader and head.strip()
                        and head.endswith(newline * 2)):
                    record = newline
                launch = startup_code(existing, record)
                if existing.replace("\r\n", "\n") != launch:
                    compile(launch, "<EmOji-san startup block>", "exec")
                    text = head + separator + launch.replace("\n", newline) + tail
                    scratch = None
                    try:
                        with tempfile.NamedTemporaryFile(
                                mode="w", encoding="utf-8", newline="",
                                prefix=".emoji-san-startup-", dir=app_data,
                                delete=False) as f:
                            scratch = f.name
                            f.write(text)
                            f.flush()
                            os.fsync(f.fileno())
                        if info is not None:  # an ordinary file
                            os.chmod(scratch, stat.S_IMODE(info.st_mode))
                        os.replace(scratch, startup)
                        scratch = None
                    finally:
                        if scratch is not None:
                            os.unlink(scratch)
            finally:
                lock.unlock()
        if on:
            exec(compile(hook_source, "<EmOji-san save hook>", "exec"), {})
            settings.setValue(key, True)
            settings.sync()
        return was, on

    try:
        lock = acquire()
    except (OSError, ValueError) as ex:
        print("EmOji-san: %s" % ex)
        return
    source_lock = None
    try:
        recover, apply = _emoji_san_transaction(root, target, path_info)
        if recover():
            print("EmOji-san: recovered an interrupted update")
        try:
            rows, assets = read_archive()
        except Exception as ex:
            print("EmOji-san: could not get the files (%s: %s). Nothing changed."
                  % (type(ex).__name__, ex))
            if "://" in source:
                print("  If QGIS cannot reach GitHub, there is another way: "
                      "https://github.com/%s#without-internet-access-from-qgis" % REPO)
            return

        owned, previous = installed_state()
        recovered_index = False
        if not owned:
            owned, previous = restore_legacy_state(root, rows, assets)
            recovered_index = previous is not None
        settings = QgsSettings()
        settings.sync()
        registered = registered_paths(settings.value(SVG_PATHS, []))
        # Only the standard QGIS 3 sibling can be the source of QGIS 4's
        # profile migration. Disconnected and custom libraries stay registered.
        home = os.path.dirname(root)
        older = os.path.join(os.path.dirname(home), "QGIS3", FOLDER)
        elsewhere, migrated_paths, inherited = [], [], []
        if os.path.basename(home).casefold() == "qgis4":
            candidates = [path for path in registered if same(path, older)]
            if candidates:
                try:
                    if plain(older, directory=True):
                        source_lock = acquire(older)
                        pending = os.path.join(os.path.dirname(older), ".EmOji-san.transaction")
                        if os.path.lexists(pending):
                            raise ValueError("the older QGIS installation has a pending update")
                        old_owned, old_size = installed_state(older)
                        if not old_owned:
                            old_owned, old_size = restore_legacy_state(older, rows, assets)
                        if old_size and any(svg_path(rel) and os.path.isfile(target(rel, older))
                                            for rel in old_owned):
                            elsewhere = [older]
                            inherited = [(older, old_owned, old_size)]
                            if not has_unmanaged_files(older, old_owned):
                                migrated_paths = candidates
                except (OSError, ValueError, csv.Error) as ex:
                    print("  kept the previous SVG path because it could not be migrated (%s)" % ex)

        installed_svgs = {rel for rel in owned if svg_path(rel)
                          and os.path.isfile(target(rel))}
        here = bool(installed_svgs)
        installed_sets = [selected for _, _, selected in inherited]
        if previous:
            installed_sets.append(previous)
        prev = max(installed_sets, key=SETS.index) if installed_sets else None
        size = size or prev or SETS[0]
        rank = SETS.index(size)
        downgrade = prev is not None and rank < SETS.index(prev)
        wanted = [row for row in rows if SETS.index(row["set"]) <= rank]
        desired_svgs = {row["path"] for row in wanted}
        old_spellings = {rel.casefold(): rel for rel in owned if svg_path(rel)}
        for rel in sorted(desired_svgs - owned):
            if rel.casefold() in old_spellings:
                raise ValueError("SVG path only changes case: %s" % rel)
        # Changes to set membership or the upstream catalog must not break
        # references in existing projects. Only a deliberate downgrade prunes.
        outside_set = installed_svgs - desired_svgs
        obsolete = outside_set if downgrade else set()
        retained = outside_set - obsolete
        if obsolete and other_profiles():
            print("EmOji-san: other QGIS profiles use this copy. "
                  "This update would remove shared SVGs. Nothing changed.")
            return
        legacy_hook = ("embed_on_save.py" in owned
                       and os.path.isfile(target("embed_on_save.py")))
        carried = {}
        if not downgrade:
            desired_names = {rel.casefold(): rel for rel in desired_svgs}
            for location, inherited_files, _ in inherited:
                for rel in sorted(inherited_files):
                    if not svg_path(rel) or rel in desired_svgs or rel in carried:
                        continue
                    if rel.casefold() in desired_names:
                        raise ValueError("SVG path only changes case: %s" % rel)
                    path = target(rel, location)
                    if os.path.isfile(path):
                        with open(path, "rb") as file:
                            limit = 8 * 1024 * 1024
                            content = file.read(limit + 1)
                        if len(content) > limit:
                            raise ValueError("SVG is too large to carry over: %s" % path)
                        carried[rel] = content
                        desired_names[rel.casefold()] = rel

        # --- index.csv --------------------------------------------------------
        def local_names():
            """(code, {emoji: name}, problem) from Unicode CLDR, for the second
            name column. English has none to add.

            A CLDR file holds only what differs from its parent locale: "es-MX"
            has a fifth of the names, the rest are in "es-419" and "es". So the
            names are read from the most general locale to the most specific.
            """
            tag = str(language or ui).replace("_", "-")
            tag = tag.replace("@latin", "-Latn")
            parts = tag.split("-")
            if parts[0].lower() in ("en", "c", ""):
                return "en", {}, None
            if parts[0].lower() == "zh" and parts[-1].upper() in ("TW", "HK",
                                                                  "MO"):
                tag = "zh-Hant-" + parts[-1].upper()  # traditional characters

            def fetch(path):
                with urllib.request.urlopen(CLDR + path, timeout=30) as reply:
                    return json.loads(reply.read().decode("utf-8"))

            names, found = {}, None
            try:
                parents = fetch("cldr-core/supplemental/parentLocales.json")[
                    "supplemental"]["parentLocales"]["parentLocale"]
                chain = []  # "es-MX", "es-419", "es"
                while tag and tag not in ("und", "root"):
                    chain.append(tag)
                    tag = parents.get(tag) or tag.rpartition("-")[0]
                for code in reversed(chain):
                    for package, key in (("annotations", "annotations"),
                                         ("annotations-derived",
                                          "annotationsDerived")):
                        try:
                            data = fetch("cldr-%s-full/%s/%s/annotations.json"
                                         % (package, key, code))
                        except urllib.error.HTTPError as error:
                            error.close()
                            if error.code != 404:
                                raise  # not "no such file": reported below
                            continue  # CLDR has no file for this locale
                        found = code
                        for emoji, entry in data[key]["annotations"].items():
                            if entry.get("tts"):
                                names[emoji] = entry["tts"][0]
            except Exception as ex:  # offline, timeout, ...
                return parts[0], {}, "%s: %s" % (type(ex).__name__, ex)
            if names:
                return found, names, None
            return parts[0], {}, ("Unicode CLDR has no emoji names for %r"
                                  % (chain[0] if chain else parts[0]))

        code, names, problem = local_names()
        column = "name_" + code if names else None
        fields = ["emoji", "codepoint", "name"] + ([column] if column else [])
        fields += ["category", "path", "set", "noto_file"]
        for r in wanted:
            if column:  # CLDR lists most emoji without the U+FE0F selector
                e = r["emoji"]
                r[column] = names.get(e) or names.get(e.replace(chr(0xFE0F), ""),
                                                      "")
        listing = io.StringIO(newline="")
        writer = csv.DictWriter(listing, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(wanted)
        readme = (README_START + "Set %s, %d emoji. This folder is one of the QGIS SVG paths.\n"
                  % (size, len(wanted)) + README_PATHS)
        if column:
            readme += ("\"%s\" is the name in the language of this QGIS "
                       "(Unicode CLDR).\n" % column)
        kept = len(retained | set(carried))
        if kept:
            readme += ("%d previously installed SVGs are also kept for existing projects.\n"
                       % kept)
        readme += README_END

        expected = {rel: assets[rel] for rel in sorted(desired_svgs)}
        expected.update(carried)
        expected.update((name, assets[name]) for name in EXTRAS)
        expected["README.txt"] = readme.encode("utf-8")
        expected["index.csv"] = listing.getvalue().encode("utf-8")
        writes = {}
        managed = set(retained)
        if legacy_hook:
            managed.add("embed_on_save.py")
        added = changed = 0
        for rel, content in expected.items():
            dest = target(rel)
            if os.path.isfile(dest):
                with open(dest, "rb") as file:
                    matches = file.read() == content
                if rel not in owned:
                    if not matches:
                        raise ValueError("file is not managed by EmOji-san: %s" % dest)
                    # A user's identical file can be used without claiming it.
                    if rel == "index.csv":
                        raise ValueError("index.csv is not managed by EmOji-san: %s" % dest)
                    continue
                if not matches:
                    writes[rel] = content
                    changed += svg_path(rel)
            else:
                writes[rel] = content
                added += svg_path(rel)
            managed.add(rel)
        writes[manifest] = (json.dumps({"format": 1, "files": sorted(managed),
                                       "selected_set": size})
                            + "\n").encode("utf-8")
        deleted_svgs = {rel for rel in obsolete if svg_path(rel)}
        removed = len(deleted_svgs)
        apply(writes, obsolete)
        if recovered_index:
            print("  recovered the legacy set and rebuilt index.csv")
        try:
            clean_categories(deleted_svgs)
        except (OSError, ValueError) as ex:
            print("EmOji-san: could not tidy empty categories (%s)" % ex)

        # --- SVG path -----------------------------------------------------
        paths = [p for p in registered if p not in migrated_paths]
        newly = not any(same(p, root) for p in paths)
        if newly:
            # A retained old library is a fallback for user-owned SVGs.
            first_old = next((i for i, p in enumerate(paths) if elsewhere and same(p, older)),
                             len(paths))
            paths.insert(first_old, root.replace(os.sep, "/"))
        if paths != registered:
            if hasattr(QgsApplication, "setSvgPaths"):
                QgsApplication.setSvgPaths(paths)
            else:
                settings.setValue(SVG_PATHS, paths)
            settings.sync()
        try:
            embed_was, embed_now = set_embed(embed)
            embed_problem = None
        except Exception as ex:  # the emoji are installed all the same
            embed_was = embed_now = None
            embed_problem = "%s: %s" % (type(ex).__name__, ex)
        else:
            if legacy_hook:
                try:
                    os.unlink(target("embed_on_save.py"))
                except (OSError, ValueError) as ex:
                    print("EmOji-san: could not remove the old save hook (%s)" % ex)
    except (OSError, ValueError, csv.Error) as ex:
        print("EmOji-san: installation stopped (%s)" % ex)
        return
    finally:
        if source_lock is not None:
            source_lock.unlock()
        lock.unlock()

    # --- report -----------------------------------------------------------
    if not here:
        kind = "first"
    elif prev is not None and rank != SETS.index(prev):
        kind = "up" if rank > SETS.index(prev) else "down"
    else:
        kind = "update" if added or changed or removed else "same"
    hello = GREETINGS["ja" if ui.lower().startswith("ja") else "en"][kind] % {
        "n": len(wanted), "set": size, "added": added, "removed": removed}
    count = {s: sum(SETS.index(r["set"]) <= i for r in rows)
             for i, s in enumerate(SETS)}

    print(hello)
    print("EmOji-san %s: %d emoji (+%d added, -%d removed%s) -> %s" % (
        size, len(wanted), added, removed,
        ", %d updated" % changed if changed else "", root))
    if kept:
        print("  kept %d SVGs from earlier installs for existing projects" % kept)
    if column:
        print("  index.csv (+ %s)" % column)
    else:
        print("  index.csv%s" % (" (no second name column: %s)" % problem
                                 if problem else ""))
    if newly:
        print("  registered as an SVG path (Settings > Options > System)")
    for p in migrated_paths:
        print("  taken off the SVG paths: %s (the EmOji-san folder of "
              "another QGIS version; its files are still there)" % p)
    if embed_problem:
        print("  embedding on save: could not be set up (%s)" % embed_problem)
    elif embed_now:
        print("  embedding SVGs into projects on save: on "
              "(EMBED=False; in front turns it off)")
    elif embed_was:
        print("  embedding SVGs into projects on save: off")
    if removed:
        print("  maps that used a removed emoji show \"?\" until a bigger "
              "set is installed again")
    if kind == "first":
        print("Next: Symbology of a point layer > SVG Marker > SVG browser "
              "> EmOji-san > a category. Reopen the dialog if it was open.")
        if rank + 1 < len(SETS):
            print("More emoji: SET='%s'; in front of the same line (%s)." % (
                SETS[rank + 1], ", ".join(
                    "%s %s" % (s, "{:,}".format(count[s])) for s in SETS)))
        if not embed_now:
            print("Sharing a project: embed the SVG in the symbol "
                  "(\"...\" > Embed File), or run this again with "
                  "EMBED=True; in front.")
    try:
        from qgis.utils import iface
        if iface:
            iface.messageBar().pushSuccess("EmOji-san", hello)
    except Exception:
        pass


try:
    _emoji_san_install(globals())
finally:
    del _emoji_san_install, _emoji_san_storage, _emoji_san_transaction
