# EmOji-san

**Noto Emoji markers for QGIS** — and yes, there is an *Oji-san* (おじさん) hiding in the name.

Use color emoji (🏪 🚌 🏥 🌸 …) as point symbols in QGIS — no plugin,
one paste into the Python console, one download.

QGIS font markers can't render color emoji fonts
([qgis/QGIS#47970](https://github.com/qgis/QGIS/issues/47970)), but SVG
markers work perfectly. This repository ships a curated, renamed,
ready-to-use copy of [Google Noto
Emoji](https://github.com/googlefonts/noto-emoji) SVGs, and a tiny
installer that puts them next to your QGIS profiles and registers them
as an SVG path, so the SVG browser shows an **EmOji-san** group with one
sub-group per category.

## Install (one paste)

Open **Plugins → Python Console** and paste:

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
```

Then open any point layer's symbology → **SVG Marker → SVG Browser**
and find the **EmOji-san** group. That's it.

- One HTTP request: the installer downloads this repository's tagged
  archive (~8 MB) and extracts the SVGs. A few seconds on a normal
  connection, proxy-friendly.
- Installs the **map set**: ~1,060 emoji in 6 categories — Animals &
  Nature, Food & Drink, Travel & Places, Activities, Objects, Symbols.
  The standard Unicode emoji you know from iPhone/Android keyboards,
  in Google's Noto design.
- Skin-tone variants are excluded (they triple the file count and have
  no cartographic value).
- Re-running simply overwrites — always safe.

### For scripts and AI agents: `index.csv`

The installed folder also holds `index.csv`, one row per emoji:

| emoji | codepoint | name | name_ja | category | path | noto_file |
|---|---|---|---|---|---|---|
| ♨️ | U+2668 U+FE0F | hot springs | 温泉マーク | Travel & Places | Travel and Places/hot_springs.svg | emoji_u2668.svg |

`path` is relative to the SVG path, the same form QGIS saves in projects.
The `name_<lang>` column is added at install time in your QGIS's
language, from Unicode CLDR (~100 languages; none for English). Scripts
and AI assistants for QGIS can look emoji up here instead of guessing
file names. Force a language with `LOCALE = 'de'; import urllib.request as u; exec(...)`.

### Full set

Want faces and people too? Put `FULL = True;` in front of the same
line (adds Smileys & Emotion, People & Body, and the 8 generic flags —
~1,600 total). The QGIS console runs one line at a time, so keep it on
one line:

```python
FULL = True; import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
```

### Prefer a GUI? (QGIS Resource Sharing)

This repository doubles as a [QGIS Resource
Sharing](https://plugins.qgis.org/plugins/qgis_resource_sharing/)
repository: install that plugin, add this repository's URL under
Settings, and install the "EmOji-san" collections with clicks instead
of code.

### Core set: 200 embedded symbols (no install at all)

A hand-picked **core set (200 symbols)** is also shipped as a style
file with the SVGs **embedded** — no files, no paths, nothing to break
when you share a project. Download `emoji_san_core.xml` from the
[Releases](../../releases) page (or `styles/` in this repository) and
import it via **Settings → Style Manager → Import/Export → Import**.
Symbols are tagged (`EmOji-san`, `Noto Emoji` + category) and
searchable. Selection rationale: simple shapes that stay legible at
point-marker size (faces, hands, single objects, signs), matching
Mapbox Maki icons / major OSM POI tags; see `build/make_core.py`.

### Check your install

Paste this into the QGIS Python console after installing. It checks the
folder, the SVG path registration, `index.csv`, that QGIS really renders
the SVGs (and, if imported, all core style symbols), then adds a small
"EmOji-san demo" layer around the map centre (`DEMO = False;` in front
to skip it):

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

### Uninstall

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/uninstall.py').read())
```

(or delete the `EmOji-san` folder next to the `profiles` folder in your
[QGIS settings
folder](https://docs.qgis.org/latest/en/docs/user_manual/introduction/qgis_configuration.html)
and remove it under Settings → Options → System → SVG paths).

## Performance notes

Large SVG collections can make the QGIS SVG browser sluggish. This
distribution is designed around that:

- **Curated by default** — ~1,060 files instead of Noto's full 3,750.
- **Per-category groups** — the folder is registered as its own SVG
  path, so each category shows up as a sub-group and the browser loads
  one category (at most ~360 files) at a time. (Folders nested inside
  the profile's `svg` folder are NOT split this way: QGIS lists
  everything under them as one group.)
- **Readable file names** (`convenience_store.svg`, not
  `emoji_u1f3ea.svg`) — hover tooltips tell you what's what.
- Keep your QGIS settings folder on a **local disk**. Profiles on network
  drives or heavily-synced folders (OneDrive etc.) are a known cause of
  a slow SVG browser
  ([qgis/QGIS#59056](https://github.com/qgis/QGIS/issues/59056)).
- Rendering many emoji points? Consider the layer rendering option
  **"Render as raster"**, and avoid per-feature data-defined
  size/rotation where you can — QGIS's SVG cache only hits on identical
  parameters.

## Security & reproducibility

- The one-liner executes code from this repository — **read
  [install.py](install.py) first**; it's ~100 short lines.
- Pin the URL to a **tag or commit**, never a branch, so what you run
  can't silently change.
- The SVGs come from this repository's tagged archive, not from a
  third-party CDN at run time. The upstream noto-emoji commit they were
  taken from is recorded in [UPSTREAM_COMMIT.txt](UPSTREAM_COMMIT.txt).
- Behind a corporate proxy, the standard `HTTPS_PROXY` environment
  variables are honored by QGIS's bundled Python.

## Maintenance (for the repository owner)

Emoji needs don't change daily — new emoji land roughly once a year
with Unicode releases. Yearly (or whenever you feel like it):

```bash
python3 build/update_from_upstream.py   # re-fetch, rename, reorganize
git add -A && git commit -m "Update to noto-emoji <commit>"
git tag v2027.1 && git push --tags
```

then update the tag in `install.py` and this README. Nothing else to
upload: the installer downloads the tagged repository archive that
GitHub serves automatically. Old tags keep working forever, so maps
built against an old tag stay reproducible — and this repository keeps
working even if upstream reorganizes its folders again (it moved
`svg/` to `2D/svg/` in 2025; this repo absorbed that so your one-liner
never notices).

## What about country flags?

Not included: Noto keeps country flags in a separate
`third_party/region-flags` tree with per-country public-domain caveats,
so they're deliberately out of scope here. See the
[noto-emoji README](https://github.com/googlefonts/noto-emoji) if you
need them.

## How the set is chosen

`build/update_from_upstream.py` intersects:

1. [gemoji](https://github.com/github/gemoji)'s `emoji.json` — the
   standard RGI emoji set with categories and English names (what
   iPhone/Android keyboards show), and
2. the SVGs actually present in `googlefonts/noto-emoji` at the
   recorded commit,

drops skin-tone variants, renames files to readable slugs, and sorts
them into category folders.

## License

- Emoji artwork: [Apache License
  2.0](https://github.com/googlefonts/noto-emoji/blob/main/LICENSE)
  (© Google), redistributed here with modifications (subset selection,
  renaming, reorganization) as described in [NOTICE](NOTICE). A copy of
  the license is installed next to the SVGs.
- Installer and build scripts: MIT.

## FAQ: why not a QGIS plugin?

Installing a folder of SVGs is a one-time file copy. A plugin would add
an install/update/review lifecycle around something that has no runtime
behavior — more maintenance for zero added capability. The two channels
this repository already offers cover both audiences: the one-liner for
console users, and QGIS Resource Sharing (the official way to
distribute symbol collections) for GUI users.

---

# 日本語

QGISでカラー絵文字をポイントシンボルとして使うための配布リポジトリです。
プラグイン不要、Pythonコンソールに1行貼るだけ。ダウンロードは1回
（タグ付きアーカイブ約8MB）で済みます。

**インストール**: プラグイン → Pythonコンソール に上の
`import urllib.request as u; exec(...)` のワンライナーを貼って Enter。シンボロジの SVGマーカー → SVGブラウザ に
**EmOji-san** グループが現れ、その下にカテゴリ別のグループが並びます
（インストール先は QGIS3 設定フォルダ直下の `EmOji-san` で、SVGパスに
自動登録されます）。

- 標準では地図向け6ジャンル 約1,060個（動物・食べ物・場所/交通・
  活動・モノ・記号）。iPhone/Android の標準絵文字セット相当から選定し、
  肌色バリアントは除外しています。
- 顔・人物まで欲しい場合は、同じワンライナーの先頭に `FULL = True; ` を
  付けて1行のまま実行（約1,600個）。QGISのコンソールは複数行を一度に
  貼ると受け付けないため、1行にしてください。
- **インストール不要のコア200個**: SVGを埋め込んだスタイルファイル
  `emoji_san_core.xml` を Releases から取得し、設定 → スタイルマネージャ →
  インポート。パス参照がないので、プロジェクトを人に渡しても壊れません。
- **スクリプトやAI向けの対応表** `index.csv` も一緒に入ります。絵文字・
  コードポイント・英語名・**QGISの表示言語での名前**（Unicode CLDR、
  約100言語）・カテゴリ・パスが1行ずつ並び、AIアシスタントがファイル名を
  推測せずに絵文字を選べます。言語を指定するなら `LOCALE = 'de'; import urllib.request as u; exec(...)`。
- GUI派には QGIS Resource Sharing プラグインからも導入できます
  （このリポジトリのURLをリポジトリとして追加）。
- アンインストールは上記ワンライナー。手動なら QGIS3 設定フォルダの
  `EmOji-san` を削除し、オプション → システム → SVGパスから外します。

**インストールの確認**: インストール後に、Pythonコンソールで次の1行を
実行すると、フォルダ・SVGパスの登録・index.csv・QGISで実際に描画できるか
（コアのスタイルを入れていれば200個すべて）を確かめ、地図の中心に8個の
絵文字を置いたデモ層を追加します（不要なら先頭に `DEMO = False; `）。

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

**パフォーマンス**: 独立したSVGパスとして登録するので、カテゴリごとの
グループに分かれ、選んだカテゴリだけが読み込まれます（プロファイルの
`svg` フォルダの中に置くと、下のフォルダもまとめて1グループで表示され
るため分割されません）。設定フォルダ
はローカルディスクに置き、ネットワークドライブや同期フォルダは避けて
ください。大量ポイント描画時はレイヤの「ラスタとして描画」も有効です。

**メンテナンス（リポジトリ管理者向け）**: 絵文字の追加はUnicodeの
年1サイクルなので、年1回 `build/update_from_upstream.py` を実行して
コミット・タグを打つだけ。本家がフォルダ構成を変えても（2025年に
`svg/` → `2D/svg/` へ移動）、この配布リポジトリが吸収するので
利用者のワンライナーは壊れません。

**ライセンス**: 絵文字はGoogleのApache-2.0。選抜・改名・フォルダ再編
という改変を加えて再配布しています（NOTICE参照）。スクリプトはMIT。

**実行前に install.py の中身を読めます**（100行弱です）。URLは
ブランチではなくタグ/コミットに固定してください。
