"""Offline regression checks for the annual build and its publication."""

import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "build"))
import make_core  # noqa: E402
import update_from_upstream  # noqa: E402


OLD_SHA = "a" * 40
SAVED_SHA = "b" * 40
NEXT_SHA = "c" * 40
SVG = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
NEW_SVG = b'<svg xmlns="http://www.w3.org/2000/svg"><circle r="1"/></svg>'
SUN = "Animals and Nature/sun.svg"
RETIRED = "Food and Drink/retired.svg"
FLAGS = update_from_upstream.NOTO_FLAG_DIR


def entry(codepoints, name, status="fully-qualified"):
    glyph = "".join(chr(int(point, 16)) for point in codepoints.split())
    return f"{codepoints} ; {status} # {glyph} E18.0 {name}"


def row(glyph, name, category, path, noto_file):
    return {
        "emoji": glyph,
        "codepoint": " ".join(f"U+{ord(c):04X}" for c in glyph),
        "name": name,
        "category": category,
        "collection": "map",
        "path": path,
        "noto_file": noto_file,
        "set": "S",
    }


class AnnualBuildTest(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.sun = row("☀", "bright sun", "Animals & Nature", SUN,
                       "emoji_u2600.svg")
        self.retired = row("🍄", "retired", "Food & Drink", RETIRED,
                           "emoji_u1f344.svg")
        for old in (self.sun, self.retired):
            self.write(make_core.svg_path(old), SVG)
        self.extra = make_core.svg_path(self.sun).with_name("Sun_2.svg")
        self.write(self.extra, b"an unrelated file")
        self.write("core_list.txt", f"{SUN[:-4]}\n{RETIRED[:-4]}\n".encode())
        self.write("LICENSE-noto-emoji.txt", b"Artwork License\nFull license")
        provenance = f"{OLD_SHA}\nRetained SVG {SAVED_SHA}: {RETIRED}\n"
        self.write("UPSTREAM_COMMIT.txt", provenance.encode())
        self.write("styles/emoji_san_core.xml", b"previous style")
        self.write("styles/unrelated.xml", b"unrelated style")
        make_core.write_index(self.root, [self.sun, self.retired])
        self.unicode_data = "\n".join((
            "# Version: 18.0",
            "# group: Animals & Nature",
            entry("1F31E", "sun"),
            "# group: Objects",
            entry("2600 FE0F", "sunny"),
            entry("2600", "sunny", "unqualified"),
            "# group: Travel & Places",
            entry("1F6D9", "lighthouse"),
            entry("1F6F6", "canoe"),
            "# group: Smileys & Emotion",
            entry("1F600", "grinning face"),
            "# group: People & Body",
            entry("1F44B 1F3FB", "waving hand: light skin tone"),
            "# group: Flags",
            "# subgroup: flag",
            entry("1F3F3 FE0F 200D 26A7 FE0F", "transgender flag"),
            "# subgroup: country-flag",
            entry("1F1EF 1F1F5", "flag: Japan"),
            entry("1F1E6 1F1FD", "flag: Åland Islands"),
            "# subgroup: subdivision-flag",
            entry("1F3F4 E0067 E0062 E0065 E006E E0067 E007F",
                  "flag: England"),
        )).encode("utf-8")
        self.noto = {
            "emoji_u2600_fe0f.svg", "emoji_u1f31e.svg", "emoji_u1f6d9.svg",
            "emoji_u1f3f3_200d_26a7_fe0f.svg", "emoji_u1f44b_1f3fb.svg",
            "emoji_u1f600.svg",
            f"{FLAGS}/emoji_u1f1ef_1f1f5.svg",
            f"{FLAGS}/emoji_u1f1e6_1f1fd.svg",
            f"{FLAGS}/emoji_u1f3f4_e0067_e0062_e0065_e006e_e0067_e007f.svg",
        }
        # England's flag is a git symlink to Japan's here, as Bouvet Island's
        # is to Norway's upstream: a raw download gives the link's target.
        self.links = {
            f"{FLAGS}/emoji_u1f3f4_e0067_e0062_e0065_e006e_e0067_e007f.svg":
                b"emoji_u1f1ef_1f1f5.svg",
        }
        self.write("l_only_list.txt",
                   b"# kept out of M\nTravel and Places/lighthouse\n")

    def write(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def snapshot(self):
        return {p.relative_to(self.root): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def run_build(self):
        def fetch(url):
            if url == update_from_upstream.unicode_url("18.0.0"):
                return self.unicode_data
            name = url.rsplit("/", 1)[-1]
            if name == "LICENSE":
                return b"Artwork License\n"
            path = url.split(NEXT_SHA + "/", 1)[1]
            if path.startswith(update_from_upstream.NOTO_SVG_DIR + "/"):
                path = name
            if path in self.links:
                return self.links[path]
            self.assertIn(path, self.noto)
            return NEW_SVG

        output = io.StringIO()
        source = patch.object(update_from_upstream, "upstream_files",
                              return_value=(NEXT_SHA, self.noto))
        downloads = patch.object(update_from_upstream, "fetch",
                                 side_effect=fetch)
        with patch.object(update_from_upstream, "ROOT", self.root), source, \
                downloads, contextlib.redirect_stdout(output):
            update_from_upstream.main("chosen-noto-ref")
        return output.getvalue()

    def test_annual_update_preserves_published_paths_and_assets(self):
        output = self.run_build()
        records = make_core.read_index(self.root)
        by_path = {record["path"]: record for record in records}
        self.assertEqual(list(by_path), [
            SUN, RETIRED, "Animals and Nature/sun_3.svg",
            "Travel and Places/lighthouse.svg",
            "Smileys and Emotion/grinning_face.svg",
            "Flags/transgender_flag.svg", "Flags/flag_japan.svg",
            "Flags/flag_aland_islands.svg", "Flags/flag_england.svg",
        ])
        self.assertEqual({path: record["set"] for path, record in by_path.items()}, {
            SUN: "S", RETIRED: "S", "Animals and Nature/sun_3.svg": "M",
            "Travel and Places/lighthouse.svg": "L",  # l_only_list.txt
            "Smileys and Emotion/grinning_face.svg": "M",  # faces are in M
            "Flags/transgender_flag.svg": "L", "Flags/flag_japan.svg": "L",
            "Flags/flag_aland_islands.svg": "L", "Flags/flag_england.svg": "L",
        })
        self.assertEqual(by_path["Flags/flag_england.svg"]["noto_file"],
                         f"{FLAGS}/emoji_u1f3f4_e0067_e0062_e0065_e006e_e0067_e007f.svg")
        self.assertEqual((self.root / make_core.svg_path(
            by_path["Flags/flag_england.svg"])).read_bytes(), NEW_SVG)
        self.assertEqual(by_path[SUN], {
            **self.sun, "name": "sunny", "noto_file": "emoji_u2600_fe0f.svg",
        })
        self.assertEqual(by_path[RETIRED], self.retired)
        self.assertEqual(
            (self.root / make_core.svg_path(self.sun)).read_bytes(), NEW_SVG)
        self.assertEqual(
            (self.root / make_core.svg_path(self.retired)).read_bytes(),
            SVG)
        self.assertEqual((self.root / self.extra).read_bytes(),
                         b"an unrelated file")
        self.assertEqual((self.root / "styles/unrelated.xml").read_bytes(),
                         b"unrelated style")
        style = ElementTree.parse(self.root / "styles/emoji_san_core.xml")
        self.assertEqual(
            [s.attrib["name"] for s in style.findall(".//symbol")],
            ["☀ sun", "🍄 retired"])
        provenance = (self.root / "UPSTREAM_COMMIT.txt").read_text("utf-8")
        self.assertTrue(provenance.startswith(NEXT_SHA + "\n"))
        self.assertIn(f"Retained SVG {SAVED_SHA}: {RETIRED}", provenance)
        self.assertIn("retained from previous builds: 1", output)
        self.assertIn("Unicode entries without a Noto SVG: 1", output)
        self.assertIn("U+1F6F6 canoe", output)

    def test_validation_failure_keeps_previous_outputs(self):
        self.write("core_list.txt", b"Missing/unknown\n")
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, "core_list.txt"):
            self.run_build()
        self.assertEqual(self.snapshot(), before)

    def test_publish_failure_restores_replaced_and_new_files(self):
        before = self.snapshot()
        replace = os.replace

        def fail_style(source, target):
            if target == self.root / "styles/emoji_san_core.xml":
                raise OSError("simulated style replacement failure")
            return replace(source, target)

        with patch.object(make_core.os, "replace", side_effect=fail_style):
            with self.assertRaisesRegex(OSError, "simulated style"):
                self.run_build()
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.root / "collections/noto_emoji_people").exists())

    def test_release_version_is_checked(self):
        with self.assertRaisesRegex(ValueError, "Expected Unicode Emoji"):
            update_from_upstream.unicode_emoji(self.unicode_data, "17.0.0")
        self.assertEqual(
            update_from_upstream.unicode_url("16.0.0"),
            "https://www.unicode.org/Public/emoji/16.0/emoji-test.txt",
        )


if __name__ == "__main__":
    unittest.main()
