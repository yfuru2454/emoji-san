# EmOji-san

Color emoji as point markers in QGIS: 🏪 🚌 🏥 ♨️

The emoji are Google's Noto Emoji as SVG files. One line in the QGIS Python
console installs them. It is not a plugin.

The name is Emoji plus Oji-san (おじさん, a middle-aged man). He signs the
message you get after the install.

Tested with QGIS 3.34, 3.44 and 4.4.

[日本語](#日本語)

## Install

1. In QGIS, open **Plugins → Python Console**.
2. Paste this line and press Enter.

   ```python
   import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
   ```

3. The console prints this. The folder depends on your system.

   ```
   EmOji-san: getting https://github.com/yfuru2454/emoji-san/archive/refs/tags/v1.0.0.zip
   200 emoji installed! Have fun with your maps 😃✨ Love, EmOji-san 👨‍💼
   EmOji-san S: 200 emoji (+200 added, -0 removed) -> C:\Users\you\AppData\Roaming\QGIS\QGIS3\EmOji-san
     index.csv
     registered as an SVG path (Settings > Options > System)
   Next: Symbology of a point layer > SVG Marker > SVG browser > EmOji-san > a category. Reopen the dialog if it was open.
   More emoji: SET='M'; in front of the same line (S 200, M 1,109, L 1,595).
   Sharing a project: embed the SVG in the symbol ("..." > Embed File), or run this again with EMBED=True; in front.
   ```

4. Open the **Symbology** of a point layer and set the symbol layer type to
   **SVG Marker**. In the **SVG browser**, the emoji are under **EmOji-san**,
   one folder per category.

## Sets

| Set | Emoji | Contents |
|---|---|---|
| `S` | 200 | The ones that stay readable at marker size. This is what you get if you do not choose. |
| `M` | 1,109 | S, and the rest of Activities, Animals and Nature, Food and Drink, Objects, Symbols, Travel and Places |
| `L` | 1,595 | M, and the rest of the faces and people, and 8 flags |

No set has skin-tone variants or country flags.

- To choose a set, put `SET='M';` in front of the line. The console runs one
  line at a time, so keep it on one line.

  ```python
  SET='M'; import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
  ```

- Run the line again with another `SET` to switch. A bigger set adds emoji.
  A smaller set deletes the emoji it does not have, and markers that used
  them show `?` until you go back to the bigger set.
- Without `SET`, running the line again keeps the set you have.

## Sharing a project

A marker stores where the SVG file is on your computer. On a computer
without EmOji-san it shows `?`. Before you pass a project on, do one of
these:

- In the settings of the SVG marker, click **…** next to the file name and
  choose **Embed File…**.
- Use the symbols from the style file in the next section. Their SVG is
  already inside.
- Put `EMBED=True;` in front of the install line. From then on QGIS embeds
  the EmOji-san SVGs every time it saves a project. This covers markers,
  fills and label backgrounds in layer styles, not pictures in print
  layouts. It works by adding a few marked lines to `startup.py` in the QGIS
  settings folder, which QGIS runs at every start. `EMBED=False;` removes
  them.

## The S set as symbols

`emoji_san_core.xml` on the [Releases](../../releases) page is a style file
with the S set as marker symbols. The SVG is inside each symbol, so it works
without the installer.

1. Download the file.
2. **Settings → Style Manager → Import/Export → Import Item(s)…**, choose
   the file, then **Select All** and **Import**.

The symbols are tagged `EmOji-san`.

## Check and uninstall

Check the install. The last line it prints should start with
`Result: ALL GOOD`. It also adds a layer with 8 emoji to the map;
`DEMO=False;` in front leaves that out.

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

Uninstall. It deletes the files it installed. Files of your own in the
folder stay. Symbols imported from the style file also stay; delete those in
the Style Manager.

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/uninstall.py').read())
```

## If the SVG browser is slow

Each time it opens, the SVG browser lists the SVGs of every folder under
**Settings → Options → System → SVG Paths**.

- Take the folders you do not need off that list. The usual cause is an old
  copy of all of Noto Emoji (more than 3,000 files) or a folder on a network
  drive.
- Click a category, not the **EmOji-san** folder itself.
- This line measures where the time goes and prints the `LIKELY CAUSES`:

  ```python
  import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/diagnose.py').read())
  ```

## QGIS 3 and QGIS 4

They have separate settings folders, so install in each. When QGIS 4 takes
over a QGIS 3 profile, it keeps pointing at the folder of QGIS 3. Run the
install line in QGIS 4 and it gets its own folder, with the same set.

## Without internet access from QGIS

Download the source ZIP of the release with a browser and take `install.py`
out of it. Then run this with your own paths (on Windows, write them as
`r'C:\...'`):

```python
ZIP='/path/to/emoji-san-1.0.0.zip'; exec(open('/path/to/install.py', 'rb').read())
```

## What is installed

- `EmOji-san/<Category>/<name>.svg` in the QGIS settings folder, the one
  that holds `profiles`. On Windows that is
  `%APPDATA%\QGIS\QGIS3`, on macOS
  `~/Library/Application Support/QGIS/QGIS3`, on Linux
  `~/.local/share/QGIS/QGIS3` (`QGIS4` for QGIS 4).
- The file names are the English emoji names, like `convenience_store.svg`.
  The search box of the SVG browser finds them.
- `index.csv` in the same folder has one line per emoji: the emoji, its code
  point, the English name, the name in the language of your QGIS, the
  category, the path, the set and Noto's file name. Scripts and AI
  assistants can look emoji up in it. `LOCALE='de';` in front of the install
  line chooses another language for the names.

## Resource Sharing plugin

The repository can also be added to the QGIS Resource Sharing plugin
(QGIS 3). The plugin keeps the files in a folder of its own, under other
paths. A project made that way does not find the emoji installed by the line
above, so use one or the other.

## License

- Emoji: [Google Noto Emoji](https://github.com/googlefonts/noto-emoji),
  Apache License 2.0. EmOji-san takes part of the SVG files, renames them
  and sorts them into folders. The files themselves are unchanged. Details
  are in `NOTICE`.
- Scripts: MIT.
- The lines above run code from this repository. The URLs point at a tag,
  which is a fixed version of the code. Read `install.py` first if you want
  to know what it does.

## Maintenance

Once a year, when Noto Emoji has the new emoji:

1. `python3 build/update_from_upstream.py` fetches the SVG files and
   rebuilds `index.csv` and the style file. It lists the emoji that are new
   and those that are gone. To change the S set, edit `core_list.txt` and
   run `python3 build/make_core.py`.
2. Change the version in `TAG` in `install.py` and everywhere in this
   README (search for the old number), and correct the numbers in the Sets
   table.
3. `python3 tests/scenarios.py` runs install, upgrade, downgrade, embedding
   and uninstall in an empty QGIS settings folder, and checks that step 2
   left nothing out. It needs a Python that can import `qgis`; the head of
   the file shows how to run it in Docker.
4. Commit, tag and push, then attach the style file to the release:

   ```bash
   git add -A && git commit -m "v1.1.0" && git tag v1.1.0 && git push && git push --tags
   gh release create v1.1.0 styles/emoji_san_core.xml --title "EmOji-san v1.1.0" --notes "Noto Emoji as of 2027"
   ```

---

# 日本語

QGISで、カラーの絵文字をポイントのマーカーに使えるようにします: 🏪 🚌 🏥 ♨️

絵文字はGoogleのNoto EmojiのSVGです。QGISのPythonコンソールに1行貼るとインストールされます。プラグインではありません。

名前はEmojiと「おじさん」から付けました。インストールが終わると、おじさんがひとこと挨拶します。

QGIS 3.34、3.44、4.4で動作を確認しています。

## インストール

1. QGISで **プラグイン → Pythonコンソール** を開きます。
2. 次の1行を貼り付けてEnterを押します。

   ```python
   import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
   ```

3. コンソールに次のように表示されます。フォルダの場所は環境によって違います。

   ```
   EmOji-san: getting https://github.com/yfuru2454/emoji-san/archive/refs/tags/v1.0.0.zip
   EmOji-san👨‍💼参上❗ 200個の絵文字をお届けしたヨ😃✨ 地図がにぎやかになるネ🗾💕
   EmOji-san S: 200 emoji (+200 added, -0 removed) -> /Users/you/Library/Application Support/QGIS/QGIS3/EmOji-san
     index.csv (+ name_ja)
     registered as an SVG path (Settings > Options > System)
   Next: Symbology of a point layer > SVG Marker > SVG browser > EmOji-san > a category. Reopen the dialog if it was open.
   More emoji: SET='M'; in front of the same line (S 200, M 1,109, L 1,595).
   Sharing a project: embed the SVG in the symbol ("..." > Embed File), or run this again with EMBED=True; in front.
   ```

4. ポイントレイヤの **シンボロジ** を開き、シンボルレイヤの種類を **SVGマーカー** にします。**SVGブラウザ** の **EmOji-san** の下に、カテゴリごとのフォルダで並んでいます。

## セット

| セット | 個数 | 中身 |
|---|---|---|
| `S` | 200 | マーカーの大きさでも見分けやすいもの。何も指定しなければこれが入ります |
| `M` | 1,109 | Sと、Activities、Animals and Nature、Food and Drink、Objects、Symbols、Travel and Placesの残り全部 |
| `L` | 1,595 | Mと、顔・人物の残り全部、旗8個 |

どのセットにも、肌の色違いと国旗は入っていません。

- セットを選ぶには、行の先頭に`SET='M';`を付けます。コンソールは1行ずつ実行するので、1行のまま貼ってください。

  ```python
  SET='M'; import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/install.py').read())
  ```

- 別の`SET`を付けて実行し直すと、セットが切り替わります。大きくすると絵文字が増えます。小さくすると、そのセットにない絵文字は削除され、それを使っていたマーカーは大きいセットに戻すまで`?`になります。
- `SET`を付けずに実行し直したときは、今のセットのままです。

## プロジェクトを人に渡すとき

マーカーには、自分のPCにあるSVGファイルの場所が記録されています。EmOji-sanを入れていないPCで開くと`?`になります。渡す前に、次のどれかをしておきます。

- SVGマーカーの設定で、ファイル名の右の **…** から **ファイルを埋め込む...** を選びます。
- 次の節のスタイルファイルのシンボルを使います。SVGが最初から入っています。
- インストールの行の先頭に`EMBED=True;`を付けて実行します。それ以降、プロジェクトを保存するたびにQGISがEmOji-sanのSVGを埋め込みます。対象はレイヤのスタイルにあるマーカー、塗りつぶし、ラベルの背景で、印刷レイアウトの画像は対象外です。QGISが起動のたびに実行する`startup.py`（QGISの設定フォルダにあります）に、目印を付けた数行を書き足すしくみです。`EMBED=False;`で消えます。

## Sのセットをシンボルとして使う

[Releases](../../releases)にある`emoji_san_core.xml`は、Sのセットをマーカーシンボルにしたスタイルファイルです。SVGがシンボルの中に入っているので、インストールしなくても使えます。

1. ファイルをダウンロードします。
2. **設定 → スタイルマネージャ → インポートとエクスポート → アイテムのインポート...** でファイルを選び、**すべて選択**、**インポート** の順に押します。

シンボルには`EmOji-san`というタグが付きます。

## 確認とアンインストール

インストールの確認です。最後の行が`Result: ALL GOOD`で始まっていれば問題ありません。絵文字8個のレイヤも地図に追加されます。先頭に`DEMO=False;`を付けると追加されません。

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/check_install.py').read())
```

アンインストールです。インストールしたファイルを削除します。フォルダに自分で置いたファイルは残ります。スタイルファイルからインポートしたシンボルも残るので、スタイルマネージャで削除してください。

```python
import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/uninstall.py').read())
```

## SVGブラウザが遅いとき

SVGブラウザは開くたびに、**設定 → オプション → システム → SVGパス** にあるすべてのフォルダのSVGを一覧にします。

- 使っていないフォルダを一覧から外します。以前に登録したNoto Emoji全部入りのフォルダ（3,000個以上）や、ネットワークドライブ上のフォルダが原因になっていることが多いです。
- **EmOji-san** フォルダそのものではなく、カテゴリをクリックします。
- 次の行は、どこで時間がかかっているかを測って、`LIKELY CAUSES`として表示します。

  ```python
  import urllib.request as u; exec(u.urlopen('https://raw.githubusercontent.com/yfuru2454/emoji-san/v1.0.0/tests/diagnose.py').read())
  ```

## QGIS 3とQGIS 4

設定フォルダが別なので、それぞれでインストールします。QGIS 4がQGIS 3のプロファイルを引き継いだあとは、QGIS 3側のフォルダを参照し続けます。QGIS 4でインストールの行を実行すると、同じセットがQGIS 4側のフォルダに入ります。

## QGISからインターネットに出られないとき

リリースのソースのZIPをブラウザでダウンロードして、中の`install.py`を取り出します。次の行のパスを自分のものに書き換えて実行します（Windowsでは`r'C:\...'`の形で書きます）。

```python
ZIP='/path/to/emoji-san-1.0.0.zip'; exec(open('/path/to/install.py', 'rb').read())
```

## インストールされるもの

- QGISの設定フォルダ（`profiles`があるフォルダ）の中の`EmOji-san/<カテゴリ>/<名前>.svg`。設定フォルダは、Windowsでは`%APPDATA%\QGIS\QGIS3`、macOSでは`~/Library/Application Support/QGIS/QGIS3`、Linuxでは`~/.local/share/QGIS/QGIS3`です（QGIS 4は`QGIS4`）。
- ファイル名は`convenience_store.svg`のような絵文字の英語名です。SVGブラウザの検索欄で探せます。
- 同じフォルダの`index.csv`は、絵文字1個につき1行の一覧です。絵文字、コードポイント、英語名、QGISの表示言語での名前、カテゴリ、パス、セット、Notoでのファイル名が入っています。スクリプトやAIアシスタントが絵文字を探すのに使えます。インストールの行の先頭に`LOCALE='de';`を付けると、名前の言語を変えられます。

## Resource Sharingプラグイン

このリポジトリはQGIS Resource Sharingプラグイン（QGIS 3）にも登録できます。ただし、プラグインは絵文字を別のフォルダに別のパスで保存します。その絵文字で作ったプロジェクトは、上の1行で入れた絵文字を参照できません。どちらか一方を使ってください。

## ライセンス

- 絵文字: [Google Noto Emoji](https://github.com/googlefonts/noto-emoji)、Apache License 2.0。EmOji-sanはSVGファイルの一部を選び、名前を変えてフォルダに分けています。ファイルの中身は変えていません。詳しくは`NOTICE`にあります。
- スクリプト: MIT。
- 上の各行は、このリポジトリのコードを実行します。URLはタグ（固定した版）を指しています。何をするのか知りたいときは、先に`install.py`を読んでください。

## メンテナンス

年に1回、Noto Emojiに新しい絵文字が入ったら:

1. `python3 build/update_from_upstream.py`でSVGファイルを取得し、`index.csv`とスタイルファイルを作り直します。増えた絵文字と消えた絵文字が表示されます。Sのセットを変えるときは`core_list.txt`を編集して`python3 build/make_core.py`を実行します。
2. `install.py`の`TAG`と、このREADMEにあるバージョン（古い番号で検索すると見つかります）をすべて書き換え、セットの表の個数を直します。
3. `python3 tests/scenarios.py`は、空のQGIS設定フォルダで、インストール、セットの切り替え、埋め込み、アンインストールを通しで実行し、2の書き換え漏れも調べます。`qgis`をimportできるPythonが必要です。Dockerでの実行方法はファイルの先頭にあります。
4. コミットしてタグを付け、プッシュしてから、スタイルファイルをリリースに添付します。

   ```bash
   git add -A && git commit -m "v1.1.0" && git tag v1.1.0 && git push && git push --tags
   gh release create v1.1.0 styles/emoji_san_core.xml --title "EmOji-san v1.1.0" --notes "Noto Emoji as of 2027"
   ```
