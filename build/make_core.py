#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core set tooling: candidate list -> review HTML + core_list.txt
+ QGIS style XML (embedded SVG symbols), shipped via GitHub Releases.

    python3 build/make_core.py

Outputs:
  core_list.txt                 slug<TAB>category (edit = the one source)
  styles/emoji_san_core.xml    embedded-SVG symbols, import via Style Manager
  review_core.html              visual review sheet (toggle to exclude,
                                copy the resulting list back into CORE)

Selection rationale: emoji that correspond to Mapbox Maki icons or major
OSM POI tags (= symbols with cartographic precedent), plus Japanese map
staples (hot springs, shrine, castle, Mt. Fuji...). Trim to taste.
"""
import base64
import html
import pathlib
from xml.sax.saxutils import escape

ROOT = pathlib.Path(__file__).resolve().parent.parent

# (slug, category-folder, reason) — edit freely, then rerun.
CORE = [
    # --- Travel and Places: shops/buildings ---
    ("convenience_store", "Travel and Places", "OSM shop=convenience"),
    ("department_store", "Travel and Places", "OSM shop=department_store"),
    ("bank", "Travel and Places", "Maki: bank"),
    ("hospital", "Travel and Places", "Maki: hospital"),
    ("hotel", "Travel and Places", "Maki: lodging"),
    ("school", "Travel and Places", "Maki: school"),
    ("post_office", "Travel and Places", "Maki: post"),
    ("japanese_post_office", "Travel and Places", "JP: 郵便局〒"),
    ("office_building", "Travel and Places", "OSM office=*"),
    ("house", "Travel and Places", "Maki: home"),
    ("factory", "Travel and Places", "Maki: industry"),
    ("church", "Travel and Places", "Maki: religious-christian"),
    ("mosque", "Travel and Places", "Maki: religious-muslim"),
    ("synagogue", "Travel and Places", "Maki: religious-jewish"),
    ("hindu_temple", "Travel and Places", "OSM religion=hindu"),
    ("shinto_shrine", "Travel and Places", "JP: 神社⛩（地図記号）"),
    ("japanese_castle", "Travel and Places", "JP: 城跡（地図記号）"),
    ("castle", "Travel and Places", "Maki: castle"),
    ("classical_building", "Travel and Places", "Maki: museum（博物館風建物）"),
    ("stadium", "Travel and Places", "Maki: stadium"),
    ("tent", "Travel and Places", "Maki: campsite"),
    ("fountain", "Travel and Places", "OSM amenity=fountain"),
    ("tokyo_tower", "Travel and Places", "JP: タワー/展望"),
    ("ferris_wheel", "Travel and Places", "Maki: amusement-park"),
    ("construction", "Travel and Places", "Maki: construction／工事"),
    ("playground_slide", "Travel and Places", "OSM leisure=playground"),
    # --- Travel and Places: transport ---
    ("bus", "Travel and Places", "Maki: bus"),
    ("tram", "Travel and Places", "OSM railway=tram"),
    ("taxi", "Travel and Places", "OSM amenity=taxi"),
    ("automobile", "Travel and Places", "Maki: car"),
    ("delivery_truck", "Travel and Places", "物流/配送"),
    ("bicycle", "Travel and Places", "Maki: bicycle"),
    ("motorcycle", "Travel and Places", "バイク駐輪/販売"),
    ("station", "Travel and Places", "Maki: rail（駅）"),
    ("metro", "Travel and Places", "Maki: rail-metro"),
    ("bullet_train", "Travel and Places", "JP: 新幹線"),
    ("train", "Travel and Places", "OSM railway"),
    ("airplane", "Travel and Places", "Maki: airport"),
    ("small_airplane", "Travel and Places", "Maki: airfield"),
    ("helicopter", "Travel and Places", "Maki: heliport"),
    ("ferry", "Travel and Places", "Maki: ferry"),
    ("ship", "Travel and Places", "港湾/大型船"),
    ("sailboat", "Travel and Places", "Maki: harbor（マリーナ）"),
    ("anchor", "Travel and Places", "Maki: harbor"),
    ("fuel_pump", "Travel and Places", "Maki: fuel"),
    ("police_car", "Travel and Places", "Maki: police"),
    ("fire_engine", "Travel and Places", "Maki: fire-station"),
    ("ambulance", "Travel and Places", "OSM emergency=ambulance_station"),
    # --- Travel and Places: nature/landmarks ---
    ("mount_fuji", "Travel and Places", "JP: 富士山/名山"),
    ("mountain", "Travel and Places", "Maki: mountain"),
    ("volcano", "Travel and Places", "Maki: volcano"),
    ("beach_with_umbrella", "Travel and Places", "Maki: beach"),
    ("hot_springs", "Travel and Places", "JP: 温泉♨（地図記号）"),
    ("high_voltage", "Travel and Places", "電力設備/感電注意"),
    # --- Food and Drink ---
    ("fork_and_knife_with_plate", "Food and Drink", "Maki: restaurant"),
    ("steaming_bowl", "Food and Drink", "JP: ラーメン/麺類"),
    ("sushi", "Food and Drink", "JP: 寿司"),
    ("rice_ball", "Food and Drink", "JP: おにぎり/軽食"),
    ("hamburger", "Food and Drink", "Maki: fast-food"),
    ("pizza", "Food and Drink", "OSM cuisine=pizza"),
    ("hot_beverage", "Food and Drink", "Maki: cafe"),
    ("beer_mug", "Food and Drink", "Maki: beer（パブ/ビアガーデン）"),
    ("wine_glass", "Food and Drink", "ワイナリー/バー"),
    ("cocktail_glass", "Food and Drink", "Maki: bar"),
    ("sake", "Food and Drink", "JP: 酒蔵/居酒屋"),
    ("bread", "Food and Drink", "Maki: bakery"),
    ("birthday_cake", "Food and Drink", "OSM shop=confectionery"),
    ("ice_cream", "Food and Drink", "Maki: ice-cream"),
    ("bento_box", "Food and Drink", "JP: 弁当/惣菜"),
    ("tropical_drink", "Food and Drink", "リゾート/ジューススタンド"),
    # --- Animals and Nature ---
    ("cherry_blossom", "Animals and Nature", "JP: 花見名所"),
    ("maple_leaf", "Animals and Nature", "JP: 紅葉名所"),
    ("deciduous_tree", "Animals and Nature", "OSM natural=tree（広葉樹）"),
    ("evergreen_tree", "Animals and Nature", "OSM natural=tree（針葉樹）"),
    ("palm_tree", "Animals and Nature", "南国/海辺"),
    ("sunflower", "Animals and Nature", "花畑/農園"),
    ("dog_face", "Animals and Nature", "Maki: dog-park"),
    ("cat_face", "Animals and Nature", "猫スポット/保護猫"),
    ("horse_face", "Animals and Nature", "Maki: horse-riding"),
    ("cow_face", "Animals and Nature", "牧場/畜産"),
    ("fish", "Animals and Nature", "Maki: aquarium／釣り場"),
    ("bird", "Animals and Nature", "バードウォッチング"),
    ("paw_prints", "Animals and Nature", "野生動物/動物注意"),
    ("spouting_whale", "Animals and Nature", "ホエールウォッチング"),
    # --- Activities ---
    ("soccer_ball", "Activities", "Maki: soccer"),
    ("baseball", "Activities", "Maki: baseball"),
    ("basketball", "Activities", "Maki: basketball"),
    ("tennis", "Activities", "Maki: tennis"),
    ("flag_in_hole", "Activities", "Maki: golf"),
    ("skis", "Activities", "Maki: skiing"),
    ("fishing_pole", "Activities", "OSM leisure=fishing"),
    ("performing_arts", "Activities", "Maki: theatre"),
    ("artist_palette", "Activities", "Maki: art-gallery"),
    ("video_game", "Activities", "OSM leisure=amusement_arcade"),
    # --- Objects ---
    ("camera", "Objects", "Maki: attraction（撮影スポット）"),
    ("books", "Objects", "Maki: library"),
    ("graduation_cap", "Objects", "Maki: college"),
    ("bed", "Objects", "宿泊（ゲストハウス/民泊）"),
    ("toilet", "Objects", "Maki: toilet"),
    ("pill", "Objects", "Maki: pharmacy"),
    ("syringe", "Objects", "接種会場/クリニック"),
    ("stethoscope", "Objects", "OSM amenity=doctors（診療所）"),
    ("hammer_and_wrench", "Objects", "Maki: hardware（修理/工務店）"),
    ("scissors", "Objects", "Maki: hairdresser（理美容）"),
    ("shopping_cart", "Objects", "Maki: grocery（スーパー）"),
    ("shopping_bags", "Objects", "OSM shop=mall"),
    ("telephone", "Objects", "Maki: telephone（公衆電話）"),
    ("musical_note", "Objects", "Maki: music（ライブ/カラオケ）"),
    ("fire_extinguisher", "Objects", "防災: 消火設備"),
    ("wastebasket", "Objects", "Maki: waste-basket（ごみ箱）"),
    # --- Symbols ---
    ("warning", "Symbols", "防災: 注意/危険箇所"),
    ("no_entry", "Symbols", "通行止め"),
    ("prohibited", "Symbols", "立入禁止"),
    ("wheelchair_symbol", "Symbols", "Maki: wheelchair（バリアフリー）"),
    ("restroom", "Symbols", "公衆トイレ（男女）"),
    ("atm_sign", "Symbols", "OSM amenity=atm"),
    ("information", "Symbols", "Maki: information（案内所）"),
    ("p_button", "Symbols", "Maki: parking（駐車場P）"),
    ("potable_water", "Symbols", "Maki: drinking-water（水飲み場）"),
    ("recycling_symbol", "Symbols", "Maki: recycling"),
    ("children_crossing", "Symbols", "スクールゾーン"),
    ("sos_button", "Symbols", "防災: 緊急/避難"),
    ("cinema", "Symbols", "Maki: cinema（映画館）"),
    ("fire", "Travel and Places", "防災: 火災／話題スポット"),
    ("circus_tent", "Travel and Places", "イベント会場/サーカス"),
    ("red_paper_lantern", "Objects", "JP: 居酒屋/祭り"),
    ("hiking_boot", "Objects", "ハイキング/遊歩道"),
    ("running_shoe", "Objects", "ランニングコース"),
    ("ring_buoy", "Travel and Places", "プール/海水浴/水難救助"),
    ("water_wave", "Travel and Places", "サーフ/水辺"),
    ("canoe", "Travel and Places", "カヌー/ボート"),
    ("bathtub", "Objects", "銭湯/入浴施設"),
    ("lotus", "Animals and Nature", "ヨガ/瞑想"),
    ("white_cane", "Objects", "バリアフリー: 視覚"),
    ("snowflake", "Travel and Places", "防災: 凍結/積雪"),
    ("trophy", "Activities", "大会/表彰"),
    ("balloon", "Activities", "イベント/集合場所"),
    ("tractor", "Travel and Places", "農園/農道"),
    ("round_pushpin", "Objects", "汎用ピン（定番マーカー）"),
    ("compass", "Travel and Places", "方位/オリエンテーリング"),
    ("package", "Objects", "宅配/物流拠点"),
    ("key", "Objects", "不動産/レンタル/鍵"),
    ("locked", "Objects", "施錠/立入制限"),
    ("money_bag", "Objects", "金融/両替"),
    ("umbrella", "Travel and Places", "雨天対応/レンタル傘"),
    ("chair", "Objects", "ベンチ/休憩所"),
    ("placard", "Objects", "案内板/掲示"),
    ("microscope", "Objects", "研究所"),
    ("laptop", "Objects", "IT/コワーキング"),
    # --- Smileys and Emotion: 評価・感情の可視化 ---
    ("grinning_face", "Smileys and Emotion", "評価: ポジティブ"),
    ("smiling_face_with_smiling_eyes", "Smileys and Emotion", "評価: 満足"),
    ("smiling_face_with_heart_eyes", "Smileys and Emotion", "大人気スポット"),
    ("star_struck", "Smileys and Emotion", "絶景/感動スポット"),
    ("face_savoring_food", "Smileys and Emotion", "グルメ: 美味"),
    ("smiling_face_with_sunglasses", "Smileys and Emotion", "リゾート/おしゃれ"),
    ("thinking_face", "Smileys and Emotion", "検討中/疑問点"),
    ("neutral_face", "Smileys and Emotion", "評価: 中立"),
    ("slightly_smiling_face", "Smileys and Emotion", "評価: やや良い"),
    ("confused_face", "Smileys and Emotion", "評価: やや不満"),
    ("disappointed_face", "Smileys and Emotion", "評価: 不満"),
    ("crying_face", "Smileys and Emotion", "残念/悲しい"),
    ("loudly_crying_face", "Smileys and Emotion", "大不満/感動"),
    ("angry_face", "Smileys and Emotion", "苦情地点"),
    ("enraged_face", "Smileys and Emotion", "強い苦情"),
    ("face_screaming_in_fear", "Smileys and Emotion", "危険/恐怖"),
    ("face_with_medical_mask", "Smileys and Emotion", "感染対策/医療"),
    ("face_with_thermometer", "Smileys and Emotion", "発熱外来/体調"),
    ("nauseated_face", "Smileys and Emotion", "悪臭/公害地点"),
    ("sleeping_face", "Smileys and Emotion", "休憩/宿泊"),
    ("partying_face", "Smileys and Emotion", "イベント/祭り"),
    ("face_with_tears_of_joy", "Smileys and Emotion", "世界最頻出絵文字"),
    ("pile_of_poo", "Smileys and Emotion", "下水/トイレ/ネタ地点💩"),
    ("skull", "Smileys and Emotion", "廃墟/心霊スポット"),
    ("ghost", "Smileys and Emotion", "お化け屋敷/怪談"),
    ("robot", "Smileys and Emotion", "テック/自動化"),
    ("alien", "Smileys and Emotion", "ミステリースポット"),
    ("red_heart", "Smileys and Emotion", "お気に入り地点"),
    ("broken_heart", "Smileys and Emotion", "閉店/喪失"),
    ("hundred_points", "Smileys and Emotion", "評価: 100点"),
    ("collision", "Smileys and Emotion", "事故地点"),
    ("zzz", "Smileys and Emotion", "休憩所/仮眠"),
    ("speech_balloon", "Smileys and Emotion", "口コミ/コメント"),
    # --- People and Body: ジェスチャー ---
    ("thumbs_up", "People and Body", "評価: 高"),
    ("thumbs_down", "People and Body", "評価: 低"),
    ("ok_hand", "People and Body", "OK/承認"),
    ("waving_hand", "People and Body", "受付/ようこそ"),
    ("clapping_hands", "People and Body", "イベント/称賛"),
    ("folded_hands", "People and Body", "寺社/祈り/感謝"),
    ("handshake", "People and Body", "提携/取引先"),
    ("flexed_biceps", "People and Body", "ジム/トレーニング"),
    ("eyes", "People and Body", "注目/監視"),
    ("footprints", "People and Body", "散策路/痕跡"),
    # --- People and Body: 属性（施設対応） ---
    ("person", "People and Body", "汎用人物"),
    ("baby", "People and Body", "乳幼児/託児"),
    ("child", "People and Body", "子ども向け"),
    ("older_person", "People and Body", "高齢者施設"),
    ("family", "People and Body", "ファミリー向け"),
    ("couple_with_heart", "People and Body", "デートスポット"),
    ("busts_in_silhouette", "People and Body", "混雑/グループ"),
    ("pregnant_person", "People and Body", "マタニティ対応"),
    # --- People and Body: 職業＝施設 ---
    # --- People and Body: 動作＝アクティビティ ---
]

SIZE_MM = "5"


def svg_path(slug, cat):
    for coll in ("noto_emoji_map", "noto_emoji_people"):
        p = ROOT / "collections" / coll / "svg" / cat / f"{slug}.svg"
        if p.exists():
            return p
    return None


def make_symbol_xml(name, tags, b64):
    props = [("name", "base64:" + b64), ("size", SIZE_MM),
             ("size_unit", "MM"), ("angle", "0"), ("offset", "0,0"),
             ("offset_unit", "MM"), ("scale_method", "diameter"),
             ("vertical_anchor_point", "1"),
             ("horizontal_anchor_point", "1")]
    ps = "".join(f'\n      <prop k="{k}" v="{escape(v)}"/>' for k, v in props)
    return (f'  <symbol alpha="1" clip_to_extent="1" type="marker" '
            f'name="{escape(name)}" tags="{escape(tags)}" favorite="0">\n'
            f'    <layer pass="0" class="SvgMarker" locked="0" enabled="1">'
            f'{ps}\n    </layer>\n  </symbol>')


def main():
    missing = [(s, c) for s, c, _ in CORE if not svg_path(s, c)]
    if missing:
        raise SystemExit(f"missing svgs: {missing}")
    dupes = {s for s, _, _ in CORE if [x[0] for x in CORE].count(s) > 1}
    if dupes:
        raise SystemExit(f"duplicate slugs: {dupes}")

    # 1) core_list.txt
    (ROOT / "core_list.txt").write_text(
        "".join(f"{s}\t{c}\n" for s, c, _ in CORE), encoding="utf-8")

    # 2) style XML
    syms = []
    for slug, cat, _ in CORE:
        b64 = base64.b64encode(svg_path(slug, cat).read_bytes()).decode()
        syms.append(make_symbol_xml(slug, f"EmOji-san,Noto Emoji,{cat}", b64))
    xml = ('<!DOCTYPE qgis_style>\n<qgis_style version="2">\n<symbols>\n'
           + "\n".join(syms) + "\n</symbols>\n<colorramps/>\n</qgis_style>\n")
    out = ROOT / "styles" / "emoji_san_core.xml"
    out.parent.mkdir(exist_ok=True)
    out.write_text(xml, encoding="utf-8")

    # 3) review HTML
    cats, seen = [], set()
    for _, c, _ in CORE:
        if c not in seen:
            cats.append(c); seen.add(c)
    cards = []
    for slug, cat, reason in CORE:
        b64 = base64.b64encode(svg_path(slug, cat).read_bytes()).decode()
        cards.append(
            f'<div class="card" data-slug="{html.escape(slug)}" '
            f'data-cat="{html.escape(cat)}" onclick="tg(this)">'
            f'<img src="data:image/svg+xml;base64,{b64}">'
            f'<div class="nm">{html.escape(slug)}</div>'
            f'<div class="rs">{html.escape(reason)}</div></div>')
    cat_sections = []
    for c in cats:
        inner = "".join(cd for (s2, c2, r2), cd in zip(CORE, cards) if c2 == c)
        cat_sections.append(
            f'<h2>{html.escape(c)} '
            f'<span class="cnt" data-cat="{html.escape(c)}"></span></h2>'
            f'<div class="grid">{inner}</div>')
    page = """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Core emoji review</title><style>
:root{color-scheme:light}body{font-family:'Noto Sans CJK JP','Hiragino Sans',
'Yu Gothic',sans-serif;background:#fcfbf7;margin:24px;color:#2b2b2b}
h1{font-size:22px}h2{font-size:17px;margin:26px 0 8px;color:#9a4a00}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
gap:8px}.card{background:#fff;border:1.5px solid #e0d8c8;border-radius:10px;
padding:8px;cursor:pointer;text-align:center;user-select:none}
.card img{width:44px;height:44px}.nm{font-size:12px;font-weight:600;
word-break:break-all}.rs{font-size:10.5px;color:#8a7a5c;margin-top:2px}
.card.off{opacity:.32;filter:grayscale(1);border-style:dashed}
#bar{position:sticky;top:0;background:#fcfbf7ee;padding:10px 0;z-index:9}
#total{font-weight:700;color:#1f6b33}textarea{width:100%;height:110px;
font:12px/1.5 monospace;margin-top:10px}.cnt{color:#999;font-size:13px;
font-weight:400}</style></head><body>
<div id="bar"><h1>コア絵文字 候補レビュー（クリックで除外⇔採用）</h1>
<div>採用: <span id="total"></span> 個 — 確定したら下のリストを
build/make_core.py の CORE に反映（除外行を消すだけ）</div></div>
__SECTIONS__
<h2>採用スラッグ一覧（コピー用）</h2><textarea id="out" readonly></textarea>
<script>
function upd(){const on=[...document.querySelectorAll('.card:not(.off)')];
document.getElementById('total').textContent=on.length;
document.querySelectorAll('.cnt').forEach(e=>{const c=e.dataset.cat;
e.textContent='('+document.querySelectorAll(
'.card[data-cat="'+c+'"]:not(.off)').length+')';});
document.getElementById('out').value=on.map(e=>e.dataset.slug).join('\\n');}
function tg(el){el.classList.toggle('off');upd()}upd();
</script></body></html>"""
    page = page.replace("__SECTIONS__", "".join(cat_sections))
    (ROOT / "review_core.html").write_text(page, encoding="utf-8")

    kb = len(xml) // 1024
    print(f"candidates: {len(CORE)}  style xml: {kb} KB")
    print("wrote core_list.txt, styles/emoji_san_core.xml, review_core.html")


if __name__ == "__main__":
    main()
