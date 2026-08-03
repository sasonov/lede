# Discord vs Telegram formatting

Discord and Telegram receive separately authored messages based on the same fact brief. Do not reuse one finished body and swap formatting. Use native formatting on both platforms; never imitate bold with Unicode mathematical characters.

Both platforms forbid em dashes (`—`) in drafted copy. Use a comma, colon,
semicolon, period, or parentheses instead.

## Discord

| Feature | Syntax |
|---|---|
| Header | `## ` / `### ` |
| Bold | `**bold**` |
| Italic | `*italic*` |
| Bullets | `- item` |
| Link | `[label](url)` |
| Code block | fenced code block |

- Character limit: 2000 characters of message content.
- Use 2–4 meaningful emoji accents in a typical 3–5-section announcement.
- Keep emoji on the title and selected section headers, not every bullet.

## Telegram

- Use normal native bold for titles, headers, and key terms. In agent source, mark it as `**bold**`; the Telegram rendering surface converts it to a bold entity.
- Native formatting survives the copy-paste workflow. Do not convert letters to Unicode mathematical-bold glyphs.
- Never use Discord custom server emoji (`<:PredixaLogo:1488555443629592686>`, `<:TMX_ecosystem_logo:1526147965469589504>`, or any `<:name:id>` / `<a:name:id>` code). Discord resolves those; Telegram shows the raw string. Use Unicode emoji here. The checker enforces this.
- Separate every paragraph with a blank line. Telegram draws consecutive lines flush against each other, so single-newline text sends as one wall of text. Consecutive `- ` list items are the exception; the blank lines go before and after the list. The checker enforces this.
- Use literal `-` list markers, not `•`.
- Use bare URLs so Telegram auto-links them.
- Do not use Markdown headings (`##`) or HTML tags.
- Emit the Telegram message as ordinary rendered text, never inside a code block, quote, or inline-code wrapper.
- Character limit: 4096 UTF-16 code units after formatting entities are parsed.
- Use 2–4 meaningful emoji accents in a typical 3–5-section announcement. A longer post may use one additional accent when it improves scanning.

## Emoji standard

The target is roughly 30–40% more visual guidance than the previous minimalist style:

- Typical short announcement: 2–3 emoji.
- Typical multi-section announcement: 3–4 emoji.
- Choose placements after each platform draft is complete. Do not reuse an emoji
  plan as a substitute for independently authored structure.
- Avoid emoji bullets on every line, decorative clusters, repeated emoji, and mid-sentence interruptions.

## Validation

Run the checker on each projected source file:

```bash
python scripts/lede.py check discord --file discord.txt
python scripts/lede.py check telegram --file telegram.txt
python scripts/lede.py compare --discord-file discord.txt --telegram-file telegram.txt
```

The checker rejects generic label stacks, unsupported urgency, em dashes, malformed bold markers, Unicode mathematical alphanumeric glyphs, `•` list markers, and whole-message code/quote wrappers. Telegram length is measured on rendered text after supported formatting markers are removed. The comparison gate uses character similarity, token overlap, and section order; it also rejects identical short drafts.
