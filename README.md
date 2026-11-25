# EmOji-san

Color emoji (🏪 🚌 🏥 ♨️) as point symbols in QGIS.
Google Noto Emoji, installed with one line in the Python console.

[日本語は下にあります](#日本語)

## Install

1. In QGIS, open **Plugins → Python Console**.
2. Paste this line and press Enter:

   ```python
   import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
   ```

3. You should see:

   ```
   EmOji-san: 1060 files installed -> .../QGIS3/EmOji-san
     index.csv: 1058 emoji (+ name_ja)
     registered as an SVG path (Settings > Options > System)
   ```

4. Open a point layer's **Symbology**, set the symbol layer type to
   **SVG Marker**, and pick a category under **EmOji-san** in the
   SVG browser.

## Options

Put the option in front of the same line, separated by `;`.
The console only accepts one line at a time.

- All emoji including faces and people (1,595):
  `FULL = True; import urllib.request as u; exec(...)`
- Names in another language in `index.csv`:
  `LOCALE = 'de'; import urllib.request as u; exec(...)`

## 200 core symbols (no install needed)

- Download `emoji_san_core.xml` from [Releases](../../releases).
- **Settings → Style Manager → Import/Export → Import Items**,
  choose the file, **Select All**, **Import**.
- The SVGs are embedded, so projects using them work on other
  computers too.

## Check the install

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

- Expected: `Result: ALL GOOD (9 passed, 0 failed, 0 skipped)`
- It also adds an "EmOji-san demo" layer with 8 emoji. Put
  `DEMO = False; ` in front to skip it.

## Uninstall

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/uninstall.py').read())
```

## If the SVG browser is slow or freezes

- In **Settings → Options → System → SVG paths**, remove folders you no
  longer need, especially an older full Noto Emoji folder (3,000+ SVGs)
  or folders on a network drive or a shared folder.
- In the SVG browser, click a category, not the top **EmOji-san** group.
- To find the cause, run the diagnostics. It prints `LIKELY CAUSES`:

  ```python
  import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/diagnose.py').read())
  ```

## What you get

- 1,058 emoji in 6 categories: Activities, Animals and Nature,
  Food and Drink, Objects, Symbols, Travel and Places.
- `FULL = True` adds Smileys and Emotion, People and Body, and 8
  generic flags.
- No skin-tone variants and no country flags.
- English file names (`convenience_store.svg`), so the SVG browser's
  search box finds them by name.
- `index.csv`: one row per emoji (emoji, codepoint, name, name in your
  QGIS language, category, path), for scripts and AI assistants.
- Also usable as a [QGIS Resource Sharing](https://plugins.qgis.org/plugins/qgis_resource_sharing/)
  repository.

## License

- Emoji artwork: [Google Noto Emoji](https://github.com/googlefonts/noto-emoji),
  Apache-2.0. Subset, renamed and sorted into folders (see `NOTICE`).
- Scripts: MIT.
- The one-line installers run code from this repository. Read
  `install.py` first if you like; the URLs are pinned to a tag.

## Maintenance

Once a year, when new emoji come out:

1. `python3 build/update_from_upstream.py` and `python3 build/make_core.py`
2. Change the version (e.g. `v1.0.0` → `v1.1.0`) in `install.py` (`TAG`)
   and in every URL of this README.
3. Commit, tag and push:

   ```bash
   git add -A && git commit -m "Update emoji" && git tag v1.1.0 && git push && git push --tags
   ```

---

# 日本語

QGISで、カラーの絵文字（🏪 🚌 🏥 ♨️）をポイントのシンボルとして使えます。
Google の Noto Emoji を、Pythonコンソールに1行貼るだけでインストールします。

## インストール

1. QGISで **プラグイン → Pythonコンソール** を開く
2. 次の1行を貼って Enter

   ```python
   import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
   ```

3. 次のように表示されれば成功

   ```
   EmOji-san: 1060 files installed -> .../QGIS3/EmOji-san
     index.csv: 1058 emoji (+ name_ja)
     registered as an SVG path (Settings > Options > System)
   ```

4. ポイントレイヤの **シンボロジ** で、シンボルレイヤの種類を
   **SVGマーカー** にし、SVGブラウザの **EmOji-san** の下のカテゴリを選ぶ

## オプション

同じ1行の先頭に `;` で区切って付けます。
コンソールは1行ずつしか受け付けないので、1行のまま貼ってください。

- 顔・人物も含めた全部（1,595個）:
  `FULL = True; import urllib.request as u; exec(...)`
- `index.csv` の名前を別の言語にする:
  `LOCALE = 'de'; import urllib.request as u; exec(...)`

## コア200個（インストール不要）

- [Releases](../../releases) から `emoji_san_core.xml` をダウンロード
- **設定 → スタイルマネージャ → インポート/エクスポート → アイテムのインポート**
  でファイルを選び、**すべて選択** → **インポート**
- SVGがシンボルに埋め込まれているので、プロジェクトを他のPCに渡しても
  表示が崩れません

## インストールの確認

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

- 期待される表示: `Result: ALL GOOD (9 passed, 0 failed, 0 skipped)`
- 絵文字8個を置いた「EmOji-san demo」レイヤも追加されます。
  不要なら先頭に `DEMO = False; ` を付けます

## アンインストール

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/uninstall.py').read())
```

## SVGブラウザが遅い・固まるとき

- **設定 → オプション → システム → SVGパス** で、不要なフォルダを外す。
  特に、以前に登録したNoto Emojiの全セット（3,000個以上）や、
  ネットワークドライブ・共有フォルダ上のフォルダ
- SVGブラウザでは、一番上の **EmOji-san** ではなくカテゴリをクリックする
- 原因を調べるには診断を実行します。`LIKELY CAUSES` に原因が表示されます

  ```python
  import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/diagnose.py').read())
  ```

## 入っているもの

- 6カテゴリ1,058個: Activities, Animals and Nature, Food and Drink,
  Objects, Symbols, Travel and Places
- `FULL = True` で、顔（Smileys and Emotion）、人物（People and Body）、
  汎用の旗8個を追加
- 肌の色違いと国旗は含みません
- ファイル名は英語（`convenience_store.svg`）なので、SVGブラウザの検索欄で
  名前から探せます
- `index.csv`: 絵文字ごとに1行（絵文字、コードポイント、英語名、
  QGISの表示言語での名前、カテゴリ、パス）。スクリプトやAIアシスタント向け
- [QGIS Resource Sharing](https://plugins.qgis.org/plugins/qgis_resource_sharing/)
  のリポジトリとしても使えます

## ライセンス

- 絵文字: [Google Noto Emoji](https://github.com/googlefonts/noto-emoji)、
  Apache-2.0。一部を選び、名前を変え、フォルダに分けています（`NOTICE` 参照）
- スクリプト: MIT
- 1行インストールは、このリポジトリのコードを実行します。気になる場合は
  先に `install.py` を読んでください。URLはタグで版を固定しています

## メンテナンス

年1回、新しい絵文字が出たら:

1. `python3 build/update_from_upstream.py` と `python3 build/make_core.py` を実行
2. 版（例: `v1.0.0` → `v1.1.0`）を、`install.py` の `TAG` と
   このREADMEのすべてのURLで書き換える
3. コミットしてタグを付け、プッシュ

   ```bash
   git add -A && git commit -m "Update emoji" && git tag v1.1.0 && git push && git push --tags
   ```
