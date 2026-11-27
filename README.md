# EmOji-san

Color emoji as point markers in QGIS: 🏪 🚌 🏥 ♨️

<img width="432" height="227" alt="image" src="https://github.com/user-attachments/assets/c3a51cfe-4dd8-4339-8f35-9e936d36959d" />

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
   import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/install.py').read())
   ```

3. The console prints this. The folder depends on your system.

   ```
   EmOji-san: getting https://github.com/yfuru2454/emoji-san/releases/download/v1.1.0/emoji_san_data.zip
   300 emoji delivered❗ Have fun with your maps 😃✨🗺️💕 Love, EmOji-san 👨‍💼😘
   EmOji-san S: 300 emoji (+300 added, -0 removed) -> C:\Users\you\AppData\Roaming\QGIS\QGIS3\EmOji-san
     index.csv
     registered as an SVG path (Settings > Options > System)
   Next: Symbology of a point layer > SVG Marker > SVG browser > EmOji-san > a category. Reopen the dialog if it was open.
   More emoji: SET='M'; in front of the same line (S 300, M 1,076, L 1,923).
   Sharing a project: embed the SVG in the symbol ("..." > Embed File), or run this again with EMBED=True; in front.
   ```

4. Open the **Symbology** of a point layer and set the symbol layer type to
   **SVG Marker**. In the **SVG browser**, the emoji are under **EmOji-san**,
   one folder per category.

The line always takes the latest release. To install a particular
version, write `download/v1.1.0/` in place of `latest/download/`.

## Sets

| Set | Emoji | Contents |
|---|---|---|
| `S` | 300 | The ones that stay readable at marker size. This is what you get if you do not choose. |
| `M` | 1,076 | S, all the faces, and the rest of Activities, Animals and Nature, Food and Drink, Objects, Symbols, Travel and Places, except clocks, zodiac signs, player buttons, clothes, games, musical instruments and the like (`l_only_list.txt`) |
| `L` | 1,923 | M, and the rest: people and hands, and all the flags, country and subdivision flags included |

No set has skin-tone variants.

<!-- sets:en begin: written by build/make_core.py from index.csv -->
<details>
<summary>S: the 300 emoji</summary>

**Smileys & Emotion** (42)<br>
😀😆😅😂🙂😉😊😇🥰😍🤩😘😋😜🤗🤔😐😴😷🤒🤢🥳😎😕🥺😢😭😱😞😡😠💀💩👻👽🤖💔❤️💯💥💬💤

**People & Body** (19)<br>
👋👌👍👎👏🙌🤝🙏💪👀👶🧒🧑🧓🫄💑👪👥👣

**Animals & Nature** (42)<br>
🐵🐶🦊🐱🦁🐯🐴🦌🐮🐷🐗🦒🐘🐰🐻🐨🐼🐾🐦🐧🦆🦉🐸🐢🐳🐬🐟🦋🌸🪷🌺🌻🌷🌱🌲🌳🌴🌵🌾🌿🍁🍄

**Food & Drink** (31)<br>
🍇🍊🍎🍑🍓🍞🥐🍔🍕🍱🍙🍛🍜🍝🍢🍣🍤🍡🍦🍨🎂🍰☕🍵🍶🍷🍸🍹🍺🧋🍽️

**Travel & Places** (91)<br>
🗺️🗾🧭🏔️⛰️🌋🗻🏕️🏖️🏝️🏞️🏟️🏛️🏗️🪨🏘️🏠🏡🏢🏣🏤🏥🏦🏨🏪🏫🏬🏭🏯🏰🗼⛪🕌🛕🕍⛩️⛲⛺🌅♨️🛝🎡🎢🎪🚄🚅🚆🚇🚉🚊🚋🚌🚑🚒🚓🚕🚗🚚🚜🏍️🚲🚏⛽🚦🛑🚧⚓🛟⛵🛶🛳️⛴️🚢✈️🛩️🛫🚁🚠☀️⭐🌌⛅🌧️🌨️🌀☂️⚡❄️🔥💧🌊

**Activities** (19)<br>
🎃🎄🎆🎈🎉🏆⚽⚾🏀🎾🎳⛳🎣🎿🎯🎮🎰🎭🎨

**Objects** (35)<br>
🛍️👟🥾🎓🎵🎤☎️🔋🔌💻📷🏮📚💰📦📮📍✂️🗑️🔒🔑🛠️🦯🔬💉💊🩺🛗🛏️🪑🚽🛁🧯🛒🪧

**Symbols** (21)<br>
🏧🚰♿🚹🚺🚻🚼⚠️🚸⛔🚫🚭🎦♻️✅❌🆓ℹ️🆕🅿️🆘

</details>

<details>
<summary>M adds 776 emoji</summary>

**Smileys & Emotion** (130)<br>
😃😄😁🤣🙃🫠😗☺️😚😙🥲😛🤪😝🤑🤭🫢🫣🤫🫡🤐🤨😑😶🫥😶‍🌫️😏😒🙄😬😮‍💨🤥🫨😌😔😪🤤🤕🤮🤧🥵🥶🥴😵😵‍💫🤯🤠🥸🤓🧐🫤😟🙁☹️😮😯😲😳🥹😦😧😨😰😥😖😣😓😩😫🥱😤🤬😈👿☠️🤡👹👺👾😺😸😹😻😼😽🙀😿😾🙈🙉🙊💌💘💝💖💗💓💞💕💟❣️❤️‍🔥❤️‍🩹🩷🧡💛💚💙🩵💜🤎🖤🩶🤍💋💢💫💦💨🕳️👁️‍🗨️🗨️🗯️💭🫫🙂‍↔️🙂‍↕️🫩🫪🫯

**Animals & Nature** (114)<br>
🐒🦍🦧🐕🦮🐕‍🦺🐩🐺🦝🐈🐈‍⬛🐅🐆🫎🫏🐎🦄🦓🦬🐂🐃🐄🐖🐽🐏🐑🐐🐪🐫🦙🦣🦏🦛🐭🐁🐀🐹🐇🐿️🦫🦔🦇🐻‍❄️🦥🦦🦨🦘🦡🦃🐔🐓🐣🐤🐥🕊️🦅🦢🦤🪶🦩🦚🦜🪽🐦‍⬛🪿🐊🦎🐍🐲🐉🦕🦖🐋🦭🐠🐡🦈🐙🐚🪸🪼🐌🐛🐜🐝🪲🐞🦗🪳🕷️🕸️🦂🦟🪰🪱🦠💐💮🏵️🌹🥀🌼🪻🪴☘️🍀🍂🍃🪹🪺🐦‍🔥🫍🫌🪾

**Food & Drink** (106)<br>
🍈🍉🍋🍌🍍🥭🍏🍐🍒🫐🥝🍅🫒🥥🥑🍆🥔🥕🌽🌶️🫑🥒🥬🥦🧄🧅🥜🫘🌰🫚🫛🥖🫓🥨🥯🥞🧇🧀🍖🍗🥩🥓🍟🌭🥪🌮🌯🫔🥙🧆🥚🍳🥘🍲🫕🥣🥗🍿🧈🧂🥫🍘🍚🍠🍥🥮🥟🥠🥡🦀🦞🦐🦑🦪🍧🍩🍪🧁🥧🍫🍬🍭🍮🍯🍼🥛🫖🍾🍻🥂🥃🫗🥤🧃🧉🧊🥢🍴🥄🔪🫙🏺🍋‍🟩🫝🍄‍🟫🫜

**Travel & Places** (85)<br>
🌍🌎🌏🌐🏜️🧱🪵🛖🏚️🏩💒🗽🕋🌁🌃🏙️🌄🌆🌇🌉🎠💈🚂🚃🚈🚝🚞🚍🚎🚐🚔🚖🚘🚙🛻🚛🏎️🛵🦽🦼🛺🛴🛹🛼🛣️🛤️🛢️🛞🚨🚥🚤🛥️🛬🪂💺🚟🚡🛰️🚀🛸🛎️🧳🌡️🪐🌟🌠☁️⛈️🌤️🌥️🌦️🌩️🌪️🌫️🌬️🌈🌂☔⛱️☃️⛄☄️🛘🛙🪋

**Activities** (45)<br>
🎇🧨✨🎊🎋🎍🎎🎏🎐🎑🧧🎀🎁🎗️🎟️🎫🎖️🏅🥇🥈🥉🥎🏐🏈🏉🥏🏏🏑🏒🥍🏓🏸🥊🥋🥅⛸️🤿🎽🛷🥌🖼️🧵🪡🧶🪢

**Objects** (161)<br>
🎼🎶🎙️🎚️🎛️🎧📻📱📲📞📟📠🪫🖥️🖨️⌨️🖱️🖲️💽💾💿📀🧮🎥🎞️📽️🎬📺📸📹📼🔍🔎🕯️💡🔦🪔📔📕📖📗📘📙📓📒📃📜📄📰🗞️📑🔖🏷️🪙💴💵💶💷💸💳🧾💹✉️📧📨📩📤📥📫📪📬📭🗳️💼📁📂🗂️📅📆🗒️🗓️📇📈📉📊📋📌📎🖇️📏📐🗃️🗄️🔓🔏🔐🗝️🔨🪓⛏️⚒️🗡️⚔️💣🪃🏹🛡️🪚🔧🪛🔩⚙️🗜️⚖️🔗⛓️🪝🧰🧲🪜⚗️🧪🧫🧬🔭📡🩸🩹🩼🩻🚪🪞🪟🛋️🪠🚿🪤🪒🧴🧷🧹🧺🧻🪣🧼🫧🪥🧽🚬⚰️🪦⚱️🧿🪬🗿🪪🪎🪌🪍⛓️‍💥🪏

**Symbols** (135)<br>
🚮🚾🛂🛃🛄🛅🚳🚯🚱🚷📵🔞☢️☣️⬆️↗️➡️↘️⬇️↙️⬅️↖️↕️↔️↩️↪️⤴️⤵️🔃🔄🔙🔚🔛🔜🔝🛐⚛️🕉️✡️☸️☯️✝️☦️☪️☮️🕎🔯🪯⚕️⚜️🔱📛🔰⭕☑️✔️❎➰➿〽️✳️✴️❇️™️🔠🔡🔢🔣🔤🅰️🆎🅱️🆑🆒🆔Ⓜ️🆖🅾️🆗🆙🆚🈁🈂️🈷️🈶🈯🉐🈹🈚🈲🉑🈸🈴🈳㊗️㊙️🈺🈵🔴🟠🟡🟢🔵🟣🟤⚫⚪🟥🟧🟨🟩🟦🟪🟫⬛⬜◼️◻️◾◽▪️▫️🔶🔷🔸🔹🔺🔻💠🔘🔳🔲©️®️🫟

</details>

<details>
<summary>L adds 847 emoji</summary>

**People & Body** (371)<br>
🤚🖐️✋🖖🫱🫲🫳🫴🫷🫸🤌🤏✌️🤞🫰🤟🤘🤙👈👉👆🖕👇☝️🫵✊👊🤛🤜🫶👐🤲✍️💅🤳🦾🦿🦵🦶👂🦻👃🧠🫀🫁🦷🦴👁️👅👄🫦👦👧👱👨🧔🧔‍♂️🧔‍♀️👨‍🦰👨‍🦱👨‍🦳👨‍🦲👩👩‍🦰🧑‍🦰👩‍🦱🧑‍🦱👩‍🦳🧑‍🦳👩‍🦲🧑‍🦲👱‍♀️👱‍♂️👴👵🙍🙍‍♂️🙍‍♀️🙎🙎‍♂️🙎‍♀️🙅🙅‍♂️🙅‍♀️🙆🙆‍♂️🙆‍♀️💁💁‍♂️💁‍♀️🙋🙋‍♂️🙋‍♀️🧏🧏‍♂️🧏‍♀️🙇🙇‍♂️🙇‍♀️🤦🤦‍♂️🤦‍♀️🤷🤷‍♂️🤷‍♀️🧑‍⚕️👨‍⚕️👩‍⚕️🧑‍🎓👨‍🎓👩‍🎓🧑‍🏫👨‍🏫👩‍🏫🧑‍⚖️👨‍⚖️👩‍⚖️🧑‍🌾👨‍🌾👩‍🌾🧑‍🍳👨‍🍳👩‍🍳🧑‍🔧👨‍🔧👩‍🔧🧑‍🏭👨‍🏭👩‍🏭🧑‍💼👨‍💼👩‍💼🧑‍🔬👨‍🔬👩‍🔬🧑‍💻👨‍💻👩‍💻🧑‍🎤👨‍🎤👩‍🎤🧑‍🎨👨‍🎨👩‍🎨🧑‍✈️👨‍✈️👩‍✈️🧑‍🚀👨‍🚀👩‍🚀🧑‍🚒👨‍🚒👩‍🚒👮👮‍♂️👮‍♀️🕵️🕵️‍♂️🕵️‍♀️💂💂‍♂️💂‍♀️🥷👷👷‍♂️👷‍♀️🫅🤴👸👳👳‍♂️👳‍♀️👲🧕🤵🤵‍♂️🤵‍♀️👰👰‍♂️👰‍♀️🤰🫃🤱👩‍🍼👨‍🍼🧑‍🍼👼🎅🤶🧑‍🎄🦸🦸‍♂️🦸‍♀️🦹🦹‍♂️🦹‍♀️🧙🧙‍♂️🧙‍♀️🧚🧚‍♂️🧚‍♀️🧛🧛‍♂️🧛‍♀️🧜🧜‍♂️🧜‍♀️🧝🧝‍♂️🧝‍♀️🧞🧞‍♂️🧞‍♀️🧟🧟‍♂️🧟‍♀️🧌💆💆‍♂️💆‍♀️💇💇‍♂️💇‍♀️🚶🚶‍♂️🚶‍♀️🧍🧍‍♂️🧍‍♀️🧎🧎‍♂️🧎‍♀️🧑‍🦯👨‍🦯👩‍🦯🧑‍🦼👨‍🦼👩‍🦼🧑‍🦽👨‍🦽👩‍🦽🏃🏃‍♂️🏃‍♀️💃🕺🕴️👯👯‍♂️👯‍♀️🧖🧖‍♂️🧖‍♀️🧗🧗‍♂️🧗‍♀️🤺🏇⛷️🏂🏌️🏌️‍♂️🏌️‍♀️🏄🏄‍♂️🏄‍♀️🚣🚣‍♂️🚣‍♀️🏊🏊‍♂️🏊‍♀️⛹️⛹️‍♂️⛹️‍♀️🏋️🏋️‍♂️🏋️‍♀️🚴🚴‍♂️🚴‍♀️🚵🚵‍♂️🚵‍♀️🤸🤸‍♂️🤸‍♀️🤼🤼‍♂️🤼‍♀️🤽🤽‍♂️🤽‍♀️🤾🤾‍♂️🤾‍♀️🤹🤹‍♂️🤹‍♀️🧘🧘‍♂️🧘‍♀️🛀🛌🧑‍🤝‍🧑👭👫👬💏👩‍❤️‍💋‍👨👨‍❤️‍💋‍👨👩‍❤️‍💋‍👩👩‍❤️‍👨👨‍❤️‍👨👩‍❤️‍👩👨‍👩‍👦👨‍👩‍👧👨‍👩‍👧‍👦👨‍👩‍👦‍👦👨‍👩‍👧‍👧👨‍👨‍👦👨‍👨‍👧👨‍👨‍👧‍👦👨‍👨‍👦‍👦👨‍👨‍👧‍👧👩‍👩‍👦👩‍👩‍👧👩‍👩‍👧‍👦👩‍👩‍👦‍👦👩‍👩‍👧‍👧👨‍👦👨‍👦‍👦👨‍👧👨‍👧‍👦👨‍👧‍👧👩‍👦👩‍👦‍👦👩‍👧👩‍👧‍👦👩‍👧‍👧🗣️👤🫂🫹🫺🫈🚶‍➡️🚶‍♀️‍➡️🚶‍♂️‍➡️🧎‍➡️🧎‍♀️‍➡️🧎‍♂️‍➡️🧑‍🦯‍➡️👨‍🦯‍➡️👩‍🦯‍➡️🧑‍🦼‍➡️👨‍🦼‍➡️👩‍🦼‍➡️🧑‍🦽‍➡️👨‍🦽‍➡️👩‍🦽‍➡️🏃‍➡️🏃‍♀️‍➡️🏃‍♂️‍➡️🧑‍🩰🧑‍🧑‍🧒🧑‍🧑‍🧒‍🧒🧑‍🧒🧑‍🧒‍🧒🫆

**Travel & Places** (45)<br>
⌛⏳⌚⏰⏱️⏲️🕰️🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦🌑🌒🌓🌔🌕🌖🌗🌘🌙🌚🌛🌜🌝🌞

**Activities** (21)<br>
🪀🪁🔫🎱🔮🪄🕹️🎲🧩🧸🪅🪩🪆♠️♥️♦️♣️♟️🃏🀄🎴

**Objects** (72)<br>
👓🕶️🥽🥼🦺👔👕👖🧣🧤🧥🧦👗👘🥻🩱🩲🩳👙👚🪭👛👜👝🎒🩴👞🥿👠👡🩰👢🪮👑👒🎩🧢🪖⛑️📿💄💍💎🔇🔈🔉🔊📢📣📯🔔🔕🎷🪗🎸🎹🎺🎻🪕🥁🪘🪇🪈✏️✒️🖋️🖊️🖌️🖍️📝🪊🪉

**Symbols** (68)<br>
♈♉♊♋♌♍♎♏♐♑♒♓⛎🔀🔁🔂▶️⏩⏭️⏯️◀️⏪⏮️🔼⏫🔽⏬⏸️⏹️⏺️⏏️🔅🔆📶🛜📳📴♀️♂️⚧️✖️➕➖➗🟰♾️‼️⁉️❓❔❕❗〰️💱💲🔟#️⃣*️⃣0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣

**Flags** (270)<br>
🏁🚩🎌🏴🏳️🏳️‍🌈🏳️‍⚧️🏴‍☠️🇦🇨🇦🇩🇦🇪🇦🇫🇦🇬🇦🇮🇦🇱🇦🇲🇦🇴🇦🇶🇦🇷🇦🇸🇦🇹🇦🇺🇦🇼🇦🇽🇦🇿🇧🇦🇧🇧🇧🇩🇧🇪🇧🇫🇧🇬🇧🇭🇧🇮🇧🇯🇧🇱🇧🇲🇧🇳🇧🇴🇧🇶🇧🇷🇧🇸🇧🇹🇧🇻🇧🇼🇧🇾🇧🇿🇨🇦🇨🇨🇨🇩🇨🇫🇨🇬🇨🇭🇨🇮🇨🇰🇨🇱🇨🇲🇨🇳🇨🇴🇨🇵🇨🇶🇨🇷🇨🇺🇨🇻🇨🇼🇨🇽🇨🇾🇨🇿🇩🇪🇩🇬🇩🇯🇩🇰🇩🇲🇩🇴🇩🇿🇪🇦🇪🇨🇪🇪🇪🇬🇪🇭🇪🇷🇪🇸🇪🇹🇪🇺🇫🇮🇫🇯🇫🇰🇫🇲🇫🇴🇫🇷🇬🇦🇬🇧🇬🇩🇬🇪🇬🇫🇬🇬🇬🇭🇬🇮🇬🇱🇬🇲🇬🇳🇬🇵🇬🇶🇬🇷🇬🇸🇬🇹🇬🇺🇬🇼🇬🇾🇭🇰🇭🇲🇭🇳🇭🇷🇭🇹🇭🇺🇮🇨🇮🇩🇮🇪🇮🇱🇮🇲🇮🇳🇮🇴🇮🇶🇮🇷🇮🇸🇮🇹🇯🇪🇯🇲🇯🇴🇯🇵🇰🇪🇰🇬🇰🇭🇰🇮🇰🇲🇰🇳🇰🇵🇰🇷🇰🇼🇰🇾🇰🇿🇱🇦🇱🇧🇱🇨🇱🇮🇱🇰🇱🇷🇱🇸🇱🇹🇱🇺🇱🇻🇱🇾🇲🇦🇲🇨🇲🇩🇲🇪🇲🇫🇲🇬🇲🇭🇲🇰🇲🇱🇲🇲🇲🇳🇲🇴🇲🇵🇲🇶🇲🇷🇲🇸🇲🇹🇲🇺🇲🇻🇲🇼🇲🇽🇲🇾🇲🇿🇳🇦🇳🇨🇳🇪🇳🇫🇳🇬🇳🇮🇳🇱🇳🇴🇳🇵🇳🇷🇳🇺🇳🇿🇴🇲🇵🇦🇵🇪🇵🇫🇵🇬🇵🇭🇵🇰🇵🇱🇵🇲🇵🇳🇵🇷🇵🇸🇵🇹🇵🇼🇵🇾🇶🇦🇷🇪🇷🇴🇷🇸🇷🇺🇷🇼🇸🇦🇸🇧🇸🇨🇸🇩🇸🇪🇸🇬🇸🇭🇸🇮🇸🇯🇸🇰🇸🇱🇸🇲🇸🇳🇸🇴🇸🇷🇸🇸🇸🇹🇸🇻🇸🇽🇸🇾🇸🇿🇹🇦🇹🇨🇹🇩🇹🇫🇹🇬🇹🇭🇹🇯🇹🇰🇹🇱🇹🇲🇹🇳🇹🇴🇹🇷🇹🇹🇹🇻🇹🇼🇹🇿🇺🇦🇺🇬🇺🇲🇺🇳🇺🇸🇺🇾🇺🇿🇻🇦🇻🇨🇻🇪🇻🇬🇻🇮🇻🇳🇻🇺🇼🇫🇼🇸🇽🇰🇾🇪🇾🇹🇿🇦🇿🇲🇿🇼🏴󠁧󠁢󠁥󠁮󠁧󠁿🏴󠁧󠁢󠁳󠁣󠁴󠁿🏴󠁧󠁢󠁷󠁬󠁳󠁿

</details>
<!-- sets:en end -->

- To choose a set, put `SET='M';` in front of the line. The console runs one
  line at a time, so keep it on one line.

  ```python
  SET='M'; import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/install.py').read())
  ```

- Run the line again with another `SET` to switch. A bigger set adds emoji.
  A smaller set deletes the emoji it does not have, and markers that used
  them show `?` until you go back to the bigger set. If another profile uses
  the same folder, QGIS keeps the shared set and reports the conflict.
- Without `SET`, an update keeps the set you selected. If an update moves an
  emoji out of your set, its installed SVG stays so existing projects still
  open.
- If QGIS closes during an update, run the install line again to recover the
  previous files before applying an update.

## Sharing a project

A marker stores where the SVG file is on your computer. On a computer
without EmOji-san it shows `?`. Before you pass a project on, do one of
these:

- In the settings of the SVG marker, click **…** next to the file name and
  choose **Embed File…**.
- Use the symbols from the style file in the next section. Their SVG is
  already inside.
- Put `EMBED=True;` in front of the install line to enable embedding in
  the current QGIS profile. When you save, QGIS embeds EmOji-san SVG files
  selected directly in markers, fills and label backgrounds. SVG file paths
  chosen by an expression or field stay external, even if the fixed fallback
  is embedded. Make those files available to the recipient. Pictures in print
  layouts are outside this feature. QGIS reads the profile's setting at startup
  through a marked block in `startup.py`. `EMBED=False;` turns embedding off
  in that profile.

## The S set as symbols

`emoji_san_core.xml` on the [Releases](../../releases) page is a style file
with the S set as marker symbols. The SVG is inside each symbol, so it works
without the installer.

1. Download the file.
2. **Settings → Style Manager → Import / Export → Import Item(s)…**, choose
   the file, then **Select All** and **Import**.
3. QGIS asks whether to overwrite a symbol, even the first time: after
   **Select All** it takes each symbol twice. Answer **No to All**.

The symbols are tagged `EmOji-san`.

To replace symbols from an older `emoji_san_core.xml`, delete them in the
Style Manager first; the tag finds them. Overwriting them on import does
not last: after a restart, QGIS has the old symbols again.

## Check and uninstall

Check the install. The last line it prints should start with
`Result: ALL GOOD`. It also adds a temporary layer, "EmOji-san catalog",
with every installed emoji and its name, grouped by category and fitted
into the view of the map; `DEMO=False;` in front leaves that out.

```python
import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/check_install.py').read())
```

Uninstall. It unregisters EmOji-san and turns off embedding in the current
profile. Installed files stay while another profile uses the folder. Files
you put there are kept, along with the SVG path if those are the only files
left. Once no profile uses the folder, EmOji-san's lines also leave
`startup.py`; your own lines there stay. Symbols imported from the style
file stay in the Style Manager, where you can delete them.

```python
import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/uninstall.py').read())
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
  import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/diagnose.py').read())
  ```

## QGIS 3 and QGIS 4

With the standard settings paths, QGIS 3 and QGIS 4 have separate folders.
When QGIS 4 inherits a profile that still uses the standard QGIS 3 copy,
run the install line in QGIS 4 to carry over its SVGs. If QGIS 4 already has
a set, an update without `SET` keeps the larger of the two sets. The old
path stays registered if it also contains files that EmOji-san does not manage.

## Without internet access from QGIS

If the install line ends in a network error, use a browser to download
`install.py` and `emoji_san_data.zip` from the Assets of the same
[release](../../releases). Run this line with the paths of those two files.
On Windows, use paths like `r'C:\Downloads\install.py'`.

```python
from pathlib import Path; ZIP='/path/to/emoji_san_data.zip'; LOCALE='en'; exec(Path('/path/to/install.py').read_bytes())
```

Keep `emoji_san_data.zip` exactly as downloaded so it passes the SHA-256
check. If Safari opens it automatically, turn off **Open “safe” files after
downloading** in **Safari → Settings → General** and download it again.

You can also download **Source code (zip)** from that release and run its
installer with the line below. Use the source ZIP from EmOji-san because the
line runs Python from inside it. The line finds `install.py` at the ZIP root
or inside one top-level folder, whatever that folder is called. If Safari
unpacks the source ZIP, compress that folder again and use the result.

```python
ZIP='/path/to/emoji-san-1.1.0.zip'; LOCALE='en'; exec("from zipfile import ZipFile\nwith ZipFile(console['ZIP']) as archive:\n    names = [n for n in archive.namelist() if n.count('/') <= 1 and n.rsplit('/', 1)[-1] == 'install.py' and not n.startswith(('/', './', '../'))]\n    if len(names) != 1: raise ValueError('Expected one install.py at the ZIP root or inside one folder')\n    code = archive.read(names[0])\nexec(code, console)", {'console': globals()})
```

Both lines use English names in `index.csv` and install without connecting
to the internet. To add names in your QGIS display language later, run the
online install line again when you have a connection.

## What is installed

- `EmOji-san/<Category>/<name>.svg` in the QGIS settings folder, the one
  that holds `profiles`. On Windows that is
  `%APPDATA%\QGIS\QGIS3`, on macOS
  `~/Library/Application Support/QGIS/QGIS3`, on Linux
  `~/.local/share/QGIS/QGIS3` (`QGIS4` for QGIS 4).
- User profiles under the same settings folder share the SVG files. Each
  profile registers the folder separately. To use the installed set in
  another profile, run the install line there too.
- The file names are the English emoji names, like `convenience_store.svg`.
  The search box of the SVG browser finds them.
- `index.csv` in the same folder lists the current set: the emoji, its code
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
  and sorts them into folders. Some files are rewritten, because QGIS would
  draw them wrong as they are: the hands, for one, come out black. The
  picture is the same, and the other files are unchanged. Details are in
  `NOTICE`.
- Country and subdivision flags: Noto Emoji's waved flags
  (`third_party/region-flags`), whose designs are in the public domain or
  otherwise exempt from copyright. Their license is at the end of
  `LICENSE-noto-emoji.txt`.
- File names, English names and categories: [gemoji](https://github.com/github/gemoji),
  MIT License. The license text is in `LICENSE-gemoji.txt`.
- Scripts: MIT.
- The online lines run Python from a published release. GitHub locks the
  attached files of each immutable release, and its installer checks the SHA-256 of
  `emoji_san_data.zip` before using it. You can download and read each script
  from the release's Assets page before running it.

## Maintenance

Once a year, when Noto Emoji has the new emoji:

1. `python3 build/update_from_upstream.py` matches Noto against the pinned
   Unicode emoji list and validates the SVGs, index and style file before
   replacing them. It needs picosvg (`python3 -m pip install picosvg`). Use
   `--unicode-version` to choose a Unicode release. The build lists new emoji,
   eligible emoji missing from Noto, and old SVGs kept for compatibility.
   Published paths stay the same. Check the new drawings in QGIS. To change
   the S set, edit `core_list.txt` and run `python3 build/make_core.py`;
   to keep something of the map collection out of M, add it to
   `l_only_list.txt` the same way.
2. Change the version in `TAG` in `install.py` and everywhere in this
   README (search for the old number), and correct the numbers in the Sets
   table. Set `CLDR` in `install.py` to the latest release of
   [cldr-json](https://github.com/unicode-org/cldr-json); the names of new
   emoji in other languages come from there.
3. Run `python3 -m unittest discover -s tests` to check the rebuild and release
   assets. Run `python3 tests/scenarios.py --online` to check the installer
   in an isolated QGIS profile, including updates of existing projects and
   names from CLDR. The second command needs a Python that can import
   `qgis`. The script shows how to run it in Docker.
4. Enable [release immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)
   in the repository settings before publishing. Commit, tag and push.
   From a clean checkout of the tagged commit, build the assets and attach
   all six files to a draft release.

   ```bash
   python3 build/make_release.py ../emoji-san-v1.1.0-release
   gh release create v1.1.0 ../emoji-san-v1.1.0-release/* --verify-tag --draft --title "EmOji-san v1.1.0" --notes "Noto Emoji as of 2027"
   ```

5. Check the draft's asset list, then publish it. Once the repository and
   release are public, verify the release is immutable and the README's
   download links work while signed out of GitHub.

---

# 日本語

QGISで、カラーの絵文字をポイントのマーカーに使えるようにします: 🏪 🚌 🏥 ♨️

<img width="432" height="227" alt="image" src="https://github.com/user-attachments/assets/c3a51cfe-4dd8-4339-8f35-9e936d36959d" />

絵文字はGoogleのNoto EmojiのSVGです。QGISのPythonコンソールに1行貼るとインストールされます。プラグインではありません。

名前はEmojiと「おじさん」から付けました。インストールが終わると、おじさんがひとこと挨拶します。

QGIS 3.34、3.44、4.4で動作を確認しています。

## インストール

1. QGISで **プラグイン → Pythonコンソール** を開きます。
2. 次の1行を貼り付けてEnterを押します。

   ```python
   import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/install.py').read())
   ```

3. コンソールに次のように表示されます。フォルダの場所は環境によって違います。

   ```
   EmOji-san: getting https://github.com/yfuru2454/emoji-san/releases/download/v1.1.0/emoji_san_data.zip
   EmOji-san👨‍💼参上❗ 300個の絵文字をお届けしたヨ😃✨ 地図がにぎやかになるネ🗾💕
   EmOji-san S: 300 emoji (+300 added, -0 removed) -> /Users/you/Library/Application Support/QGIS/QGIS3/EmOji-san
     index.csv (+ name_ja)
     registered as an SVG path (Settings > Options > System)
   Next: Symbology of a point layer > SVG Marker > SVG browser > EmOji-san > a category. Reopen the dialog if it was open.
   More emoji: SET='M'; in front of the same line (S 300, M 1,076, L 1,923).
   Sharing a project: embed the SVG in the symbol ("..." > Embed File), or run this again with EMBED=True; in front.
   ```

4. ポイントレイヤの **シンボロジ** を開き、シンボルレイヤの種類を **SVGマーカー** にします。**SVGブラウザ** の **EmOji-san** の下に、カテゴリごとのフォルダで並んでいます。

この1行は、いつも最新のリリースを入れます。特定の版を入れたいときは、`latest/download/`を`download/v1.1.0/`に書き換えてください。

## セット

| セット | 個数 | 中身 |
|---|---|---|
| `S` | 300 | マーカーの大きさでも見分けやすいもの。何も指定しなければこれが入ります |
| `M` | 1,076 | Sと、顔の全部と、Activities、Animals and Nature、Food and Drink、Objects、Symbols、Travel and Placesの残り。ただし時計、星座、再生ボタン、服、ゲーム、楽器など地図で使わないもの（`l_only_list.txt`）は除きます |
| `L` | 1,923 | Mと、残り全部（人物・手と、国旗・地域旗を含むすべての旗） |

どのセットにも、肌の色違いは入っていません。

<!-- sets:ja begin: build/make_core.pyがindex.csvから書き込みます -->
<details>
<summary>S：300個の絵文字</summary>

**Smileys & Emotion** (42)<br>
😀😆😅😂🙂😉😊😇🥰😍🤩😘😋😜🤗🤔😐😴😷🤒🤢🥳😎😕🥺😢😭😱😞😡😠💀💩👻👽🤖💔❤️💯💥💬💤

**People & Body** (19)<br>
👋👌👍👎👏🙌🤝🙏💪👀👶🧒🧑🧓🫄💑👪👥👣

**Animals & Nature** (42)<br>
🐵🐶🦊🐱🦁🐯🐴🦌🐮🐷🐗🦒🐘🐰🐻🐨🐼🐾🐦🐧🦆🦉🐸🐢🐳🐬🐟🦋🌸🪷🌺🌻🌷🌱🌲🌳🌴🌵🌾🌿🍁🍄

**Food & Drink** (31)<br>
🍇🍊🍎🍑🍓🍞🥐🍔🍕🍱🍙🍛🍜🍝🍢🍣🍤🍡🍦🍨🎂🍰☕🍵🍶🍷🍸🍹🍺🧋🍽️

**Travel & Places** (91)<br>
🗺️🗾🧭🏔️⛰️🌋🗻🏕️🏖️🏝️🏞️🏟️🏛️🏗️🪨🏘️🏠🏡🏢🏣🏤🏥🏦🏨🏪🏫🏬🏭🏯🏰🗼⛪🕌🛕🕍⛩️⛲⛺🌅♨️🛝🎡🎢🎪🚄🚅🚆🚇🚉🚊🚋🚌🚑🚒🚓🚕🚗🚚🚜🏍️🚲🚏⛽🚦🛑🚧⚓🛟⛵🛶🛳️⛴️🚢✈️🛩️🛫🚁🚠☀️⭐🌌⛅🌧️🌨️🌀☂️⚡❄️🔥💧🌊

**Activities** (19)<br>
🎃🎄🎆🎈🎉🏆⚽⚾🏀🎾🎳⛳🎣🎿🎯🎮🎰🎭🎨

**Objects** (35)<br>
🛍️👟🥾🎓🎵🎤☎️🔋🔌💻📷🏮📚💰📦📮📍✂️🗑️🔒🔑🛠️🦯🔬💉💊🩺🛗🛏️🪑🚽🛁🧯🛒🪧

**Symbols** (21)<br>
🏧🚰♿🚹🚺🚻🚼⚠️🚸⛔🚫🚭🎦♻️✅❌🆓ℹ️🆕🅿️🆘

</details>

<details>
<summary>Mで増える776個</summary>

**Smileys & Emotion** (130)<br>
😃😄😁🤣🙃🫠😗☺️😚😙🥲😛🤪😝🤑🤭🫢🫣🤫🫡🤐🤨😑😶🫥😶‍🌫️😏😒🙄😬😮‍💨🤥🫨😌😔😪🤤🤕🤮🤧🥵🥶🥴😵😵‍💫🤯🤠🥸🤓🧐🫤😟🙁☹️😮😯😲😳🥹😦😧😨😰😥😖😣😓😩😫🥱😤🤬😈👿☠️🤡👹👺👾😺😸😹😻😼😽🙀😿😾🙈🙉🙊💌💘💝💖💗💓💞💕💟❣️❤️‍🔥❤️‍🩹🩷🧡💛💚💙🩵💜🤎🖤🩶🤍💋💢💫💦💨🕳️👁️‍🗨️🗨️🗯️💭🫫🙂‍↔️🙂‍↕️🫩🫪🫯

**Animals & Nature** (114)<br>
🐒🦍🦧🐕🦮🐕‍🦺🐩🐺🦝🐈🐈‍⬛🐅🐆🫎🫏🐎🦄🦓🦬🐂🐃🐄🐖🐽🐏🐑🐐🐪🐫🦙🦣🦏🦛🐭🐁🐀🐹🐇🐿️🦫🦔🦇🐻‍❄️🦥🦦🦨🦘🦡🦃🐔🐓🐣🐤🐥🕊️🦅🦢🦤🪶🦩🦚🦜🪽🐦‍⬛🪿🐊🦎🐍🐲🐉🦕🦖🐋🦭🐠🐡🦈🐙🐚🪸🪼🐌🐛🐜🐝🪲🐞🦗🪳🕷️🕸️🦂🦟🪰🪱🦠💐💮🏵️🌹🥀🌼🪻🪴☘️🍀🍂🍃🪹🪺🐦‍🔥🫍🫌🪾

**Food & Drink** (106)<br>
🍈🍉🍋🍌🍍🥭🍏🍐🍒🫐🥝🍅🫒🥥🥑🍆🥔🥕🌽🌶️🫑🥒🥬🥦🧄🧅🥜🫘🌰🫚🫛🥖🫓🥨🥯🥞🧇🧀🍖🍗🥩🥓🍟🌭🥪🌮🌯🫔🥙🧆🥚🍳🥘🍲🫕🥣🥗🍿🧈🧂🥫🍘🍚🍠🍥🥮🥟🥠🥡🦀🦞🦐🦑🦪🍧🍩🍪🧁🥧🍫🍬🍭🍮🍯🍼🥛🫖🍾🍻🥂🥃🫗🥤🧃🧉🧊🥢🍴🥄🔪🫙🏺🍋‍🟩🫝🍄‍🟫🫜

**Travel & Places** (85)<br>
🌍🌎🌏🌐🏜️🧱🪵🛖🏚️🏩💒🗽🕋🌁🌃🏙️🌄🌆🌇🌉🎠💈🚂🚃🚈🚝🚞🚍🚎🚐🚔🚖🚘🚙🛻🚛🏎️🛵🦽🦼🛺🛴🛹🛼🛣️🛤️🛢️🛞🚨🚥🚤🛥️🛬🪂💺🚟🚡🛰️🚀🛸🛎️🧳🌡️🪐🌟🌠☁️⛈️🌤️🌥️🌦️🌩️🌪️🌫️🌬️🌈🌂☔⛱️☃️⛄☄️🛘🛙🪋

**Activities** (45)<br>
🎇🧨✨🎊🎋🎍🎎🎏🎐🎑🧧🎀🎁🎗️🎟️🎫🎖️🏅🥇🥈🥉🥎🏐🏈🏉🥏🏏🏑🏒🥍🏓🏸🥊🥋🥅⛸️🤿🎽🛷🥌🖼️🧵🪡🧶🪢

**Objects** (161)<br>
🎼🎶🎙️🎚️🎛️🎧📻📱📲📞📟📠🪫🖥️🖨️⌨️🖱️🖲️💽💾💿📀🧮🎥🎞️📽️🎬📺📸📹📼🔍🔎🕯️💡🔦🪔📔📕📖📗📘📙📓📒📃📜📄📰🗞️📑🔖🏷️🪙💴💵💶💷💸💳🧾💹✉️📧📨📩📤📥📫📪📬📭🗳️💼📁📂🗂️📅📆🗒️🗓️📇📈📉📊📋📌📎🖇️📏📐🗃️🗄️🔓🔏🔐🗝️🔨🪓⛏️⚒️🗡️⚔️💣🪃🏹🛡️🪚🔧🪛🔩⚙️🗜️⚖️🔗⛓️🪝🧰🧲🪜⚗️🧪🧫🧬🔭📡🩸🩹🩼🩻🚪🪞🪟🛋️🪠🚿🪤🪒🧴🧷🧹🧺🧻🪣🧼🫧🪥🧽🚬⚰️🪦⚱️🧿🪬🗿🪪🪎🪌🪍⛓️‍💥🪏

**Symbols** (135)<br>
🚮🚾🛂🛃🛄🛅🚳🚯🚱🚷📵🔞☢️☣️⬆️↗️➡️↘️⬇️↙️⬅️↖️↕️↔️↩️↪️⤴️⤵️🔃🔄🔙🔚🔛🔜🔝🛐⚛️🕉️✡️☸️☯️✝️☦️☪️☮️🕎🔯🪯⚕️⚜️🔱📛🔰⭕☑️✔️❎➰➿〽️✳️✴️❇️™️🔠🔡🔢🔣🔤🅰️🆎🅱️🆑🆒🆔Ⓜ️🆖🅾️🆗🆙🆚🈁🈂️🈷️🈶🈯🉐🈹🈚🈲🉑🈸🈴🈳㊗️㊙️🈺🈵🔴🟠🟡🟢🔵🟣🟤⚫⚪🟥🟧🟨🟩🟦🟪🟫⬛⬜◼️◻️◾◽▪️▫️🔶🔷🔸🔹🔺🔻💠🔘🔳🔲©️®️🫟

</details>

<details>
<summary>Lで増える847個</summary>

**People & Body** (371)<br>
🤚🖐️✋🖖🫱🫲🫳🫴🫷🫸🤌🤏✌️🤞🫰🤟🤘🤙👈👉👆🖕👇☝️🫵✊👊🤛🤜🫶👐🤲✍️💅🤳🦾🦿🦵🦶👂🦻👃🧠🫀🫁🦷🦴👁️👅👄🫦👦👧👱👨🧔🧔‍♂️🧔‍♀️👨‍🦰👨‍🦱👨‍🦳👨‍🦲👩👩‍🦰🧑‍🦰👩‍🦱🧑‍🦱👩‍🦳🧑‍🦳👩‍🦲🧑‍🦲👱‍♀️👱‍♂️👴👵🙍🙍‍♂️🙍‍♀️🙎🙎‍♂️🙎‍♀️🙅🙅‍♂️🙅‍♀️🙆🙆‍♂️🙆‍♀️💁💁‍♂️💁‍♀️🙋🙋‍♂️🙋‍♀️🧏🧏‍♂️🧏‍♀️🙇🙇‍♂️🙇‍♀️🤦🤦‍♂️🤦‍♀️🤷🤷‍♂️🤷‍♀️🧑‍⚕️👨‍⚕️👩‍⚕️🧑‍🎓👨‍🎓👩‍🎓🧑‍🏫👨‍🏫👩‍🏫🧑‍⚖️👨‍⚖️👩‍⚖️🧑‍🌾👨‍🌾👩‍🌾🧑‍🍳👨‍🍳👩‍🍳🧑‍🔧👨‍🔧👩‍🔧🧑‍🏭👨‍🏭👩‍🏭🧑‍💼👨‍💼👩‍💼🧑‍🔬👨‍🔬👩‍🔬🧑‍💻👨‍💻👩‍💻🧑‍🎤👨‍🎤👩‍🎤🧑‍🎨👨‍🎨👩‍🎨🧑‍✈️👨‍✈️👩‍✈️🧑‍🚀👨‍🚀👩‍🚀🧑‍🚒👨‍🚒👩‍🚒👮👮‍♂️👮‍♀️🕵️🕵️‍♂️🕵️‍♀️💂💂‍♂️💂‍♀️🥷👷👷‍♂️👷‍♀️🫅🤴👸👳👳‍♂️👳‍♀️👲🧕🤵🤵‍♂️🤵‍♀️👰👰‍♂️👰‍♀️🤰🫃🤱👩‍🍼👨‍🍼🧑‍🍼👼🎅🤶🧑‍🎄🦸🦸‍♂️🦸‍♀️🦹🦹‍♂️🦹‍♀️🧙🧙‍♂️🧙‍♀️🧚🧚‍♂️🧚‍♀️🧛🧛‍♂️🧛‍♀️🧜🧜‍♂️🧜‍♀️🧝🧝‍♂️🧝‍♀️🧞🧞‍♂️🧞‍♀️🧟🧟‍♂️🧟‍♀️🧌💆💆‍♂️💆‍♀️💇💇‍♂️💇‍♀️🚶🚶‍♂️🚶‍♀️🧍🧍‍♂️🧍‍♀️🧎🧎‍♂️🧎‍♀️🧑‍🦯👨‍🦯👩‍🦯🧑‍🦼👨‍🦼👩‍🦼🧑‍🦽👨‍🦽👩‍🦽🏃🏃‍♂️🏃‍♀️💃🕺🕴️👯👯‍♂️👯‍♀️🧖🧖‍♂️🧖‍♀️🧗🧗‍♂️🧗‍♀️🤺🏇⛷️🏂🏌️🏌️‍♂️🏌️‍♀️🏄🏄‍♂️🏄‍♀️🚣🚣‍♂️🚣‍♀️🏊🏊‍♂️🏊‍♀️⛹️⛹️‍♂️⛹️‍♀️🏋️🏋️‍♂️🏋️‍♀️🚴🚴‍♂️🚴‍♀️🚵🚵‍♂️🚵‍♀️🤸🤸‍♂️🤸‍♀️🤼🤼‍♂️🤼‍♀️🤽🤽‍♂️🤽‍♀️🤾🤾‍♂️🤾‍♀️🤹🤹‍♂️🤹‍♀️🧘🧘‍♂️🧘‍♀️🛀🛌🧑‍🤝‍🧑👭👫👬💏👩‍❤️‍💋‍👨👨‍❤️‍💋‍👨👩‍❤️‍💋‍👩👩‍❤️‍👨👨‍❤️‍👨👩‍❤️‍👩👨‍👩‍👦👨‍👩‍👧👨‍👩‍👧‍👦👨‍👩‍👦‍👦👨‍👩‍👧‍👧👨‍👨‍👦👨‍👨‍👧👨‍👨‍👧‍👦👨‍👨‍👦‍👦👨‍👨‍👧‍👧👩‍👩‍👦👩‍👩‍👧👩‍👩‍👧‍👦👩‍👩‍👦‍👦👩‍👩‍👧‍👧👨‍👦👨‍👦‍👦👨‍👧👨‍👧‍👦👨‍👧‍👧👩‍👦👩‍👦‍👦👩‍👧👩‍👧‍👦👩‍👧‍👧🗣️👤🫂🫹🫺🫈🚶‍➡️🚶‍♀️‍➡️🚶‍♂️‍➡️🧎‍➡️🧎‍♀️‍➡️🧎‍♂️‍➡️🧑‍🦯‍➡️👨‍🦯‍➡️👩‍🦯‍➡️🧑‍🦼‍➡️👨‍🦼‍➡️👩‍🦼‍➡️🧑‍🦽‍➡️👨‍🦽‍➡️👩‍🦽‍➡️🏃‍➡️🏃‍♀️‍➡️🏃‍♂️‍➡️🧑‍🩰🧑‍🧑‍🧒🧑‍🧑‍🧒‍🧒🧑‍🧒🧑‍🧒‍🧒🫆

**Travel & Places** (45)<br>
⌛⏳⌚⏰⏱️⏲️🕰️🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦🌑🌒🌓🌔🌕🌖🌗🌘🌙🌚🌛🌜🌝🌞

**Activities** (21)<br>
🪀🪁🔫🎱🔮🪄🕹️🎲🧩🧸🪅🪩🪆♠️♥️♦️♣️♟️🃏🀄🎴

**Objects** (72)<br>
👓🕶️🥽🥼🦺👔👕👖🧣🧤🧥🧦👗👘🥻🩱🩲🩳👙👚🪭👛👜👝🎒🩴👞🥿👠👡🩰👢🪮👑👒🎩🧢🪖⛑️📿💄💍💎🔇🔈🔉🔊📢📣📯🔔🔕🎷🪗🎸🎹🎺🎻🪕🥁🪘🪇🪈✏️✒️🖋️🖊️🖌️🖍️📝🪊🪉

**Symbols** (68)<br>
♈♉♊♋♌♍♎♏♐♑♒♓⛎🔀🔁🔂▶️⏩⏭️⏯️◀️⏪⏮️🔼⏫🔽⏬⏸️⏹️⏺️⏏️🔅🔆📶🛜📳📴♀️♂️⚧️✖️➕➖➗🟰♾️‼️⁉️❓❔❕❗〰️💱💲🔟#️⃣*️⃣0️⃣1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣8️⃣9️⃣

**Flags** (270)<br>
🏁🚩🎌🏴🏳️🏳️‍🌈🏳️‍⚧️🏴‍☠️🇦🇨🇦🇩🇦🇪🇦🇫🇦🇬🇦🇮🇦🇱🇦🇲🇦🇴🇦🇶🇦🇷🇦🇸🇦🇹🇦🇺🇦🇼🇦🇽🇦🇿🇧🇦🇧🇧🇧🇩🇧🇪🇧🇫🇧🇬🇧🇭🇧🇮🇧🇯🇧🇱🇧🇲🇧🇳🇧🇴🇧🇶🇧🇷🇧🇸🇧🇹🇧🇻🇧🇼🇧🇾🇧🇿🇨🇦🇨🇨🇨🇩🇨🇫🇨🇬🇨🇭🇨🇮🇨🇰🇨🇱🇨🇲🇨🇳🇨🇴🇨🇵🇨🇶🇨🇷🇨🇺🇨🇻🇨🇼🇨🇽🇨🇾🇨🇿🇩🇪🇩🇬🇩🇯🇩🇰🇩🇲🇩🇴🇩🇿🇪🇦🇪🇨🇪🇪🇪🇬🇪🇭🇪🇷🇪🇸🇪🇹🇪🇺🇫🇮🇫🇯🇫🇰🇫🇲🇫🇴🇫🇷🇬🇦🇬🇧🇬🇩🇬🇪🇬🇫🇬🇬🇬🇭🇬🇮🇬🇱🇬🇲🇬🇳🇬🇵🇬🇶🇬🇷🇬🇸🇬🇹🇬🇺🇬🇼🇬🇾🇭🇰🇭🇲🇭🇳🇭🇷🇭🇹🇭🇺🇮🇨🇮🇩🇮🇪🇮🇱🇮🇲🇮🇳🇮🇴🇮🇶🇮🇷🇮🇸🇮🇹🇯🇪🇯🇲🇯🇴🇯🇵🇰🇪🇰🇬🇰🇭🇰🇮🇰🇲🇰🇳🇰🇵🇰🇷🇰🇼🇰🇾🇰🇿🇱🇦🇱🇧🇱🇨🇱🇮🇱🇰🇱🇷🇱🇸🇱🇹🇱🇺🇱🇻🇱🇾🇲🇦🇲🇨🇲🇩🇲🇪🇲🇫🇲🇬🇲🇭🇲🇰🇲🇱🇲🇲🇲🇳🇲🇴🇲🇵🇲🇶🇲🇷🇲🇸🇲🇹🇲🇺🇲🇻🇲🇼🇲🇽🇲🇾🇲🇿🇳🇦🇳🇨🇳🇪🇳🇫🇳🇬🇳🇮🇳🇱🇳🇴🇳🇵🇳🇷🇳🇺🇳🇿🇴🇲🇵🇦🇵🇪🇵🇫🇵🇬🇵🇭🇵🇰🇵🇱🇵🇲🇵🇳🇵🇷🇵🇸🇵🇹🇵🇼🇵🇾🇶🇦🇷🇪🇷🇴🇷🇸🇷🇺🇷🇼🇸🇦🇸🇧🇸🇨🇸🇩🇸🇪🇸🇬🇸🇭🇸🇮🇸🇯🇸🇰🇸🇱🇸🇲🇸🇳🇸🇴🇸🇷🇸🇸🇸🇹🇸🇻🇸🇽🇸🇾🇸🇿🇹🇦🇹🇨🇹🇩🇹🇫🇹🇬🇹🇭🇹🇯🇹🇰🇹🇱🇹🇲🇹🇳🇹🇴🇹🇷🇹🇹🇹🇻🇹🇼🇹🇿🇺🇦🇺🇬🇺🇲🇺🇳🇺🇸🇺🇾🇺🇿🇻🇦🇻🇨🇻🇪🇻🇬🇻🇮🇻🇳🇻🇺🇼🇫🇼🇸🇽🇰🇾🇪🇾🇹🇿🇦🇿🇲🇿🇼🏴󠁧󠁢󠁥󠁮󠁧󠁿🏴󠁧󠁢󠁳󠁣󠁴󠁿🏴󠁧󠁢󠁷󠁬󠁳󠁿

</details>
<!-- sets:ja end -->

- セットを選ぶには、行の先頭に`SET='M';`を付けます。コンソールは1行ずつ実行するので、1行のまま貼ってください。

  ```python
  SET='M'; import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/install.py').read())
  ```

- 別の`SET`を付けて実行し直すと、セットが切り替わります。大きくすると絵文字が増えます。小さくすると、そのセットにない絵文字は削除され、それを使っていたマーカーは大きいセットに戻すまで`?`になります。別のプロファイルが同じフォルダを使っている場合は、共用のセットが維持され、その理由が表示されます。
- `SET`を付けずに更新すると、選んでいたセットを維持します。更新でセットから外れた絵文字も、既存のプロジェクトで使えるよう、インストール済みのSVGを残します。
- 更新中にQGISが終了した場合は、インストールの行をもう一度実行してください。以前のファイルを復旧してから更新を適用します。

## プロジェクトを人に渡すとき

マーカーには、自分のPCにあるSVGファイルの場所が記録されています。EmOji-sanを入れていないPCで開くと`?`になります。渡す前に、次のどれかをしておきます。

- SVGマーカーの設定で、ファイル名の右の **…** から **ファイルを埋め込む...** を選びます。
- 次の節のスタイルファイルのシンボルを使います。SVGが最初から入っています。
- インストールの行の先頭に`EMBED=True;`を付けると、現在のQGISプロファイルで埋め込みが有効になります。保存時に、マーカー、塗りつぶし、ラベルの背景に直接指定したEmOji-sanのSVGが埋め込まれます。式やフィールドでファイルパスを指定したSVGは、固定の既定値が埋め込まれても外部ファイルへの参照のままです。受け渡し先でも、それらのSVGを使えるようにしてください。印刷レイアウトの画像は対象外です。QGISは起動時に`startup.py`の目印付きの処理から、現在のプロファイルの設定を読みます。`EMBED=False;`でそのプロファイルの埋め込みを無効にします。

## Sのセットをシンボルとして使う

[Releases](../../releases)にある`emoji_san_core.xml`は、Sのセットをマーカーシンボルにしたスタイルファイルです。SVGがシンボルの中に入っているので、インストールしなくても使えます。

1. ファイルをダウンロードします。
2. **設定 → スタイルマネージャ → インポートとエクスポート → アイテムのインポート...** でファイルを選び、**すべて選択**、**インポート** の順に押します。
3. シンボルを上書きするか聞かれます。初めてのインポートでも聞かれます（**すべて選択** のあと、QGISは各シンボルを2回ずつ取り込むためです）。**全ていいえ**（No to All）を選びます。

シンボルには`EmOji-san`というタグが付きます。

以前の`emoji_san_core.xml`から入れたシンボルを新しいものに替えるときは、先にスタイルマネージャで古いシンボルを削除します（タグで絞り込めます）。インポート時の上書きは、QGISを再起動すると元のシンボルに戻ります。

## 確認とアンインストール

インストールの確認です。最後の行が`Result: ALL GOOD`で始まっていれば問題ありません。入っている絵文字をすべて、カテゴリごとに名前付きで並べた一時レイヤ「EmOji-san catalog」も、いまの表示範囲に追加されます。先頭に`DEMO=False;`を付けると追加されません。

```python
import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/check_install.py').read())
```

アンインストールです。現在のプロファイルの登録を外し、埋め込みを無効にします。別のプロファイルが同じフォルダを使っている間は、インストールしたファイルが残ります。自分で置いたファイルは残り、それらだけが残った場合はSVGパスの登録も維持されます。どのプロファイルもフォルダを使わなくなると、`startup.py`からEmOji-sanの行も消えます。自分で書いた行は残ります。スタイルファイルからインポートしたシンボルはスタイルマネージャから削除できます。

```python
import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/uninstall.py').read())
```

## SVGブラウザが遅いとき

SVGブラウザは開くたびに、**設定 → オプション → システム → SVGパス** にあるすべてのフォルダのSVGを一覧にします。

- 使っていないフォルダを一覧から外します。以前に登録したNoto Emoji全部入りのフォルダ（3,000個以上）や、ネットワークドライブ上のフォルダが原因になっていることが多いです。
- **EmOji-san** フォルダそのものではなく、カテゴリをクリックします。
- 次の行は、どこで時間がかかっているかを測って、`LIKELY CAUSES`として表示します。

  ```python
  import urllib.request as u; exec(u.urlopen('https://github.com/yfuru2454/emoji-san/releases/latest/download/diagnose.py').read())
  ```

## QGIS 3とQGIS 4

標準の設定パスでは、QGIS 3とQGIS 4の設定フォルダは別です。QGIS 4に引き継いだプロファイルがQGIS 3の標準フォルダを参照している場合は、QGIS 4でインストールの行を実行してSVGを引き継げます。QGIS 4側にセットがある場合、`SET`を省略した更新では2つのうち大きいセットを維持します。旧フォルダにEmOji-sanの管理外のファイルがあれば、旧パスの登録も残ります。

## QGISからインターネットに出られないとき

インストールの行がネットワークのエラーで終わるときは、ブラウザで同じ[リリース](../../releases)のAssetsから`install.py`と`emoji_san_data.zip`をダウンロードします。次の行に両方のファイルの場所を書き、実行します。Windowsでは`r'C:\Downloads\install.py'`のように書きます。

```python
from pathlib import Path; ZIP='/path/to/emoji_san_data.zip'; LOCALE='en'; exec(Path('/path/to/install.py').read_bytes())
```

SHA-256を照合するため、`emoji_san_data.zip`はダウンロードしたまま使います。Safariが自動で開く場合は、**Safari → 設定 → 一般** の **ダウンロード後、“安全な”ファイルを開く** をオフにして、再ダウンロードしてください。

同じリリースの **Source code (zip)** をダウンロードし、次の行でインストールする方法もあります。ZIP内のPythonコードを実行するため、EmOji-sanのリリースから取得したソースZIPを使ってください。ZIPの直下か、その一つ下のフォルダから`install.py`を探します。フォルダ名は変わっていても構いません。Safariで展開された場合は、そのフォルダを圧縮し直して使えます。

```python
ZIP='/path/to/emoji-san-1.1.0.zip'; LOCALE='en'; exec("from zipfile import ZipFile\nwith ZipFile(console['ZIP']) as archive:\n    names = [n for n in archive.namelist() if n.count('/') <= 1 and n.rsplit('/', 1)[-1] == 'install.py' and not n.startswith(('/', './', '../'))]\n    if len(names) != 1: raise ValueError('Expected one install.py at the ZIP root or inside one folder')\n    code = archive.read(names[0])\nexec(code, console)", {'console': globals()})
```

どちらの行もインターネットに接続せずにインストールし、`index.csv`に英語名を入れます。あとでQGISの表示言語の名前を追加するには、接続できるときにオンライン用のインストール行をもう一度実行してください。

## インストールされるもの

- QGISの設定フォルダ（`profiles`があるフォルダ）の中の`EmOji-san/<カテゴリ>/<名前>.svg`。設定フォルダは、Windowsでは`%APPDATA%\QGIS\QGIS3`、macOSでは`~/Library/Application Support/QGIS/QGIS3`、Linuxでは`~/.local/share/QGIS/QGIS3`です（QGIS 4は`QGIS4`）。
- 同じ設定フォルダにあるユーザープロファイルはSVGファイルを共用し、フォルダはプロファイルごとに登録します。別のプロファイルでも同じセットを使うときは、そのプロファイルでインストールの行を実行します。
- ファイル名は`convenience_store.svg`のような絵文字の英語名です。SVGブラウザの検索欄で探せます。
- 同じフォルダの`index.csv`は、現在のセットの一覧です。絵文字、コードポイント、英語名、QGISの表示言語での名前、カテゴリ、パス、セット、Notoでのファイル名が入っています。スクリプトやAIアシスタントが絵文字を探すのに使えます。インストールの行の先頭に`LOCALE='de';`を付けると、名前の言語を変えられます。

## Resource Sharingプラグイン

このリポジトリはQGIS Resource Sharingプラグイン（QGIS 3）にも登録できます。ただし、プラグインは絵文字を別のフォルダに別のパスで保存します。その絵文字で作ったプロジェクトは、上の1行で入れた絵文字を参照できません。どちらか一方を使ってください。

## ライセンス

- 絵文字: [Google Noto Emoji](https://github.com/googlefonts/noto-emoji)、Apache License 2.0。EmOji-sanはSVGファイルの一部を選び、名前を変えてフォルダに分けています。そのままではQGISが正しく描けないファイル（手の絵文字は真っ黒になります）は、見た目を変えずに書き換えています。それ以外のファイルの中身は変えていません。詳しくは`NOTICE`にあります。
- 国旗・地域旗: Noto Emojiの波打った旗（`third_party/region-flags`）。旗のデザインはパブリックドメインか、著作権の対象外です。そのライセンスは`LICENSE-noto-emoji.txt`の末尾にあります。
- ファイル名、英語名、カテゴリ: [gemoji](https://github.com/github/gemoji)、MIT License。ライセンス文は`LICENSE-gemoji.txt`にあります。
- スクリプト: MIT。
- オンライン用の各行は、公開されたリリースのPythonコードを実行します。GitHubは変更不可のリリースに添付されたファイルを固定し、そのインストーラーは`emoji_san_data.zip`を使う前にSHA-256を照合します。実行前にリリースのAssetsから各スクリプトをダウンロードして読めます。

## メンテナンス

年に1回、Noto Emojiに新しい絵文字が入ったら:

1. `python3 build/update_from_upstream.py`で、版を固定したUnicodeの絵文字一覧とNotoを照合します。SVG、一覧、スタイルファイルを検証してから差し替えます。picosvgが必要です（`python3 -m pip install picosvg`）。`--unicode-version`でUnicodeの版を選べます。新しい絵文字、NotoにSVGがない対象絵文字、互換性のために残した旧SVGが表示されます。公開済みのパスは維持します。新しいSVGの見た目はQGISで確認してください。Sのセットを変えるときは`core_list.txt`を編集して`python3 build/make_core.py`を実行します。地図コレクションのものをMから外すときは、同じように`l_only_list.txt`に書きます。
2. `install.py`の`TAG`と、このREADMEにあるバージョン（古い番号で検索すると見つかります）をすべて書き換え、セットの表の個数を直します。`install.py`の`CLDR`は[cldr-json](https://github.com/unicode-org/cldr-json)の最新リリースに合わせます。新しい絵文字の各国語の名前はそこから取ります。
3. `python3 -m unittest discover -s tests`で再ビルドと配布ファイルを確認します。`python3 tests/scenarios.py --online`で、既存プロジェクトの更新やCLDRの名前の取得を含め、分離したQGISプロファイルでインストーラーを確認します。後者は`qgis`をimportできるPythonが必要です。Dockerでの実行方法はスクリプトの先頭にあります。
4. 公開する前に、リポジトリの設定で[リリースの変更を禁止](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)します。コミット、タグ付け、プッシュを行います。タグを付けたコミットを変更のない状態でチェックアウトし、配布用ファイルを作って、6ファイルすべてをリリースの下書きに添付します。

   ```bash
   python3 build/make_release.py ../emoji-san-v1.1.0-release
   gh release create v1.1.0 ../emoji-san-v1.1.0-release/* --verify-tag --draft --title "EmOji-san v1.1.0" --notes "Noto Emoji as of 2027"
   ```

5. 下書きの添付ファイルを確認してから公開します。リポジトリとリリースの公開後、リリースが変更不可になっていることと、GitHubからサインアウトしてもREADMEのダウンロードリンクが使えることを確認します。
