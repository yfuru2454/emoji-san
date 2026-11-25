# EmOji-san

**Noto Emoji markers for QGIS** — and yes, there is an *Oji-san* (おじさん) hiding in the name.

Use color emoji (🏪 🚌 🏥 🌸 …) as point symbols in QGIS — no plugin,
one paste into the Python console, one download.

QGIS font markers can't render color emoji fonts
([qgis/QGIS#47970](https://github.com/qgis/QGIS/issues/47970)), but SVG
markers work perfectly. This repository ships a curated, renamed,
ready-to-use copy of [Google Noto
Emoji](https://github.com/googlefonts/noto-emoji) SVGs, and a tiny
installer that puts them into your QGIS profile, where the SVG browser
picks them up automatically.

## Install (one paste)

Open **Plugins → Python Console** and paste:

```python
exec(__import__('urllib.request', fromlist=['']).urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read().decode())
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

### Full set

Want faces and people too? Set `FULL = True` first (adds Smileys &
Emotion, People & Body, and the 8 generic flags — ~1,600 total):

```python
FULL = True
exec(__import__('urllib.request', fromlist=['']).urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read().decode())
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

### Uninstall

```python
exec(__import__('urllib.request', fromlist=['']).urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/uninstall.py').read().decode())
```

(or just delete the `svg/EmOji-san` folder in your [QGIS profile
folder](https://docs.qgis.org/latest/en/docs/user_manual/introduction/qgis_configuration.html)).

## Performance notes

Large SVG collections can make the QGIS SVG browser sluggish. This
distribution is designed around that:

- **Curated by default** — ~1,060 files instead of Noto's full 3,750.
- **Per-category folders** — the SVG browser renders previews for one
  folder at a time, so no folder ever holds more than ~360 files.
- **Readable file names** (`convenience_store.svg`, not
  `emoji_u1f3ea.svg`) — hover tooltips tell you what's what.
- Keep your QGIS profile on a **local disk**. Profiles on network
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

**インストール**: プラグイン → Pythonコンソール に上の `exec(...)`
ワンライナーを貼って Enter。シンボロジの SVGマーカー → SVGブラウザ に
**EmOji-san** グループが現れます。

- 標準では地図向け6ジャンル 約1,060個（動物・食べ物・場所/交通・
  活動・モノ・記号）。iPhone/Android の標準絵文字セット相当から選定し、
  肌色バリアントは除外しています。
- 顔・人物まで欲しい場合は `FULL = True` を先に書いてから同じ
  ワンライナーを実行（約1,600個）。
- **インストール不要のコア200個**: SVGを埋め込んだスタイルファイル
  `emoji_san_core.xml` を Releases から取得し、設定 → スタイルマネージャ →
  インポート。パス参照がないので、プロジェクトを人に渡しても壊れません。
- GUI派には QGIS Resource Sharing プラグインからも導入できます
  （このリポジトリのURLをリポジトリとして追加）。
- アンインストールは上記ワンライナー、またはプロファイルフォルダの
  `svg/EmOji-san` を削除するだけ。

**パフォーマンス**: SVGブラウザはフォルダ単位でプレビューを生成する
ため、カテゴリ別フォルダ分割で選択画面が重くなりません。プロファイル
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
