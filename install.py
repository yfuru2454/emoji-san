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
#   EMBED=True;   embed the SVGs into every project you save; False stops it
#   LOCALE='de';  language of the second name column in index.csv
#   ZIP='...';    read the files from a ZIP on disk instead of downloading
#
# Without SET, the first run installs S and later runs keep the set that is
# installed. A bigger set adds files. A smaller set deletes the files it
# does not contain. Files that did not come from EmOji-san are left alone.
#
# EMBED=True adds a few marked lines to startup.py in the QGIS settings
# folder. QGIS runs that file at every start; the lines load
# embed_on_save.py from the EmOji-san folder.
#
# Everything is inside one function that is called on the last lines. That
# keeps the console's namespace clean, and a script that arrived only in
# part does nothing.


def _emoji_san_install(ns):
    import csv
    import io
    import json
    import os
    import urllib.error
    import urllib.request
    import zipfile

    from qgis.core import QgsApplication, QgsSettings

    REPO = "yfuru2454/emoji-san"
    TAG = "v1.0.0"  # the release this script installs
    CLDR = ("https://raw.githubusercontent.com/unicode-org/cldr-json/49.0.0/"
            "cldr-json/")
    SETS = ("S", "M", "L")
    FOLDER = "EmOji-san"
    SVG_PATHS = "svg/searchPathsForSVG"
    # copied next to the SVGs: license, notice, upstream commit, save hook
    EXTRAS = ("LICENSE-noto-emoji.txt", "NOTICE", "UPSTREAM_COMMIT.txt",
              "embed_on_save.py")
    LITTER = {".DS_Store", "Thumbs.db", "desktop.ini"}  # of file managers
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
            "first": "%(n)d emoji installed! Have fun with your maps 😃✨ "
                     "Love, EmOji-san 👨‍💼",
            "up": "Upgraded to size %(set)s! %(added)d more emoji for you "
                  "😆👍 Love, EmOji-san 👨‍💼",
            "down": "Back to size %(set)s... %(removed)d emoji said goodbye "
                    "😢 Love, EmOji-san 👨‍💼",
            "update": "Updated to the latest! Fresh emoji for you 😆👍 "
                      "Love, EmOji-san 👨‍💼",
            "same": "All up to date! Keep up the good work 💪 "
                    "Love, EmOji-san 👨‍💼",
        },
    }

    # --- options: taken out of the console's namespace --------------------
    size = ns.pop("SET", None)
    embed = ns.pop("EMBED", None)
    language = ns.pop("LOCALE", None)
    source = ns.pop("ZIP", None) or (
        "https://github.com/%s/archive/refs/tags/%s.zip" % (REPO, TAG))
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
    profile = os.path.normpath(QgsApplication.qgisSettingsDirPath())
    root = os.path.join(os.path.dirname(os.path.dirname(profile)), FOLDER)

    # The language QGIS runs in, e.g. "ja" or "pt_BR". QGIS stores it in
    # locale/userLocale at every start, also when it just follows the system.
    ui = str(QgsSettings().value("locale/userLocale", "")
             or QgsApplication.locale() or "en")

    def same(a, b):
        return (os.path.normcase(os.path.normpath(a))
                == os.path.normcase(os.path.normpath(b)))

    def target(rel, base=root):
        """File path for a "path" of index.csv ("Category/name.svg") under
        base, or None if it would land anywhere else."""
        p = os.path.normpath(os.path.join(base, *rel.split("/")))
        return p if p.startswith(os.path.normpath(base) + os.sep) else None

    # --- the files --------------------------------------------------------
    print("EmOji-san: getting %s" % source)
    try:
        if "://" in source:
            with urllib.request.urlopen(source, timeout=120) as reply:
                blob = reply.read()
        else:  # ZIP='...' with a file on disk
            with open(source, "rb") as f:
                blob = f.read()
        z = zipfile.ZipFile(io.BytesIO(blob))
        members = set(z.namelist())
        # GitHub packs the repository into one top folder (emoji-san-1.0.0/)
        found = sorted(n for n in members if n == "index.csv"
                       or (n.count("/") == 1 and n.endswith("/index.csv")))
        if not found:
            raise ValueError("no index.csv in the ZIP")
        top = found[0][:-len("index.csv")]
        rows = list(csv.DictReader(io.StringIO(
            z.read(top + "index.csv").decode("utf-8"))))
        member = {r["path"]: "%scollections/noto_emoji_%s/svg/%s"
                  % (top, r["collection"], r["path"]) for r in rows}
        if not rows or any(
                r["set"] not in SETS or not r["path"].endswith(".svg")
                or not target(r["path"]) or member[r["path"]] not in members
                for r in rows):
            raise ValueError("index.csv does not match the ZIP")
    except Exception as ex:  # nothing has been written yet
        print("EmOji-san: could not get the files (%s: %s). Nothing changed."
              % (type(ex).__name__, ex))
        return

    # --- what is installed now --------------------------------------------
    def sets_in(base):
        return [r["set"] for r in rows
                if os.path.isfile(target(r["path"], base) or "")]

    registered = QgsSettings().value(SVG_PATHS, [])
    if isinstance(registered, str):
        registered = [registered]
    registered = [p for p in (registered or []) if p]
    # An EmOji-san folder that belongs to another settings folder. QGIS 4
    # copies the SVG path list when it takes over a QGIS 3 profile, so it
    # starts out pointing at the folder under QGIS3. This one replaces it.
    elsewhere = [p for p in registered
                 if not same(p, root)
                 and os.path.basename(os.path.normpath(p)) == FOLDER
                 and (not os.path.isdir(p)
                      or os.path.isfile(os.path.join(p, "index.csv")))]

    here = sets_in(root)
    seen = here or [s for p in elsewhere for s in sets_in(p)]
    prev = max(seen, key=SETS.index) if seen else None
    size = size or prev or SETS[0]
    rank = SETS.index(size)
    wanted = [r for r in rows if SETS.index(r["set"]) <= rank]

    # --- write, then delete -----------------------------------------------
    def put(dest, data):
        """Write a file unless it is there already with the same content.
        Returns "new", "changed" or "" (left as it was)."""
        try:
            with open(dest, "rb") as f:
                if f.read() == data:
                    return ""
            state = "changed"
        except OSError:
            state = "new"
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(data)
        return state

    added = changed = removed = 0
    for r in wanted:
        state = put(target(r["path"]), z.read(member[r["path"]]))
        added += state == "new"
        changed += state == "changed"
    for name in EXTRAS:
        if top + name in members:
            put(os.path.join(root, name), z.read(top + name))

    # Delete what a smaller set no longer contains. Only files EmOji-san
    # installed: the ones in this release's index and in the index of the
    # release that was installed before.
    ours = {r["path"] for r in rows}
    try:
        with open(os.path.join(root, "index.csv"), encoding="utf-8",
                  newline="") as f:
            ours.update(r.get("path") or "" for r in csv.DictReader(f))
    except (OSError, ValueError, csv.Error):
        pass
    for rel in sorted(ours - {r["path"] for r in wanted}):
        dest = target(rel) if rel.endswith(".svg") else None
        if dest and os.path.isfile(dest):
            os.remove(dest)
            removed += 1
    for name in os.listdir(root):  # category folders left empty
        folder = os.path.join(root, name)
        if os.path.isdir(folder) and not set(os.listdir(folder)) - LITTER:
            for litter in os.listdir(folder):
                os.remove(os.path.join(folder, litter))
            os.rmdir(folder)

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
                    except urllib.error.HTTPError:
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
                              % chain[0])

    code, names, problem = local_names()
    column = "name_" + code if names else None
    fields = ["emoji", "codepoint", "name"] + ([column] if column else [])
    fields += ["category", "path", "set", "noto_file"]
    for r in wanted:
        if column:  # CLDR lists most emoji without the U+FE0F selector
            e = r["emoji"]
            r[column] = names.get(e) or names.get(e.replace(chr(0xFE0F), ""),
                                                  "")
    with open(os.path.join(root, "index.csv"), "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(wanted)
    with open(os.path.join(root, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            "EmOji-san: Google Noto Emoji (Apache-2.0) as SVG markers for "
            "QGIS.\n"
            "Set %s, %d emoji. This folder is one of the QGIS SVG paths.\n"
            "\n"
            "index.csv lists the emoji. \"path\" is relative to this folder, "
            "which is\nalso how QGIS writes it into a project, for example "
            "\"Food and Drink/hot_beverage.svg\".\n" % (size, len(wanted)))
        if column:
            f.write("\"%s\" is the name in the language of this QGIS "
                    "(Unicode CLDR).\n" % column)
        f.write("\nhttps://github.com/%s\n" % REPO)

    # --- SVG path ---------------------------------------------------------
    paths = [p for p in registered if p not in elsewhere]
    newly = not any(same(p, root) for p in paths)
    if newly:
        paths.append(root.replace(os.sep, "/"))  # as QGIS writes it itself
    if paths != registered:
        if hasattr(QgsApplication, "setSvgPaths"):  # QGIS 3.18 and later
            QgsApplication.setSvgPaths(paths)
        else:
            QgsSettings().setValue(SVG_PATHS, paths)

    # --- embedding on save ------------------------------------------------
    def set_embed(on):
        """Add or remove our lines in startup.py and switch the hook in
        this session. None leaves it as it is. Returns (was, now)."""
        from qgis.PyQt.QtCore import QStandardPaths
        try:  # Qt 5
            where = QStandardPaths.AppDataLocation
        except AttributeError:  # Qt 6
            where = QStandardPaths.StandardLocation.AppDataLocation
        # QGIS looks for startup.py here, wherever the profiles are
        startup = os.path.normpath(os.path.join(
            QStandardPaths.writableLocation(where), "startup.py"))
        hook = os.path.join(root, "embed_on_save.py")
        block = ("%s\ntry:\n    exec(open(%r, 'rb').read(), "
                 "{'__name__': 'emoji_san_embed'})\nexcept Exception:\n"
                 "    pass\n%s\n" % (BEGIN, hook, END))
        text = ""
        if os.path.isfile(startup):
            with open(startup, encoding="utf-8") as f:
                text = f.read()
        head, begin, rest = text.partition(BEGIN)
        body, end, tail = rest.partition(END)
        was = bool(begin and end)
        on = was if on is None else bool(on)
        if on != was or (on and begin + body + end + "\n" != block):
            # the file without our lines, then our lines at the end
            new = (head.rstrip("\n") + tail if was else text).strip("\n")
            if new:
                new += "\n"
            if on:
                new += ("\n" if new else "") + block
            if new:
                os.makedirs(os.path.dirname(startup), exist_ok=True)
                with open(startup + ".tmp", "w", encoding="utf-8") as f:
                    f.write(new)
                os.replace(startup + ".tmp", startup)
            else:  # nothing but our lines was in it: the file can go,
                os.remove(startup)  # and what Python cached of it
                cache = os.path.join(os.path.dirname(startup), "__pycache__")
                if os.path.isdir(cache):
                    for name in os.listdir(cache):
                        if name.startswith("startup.") \
                                and name.endswith(".pyc"):
                            os.remove(os.path.join(cache, name))
                    if not os.listdir(cache):
                        os.rmdir(cache)
        if os.path.isfile(hook):  # now, without restarting QGIS
            with open(hook, "rb") as f:
                exec(compile(f.read(), hook, "exec"),
                     {"__name__": "emoji_san_embed", "EMOJI_SAN_EMBED": on})
        return was, on

    try:
        if embed is None and not here:
            # Like the set, this carries over from the folder of the other
            # QGIS version: on there means on here.
            for p in elsewhere:
                other = os.path.join(os.path.dirname(os.path.normpath(p)),
                                     "startup.py")
                if os.path.isfile(other):
                    with open(other, encoding="utf-8") as f:
                        embed = embed or BEGIN in f.read()
        embed_was, embed_now = set_embed(embed)
        embed_problem = None
    except Exception as ex:  # the emoji are installed all the same
        embed_was = embed_now = None
        embed_problem = "%s: %s" % (type(ex).__name__, ex)

    # --- report -----------------------------------------------------------
    if not here:
        kind = "first"
    elif rank != SETS.index(prev):
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
    if column:
        print("  index.csv (+ %s)" % column)
    else:
        print("  index.csv%s" % (" (no second name column: %s)" % problem
                                 if problem else ""))
    if newly:
        print("  registered as an SVG path (Settings > Options > System)")
    for p in elsewhere:
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
    del _emoji_san_install
