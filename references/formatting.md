# Discord vs Telegram formatting

Discord and Telegram receive separately authored messages based on the same fact brief. Do not reuse one finished body and swap formatting. Use native formatting on both platforms; never imitate bold with Unicode mathematical characters.

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
- Good placements: title, launch/feature section, requirements or warning section, feedback/CTA.
- Avoid emoji bullets on every line, decorative clusters, repeated emoji, and mid-sentence interruptions.

## Validation

Run the checker on each projected source file:

```bash
python scripts/lede.py check discord --file discord.txt
python scripts/lede.py check telegram --file telegram.txt
python scripts/lede.py compare --discord-file discord.txt --telegram-file telegram.txt
```

The checker rejects malformed bold markers, Unicode mathematical alphanumeric glyphs, `•` list markers, and whole-message code/quote wrappers. Telegram length is measured on rendered text after supported formatting markers are removed. The comparison gate rejects substantial drafts with normalized similarity of 0.900 or higher.
