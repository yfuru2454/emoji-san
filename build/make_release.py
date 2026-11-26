#!/usr/bin/env python3
"""Build the release assets locally from a checkout of the release commit."""

import argparse
import csv
import hashlib
import pathlib
import re
import tempfile
import xml.etree.ElementTree as ET
import zipfile


ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_ZIP = "emoji_san_data.zip"
ARTWORK_NOTICES = ("LICENSE-noto-emoji.txt", "LICENSE-gemoji.txt", "NOTICE")
DATA_FILES = ("index.csv",) + ARTWORK_NOTICES + ("UPSTREAM_COMMIT.txt",)
SCRIPTS = ("uninstall.py", "tests/check_install.py", "tests/diagnose.py")
STYLE = "styles/emoji_san_core.xml"
SVG_PATH = re.compile(r"[A-Za-z][A-Za-z0-9 _-]*/[a-z0-9_]+\.svg")
DIGEST_MARKER = rb"^    DATA_SHA256 = None(?=\r?$)"


def data_paths():
    paths = list(DATA_FILES)
    seen = set()
    with (ROOT / "index.csv").open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            collection, path = row.get("collection"), row.get("path") or ""
            if (collection not in ("map", "people") or not SVG_PATH.fullmatch(path)
                    or path.casefold() in seen):
                raise ValueError("invalid or duplicate release SVG path: %r" % path)
            seen.add(path.casefold())
            paths.append("collections/noto_emoji_%s/svg/%s" % (collection, path))
    if not seen:
        raise ValueError("index.csv does not list any SVGs")
    return sorted(paths)


def standalone_style():
    """Keep the published style and its artwork notices together."""
    style = (ROOT / STYLE).read_bytes()
    for name in ARTWORK_NOTICES:
        notice = (ROOT / name).read_bytes()
        if b"--" in notice:
            raise ValueError("%s contains '--', which cannot appear in an XML comment" % name)
        style += b"\n<!-- " + name.encode("ascii") + b"\n" + notice + b"\n-->\n"
    try:
        ET.fromstring(style)
    except ET.ParseError as error:
        raise ValueError("invalid standalone style XML: %s" % error) from error
    return style


def build_release(output):
    output = pathlib.Path(output)
    if output.exists():
        raise FileExistsError("release output already exists: %s" % output)
    style = standalone_style()
    output.parent.mkdir(parents=True, exist_ok=True)
    installer = (ROOT / "install.py").read_bytes()
    if len(re.findall(DIGEST_MARKER, installer, re.M)) != 1:
        raise ValueError("install.py must have one DATA_SHA256 = None line")

    license_notice = b"\n\n" + b"\n".join(
        b"# " + line if line else b"#"
        for line in (ROOT / "LICENSE").read_bytes().splitlines()) + b"\n"

    # Publish the complete asset directory only after every file is ready.
    with tempfile.TemporaryDirectory(dir=output.parent) as temporary:
        staging = pathlib.Path(temporary) / "release"
        staging.mkdir()
        data_zip = staging / DATA_ZIP
        with zipfile.ZipFile(data_zip, "w") as archive:
            for name in data_paths():
                member = zipfile.ZipInfo(name)  # fixed timestamp and portable mode
                member.create_system = 3
                member.external_attr = 0o100644 << 16
                # Stored, not deflated: deflate output differs between zlib
                # builds, and the installer pins the SHA-256 of these bytes.
                archive.writestr(member, (ROOT / name).read_bytes(), zipfile.ZIP_STORED)
        digest = hashlib.sha256(data_zip.read_bytes()).hexdigest()
        installer = re.sub(DIGEST_MARKER, b'    DATA_SHA256 = "%s"' % digest.encode("ascii"),
                           installer, flags=re.M)
        (staging / "install.py").write_bytes(installer + license_notice)
        for name in SCRIPTS:
            source = ROOT / name
            (staging / source.name).write_bytes(source.read_bytes() + license_notice)
        (staging / pathlib.Path(STYLE).name).write_bytes(style)
        staging.rename(output)
    return digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=pathlib.Path, help="new directory for the release assets")
    args = parser.parse_args()
    try:
        digest = build_release(args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, "%s\n" % error)
    print("Release assets: %s" % args.output)
    print("SHA-256 %s: %s" % (DATA_ZIP, digest))


if __name__ == "__main__":
    main()
