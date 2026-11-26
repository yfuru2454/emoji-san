"""Regression checks for the notices in the standalone style asset."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree
from zipfile import ZIP_STORED, ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
import make_release  # noqa: E402


class ReleaseStyleTest(unittest.TestCase):
    def test_standalone_style_keeps_artwork_notices_and_symbols(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "release"
            make_release.build_release(output)
            self.assertEqual({path.name for path in output.iterdir()},
                             {"install.py", "uninstall.py", "check_install.py",
                              "diagnose.py", "emoji_san_data.zip", "emoji_san_core.xml"})
            source = (make_release.ROOT / make_release.STYLE).read_bytes()
            style = (output / "emoji_san_core.xml").read_bytes()
            self.assertTrue(style.startswith(source))
            self.assertEqual(ElementTree.tostring(ElementTree.fromstring(style)),
                             ElementTree.tostring(ElementTree.fromstring(source)))
            with ZipFile(output / "emoji_san_data.zip") as data:
                self.assertTrue(all(item.compress_type == ZIP_STORED
                                    for item in data.infolist()))
                for name in make_release.ARTWORK_NOTICES:
                    notice = (make_release.ROOT / name).read_bytes()
                    self.assertIn(b"<!-- " + name.encode("ascii") + b"\n" + notice + b"\n-->",
                                  style[len(source):])
                    self.assertEqual(data.read(name), notice)

    def test_rebuild_gives_the_same_bytes(self):
        # install.py pins the SHA-256 of the data ZIP, so a rebuild must not
        # depend on the compressor of the machine that runs it.
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a", Path(directory) / "b"
            make_release.build_release(first)
            make_release.build_release(second)
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes(),
                                 path.name)

    def test_invalid_comment_text_stops_packaging(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            style = root / make_release.STYLE
            style.parent.mkdir()
            style.write_bytes(b"<qgis_style/>")
            (root / "LICENSE-noto-emoji.txt").write_bytes(b"License")
            (root / "LICENSE-gemoji.txt").write_bytes(b"License")
            notice = root / "NOTICE"
            output = root / "release"
            with patch.object(make_release, "ROOT", root):
                for content, error in ((b"Notice -- attribution", "NOTICE.*XML comment"),
                                       (b"Notice\x00", "invalid standalone style XML")):
                    with self.subTest(content=content):
                        notice.write_bytes(content)
                        with self.assertRaisesRegex(ValueError, error):
                            make_release.build_release(output)
                        self.assertFalse(output.exists())
