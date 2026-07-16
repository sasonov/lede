# Discord vs Telegram formatting

Both messages are **copied and sent by a human user** — no bot, no API. So:
- **Discord** parses markdown on send → use markdown.
- **Telegram** does NOT parse markdown/HTML on a user paste → formatting must be
  **Unicode characters** (the bold look is baked into the glyph, so it survives
  any paste and renders everywhere).

## Discord (markdown source)

| Feature      | Syntax                    |
|--------------|---------------------------|
| Header       | `## ` / `### `            |
| Bold         | `**bold**`                |
| Italic       | `*italic*`                |
| Bullets      | `- item`                  |
| Link         | `[label](url)` (auto-embeds) |
| Code block   | ```` ```lang\n…\n``` ```` |

No tables, no inline markdown images. **Char limit 2000.**

## Telegram (Unicode — for a user send)

- **Bold** headers / labels / key terms with the converter:
  `python lede.py bold "text"` → 𝘁𝗲𝘅𝘁. Only A–Z / a–z / 0–9 convert; emoji,
  punctuation, and URLs pass through untouched.
- `•` bullets. **Bare URLs** (Telegram auto-links them). One leading emoji per
  header.
- No `**`, `<b>`, or `#` — they render as literal characters.
- **Char limit 4096.** Bold letters are surrogate pairs (2 UTF-16 units each), so
  keep bold to headers + key terms, not whole paragraphs.

**Manual fallback** (only if python is unavailable) — sans-serif bold map:

```
A→𝗔 B→𝗕 C→𝗖 D→𝗗 E→𝗘 F→𝗙 G→𝗚 H→𝗛 I→𝗜 J→𝗝 K→𝗞 L→𝗟 M→𝗠 N→𝗡
O→𝗢 P→𝗣 Q→𝗤 R→𝗥 S→𝗦 T→𝗧 U→𝗨 V→𝗩 W→𝗪 X→𝗫 Y→𝗬 Z→𝗭
a→𝗮 b→𝗯 c→𝗰 d→𝗱 e→𝗲 f→𝗳 g→𝗴 h→𝗵 i→𝗶 j→𝗷 k→𝗸 l→𝗹 m→𝗺 n→𝗻
o→𝗼 p→𝗽 q→𝗾 r→𝗿 s→𝘀 t→𝘁 u→𝘂 v→𝘃 w→𝘄 x→𝘅 y→𝘆 z→𝘇
0→𝟬 1→𝟭 2→𝟮 3→𝟯 4→𝟰 5→𝟱 6→𝟲 7→𝟳 8→𝟴 9→𝟵
```

## Why not MarkdownV2 / HTML

Those only render when a **bot** sends with `parse_mode`. A human paste shows the
literal `*` / `<b>`, so Unicode is the correct choice for user-sent messages.
