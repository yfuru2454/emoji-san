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
   EmOji-san S: 200 emoji (+200 added, -0 removed) -> .../QGIS3/EmOji-san
     index.csv (+ name_ja)
     registered as an SVG path (Settings > Options > System)
     saving a project embeds its EmOji-san SVGs: ON (turn off: EMBED=False; in front)
   ```

4. Open a point layer's **Symbology**, set the symbol layer type to
   **SVG Marker**, and pick a category under **EmOji-san** in the
   SVG browser.

## Choose a set

| Set | Emoji | What |
|---|---|---|
| `S` (default) | 200 | Hand-picked, easy to read at marker size |
| `M` | 1,109 | S + all of Activities, Animals and Nature, Food and Drink, Objects, Symbols, Travel and Places |
| `L` | 1,595 | M + all faces, people and 8 generic flags |

- Put `SET='S';`, `SET='M';` or `SET='L';` in front of the same line.
  The console only accepts one line, so keep it on one line:

  ```python
  SET='M'; import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
  ```

- Without `SET`: the first install is S; running it again keeps the size
  you have and just updates it.
- Run it again with another set at any time:
  - Upgrade (e.g. S → M): adds emoji, removes nothing.
  - Downgrade (e.g. L → S): removes the emoji that are not in the
    smaller set. Maps using them show `?` until you upgrade again.
- Names in another language in `index.csv`: `LOCALE='de';` in front.

## Saved projects work on any computer

- When you save a project, the EmOji-san SVGs it uses are embedded in
  the `.qgs` / `.qgz` file. Others can open it without EmOji-san.
- Only the saved file changes. Other SVGs are left as they are.
- It is on by default. To turn it off, run the install line with
  `EMBED=False;` in front. Run it again without that to turn it back on.
- How it works: the installer adds a few marked lines to `startup.py` in
  the QGIS settings folder, which QGIS runs at every start. Uninstall
  removes them.

## The S set as embedded symbols (no install needed)

- Download `emoji_san_core.xml` from [Releases](../../releases).
- **Settings → Style Manager → Import/Export → Import Items**,
  choose the file, **Select All**, **Import**.
- The SVGs are embedded, so projects using them work on other
  computers too.

## Check the install

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

- Expected: `Result: ALL GOOD (10 passed, 0 failed, 0 skipped)`
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

- Three nested sets: S (200) < M (1,109) < L (1,595).
- No skin-tone variants and no country flags (Noto has 3,750 SVGs in
  total; most of the rest are skin-tone variants).
- English file names (`convenience_store.svg`), so the SVG browser's
  search box finds them by name.
- `index.csv`: one row per installed emoji (emoji, codepoint, name, name
  in your QGIS language, category, path, set), for scripts and AI
  assistants.
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
   EmOji-san S: 200 emoji (+200 added, -0 removed) -> .../QGIS3/EmOji-san
     index.csv (+ name_ja)
     registered as an SVG path (Settings > Options > System)
     saving a project embeds its EmOji-san SVGs: ON (turn off: EMBED=False; in front)
   ```

4. ポイントレイヤの **シンボロジ** で、シンボルレイヤの種類を
   **SVGマーカー** にし、SVGブラウザの **EmOji-san** の下のカテゴリを選ぶ

## セットを選ぶ

| セット | 個数 | 中身 |
|---|---|---|
| `S`（初期設定） | 200 | マーカーの大きさでも見やすいものを厳選 |
| `M` | 1,109 | S ＋ Activities、Animals and Nature、Food and Drink、Objects、Symbols、Travel and Places の全部 |
| `L` | 1,595 | M ＋ 顔・人物の全部と汎用の旗8個 |

- 同じ1行の先頭に `SET='S';`、`SET='M';`、`SET='L';` のどれかを付けます。
  コンソールは1行しか受け付けないので、1行のまま貼ってください:

  ```python
  SET='M'; import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
  ```

- `SET` を付けない場合: 初回はS。2回目以降は、今のサイズのまま更新します
- 別のセットでいつでも実行し直せます:
  - アップグレード（例: S → M）: 絵文字を追加するだけで、何も消しません
  - ダウングレード（例: L → S）: 小さいセットにない絵文字を削除します。
    それを使っている地図は、アップグレードし直すまで `?` で表示されます
- `index.csv` の名前を別の言語にする: 先頭に `LOCALE='de';`

## 保存したプロジェクトはどのPCでも開ける

- プロジェクトを保存すると、使っているEmOji-sanのSVGが `.qgs` / `.qgz`
  の中に埋め込まれます。EmOji-sanを入れていない人でも開けます
- 変わるのは保存されるファイルだけです。ほかのSVGはそのままです
- 初期設定でオンです。オフにするには、インストールの1行の先頭に
  `EMBED=False;` を付けて実行します。付けずに実行し直すとオンに戻ります
- しくみ: インストーラが、QGISの設定フォルダにある `startup.py`
  （QGISが起動のたびに実行するファイル）に、印を付けた数行を追加します。
  アンインストールで消えます

## Sの200個を埋め込みシンボルで使う（インストール不要）

- [Releases](../../releases) から `emoji_san_core.xml` をダウンロード
- **設定 → スタイルマネージャ → インポート/エクスポート → アイテムのインポート**
  でファイルを選び、**すべて選択** → **インポート**
- SVGがシンボルに埋め込まれているので、プロジェクトを他のPCに渡しても
  表示が崩れません

## インストールの確認

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

- 期待される表示: `Result: ALL GOOD (10 passed, 0 failed, 0 skipped)`
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

- 入れ子の3セット: S（200）< M（1,109）< L（1,595）
- 肌の色違いと国旗は含みません（Notoの元データは3,750個で、残りの大半は
  肌の色違いです）
- ファイル名は英語（`convenience_store.svg`）なので、SVGブラウザの検索欄で
  名前から探せます
- `index.csv`: インストールした絵文字ごとに1行（絵文字、コードポイント、
  英語名、QGISの表示言語での名前、カテゴリ、パス、セット）。
  スクリプトやAIアシスタント向け
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
