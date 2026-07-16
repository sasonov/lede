# dispatch

Portable agent skill: raw notes/news → an editorial, emoji-accented message for
**Discord** and **Telegram**, ready to **copy-paste and send yourself as a user**
(no bot, no API). Prose is linted against AI-slop with [vale](https://vale.sh).

- **Discord** — markdown (renders on your paste-and-send).
- **Telegram** — Unicode 𝗯𝗼𝗹𝗱 + emoji + `•` + bare URLs (markdown doesn't
  survive a manual paste; `lede.py bold` does the conversion).

## Files

```
SKILL.md               instructions the agent follows
reference/formatting.md  Discord markdown + Telegram Unicode
lede.py                bold converter + platform length checker
.vale.ini              vale config (local styles, no `vale sync`)
styles/Editorial/*.yml Slop / Hedging / NotJust wordlists
```

## Portability (two soft dependencies)

Drop the folder into any harness. It shells out to two binaries:

- **vale** — the anti-slop gate. If absent, the skill self-checks against the
  same wordlists ("reduced check"). Install: `winget install errata-ai.Vale`
  (Windows) · `brew install vale` (macOS/Linux) · or the
  [releases page](https://github.com/errata-ai/vale/releases). No `vale sync`
  needed — styles are local.
- **python** — runs `lede.py` (Telegram bold glyphs + the `count` length gate).
  If absent, the manual map in `reference/formatting.md` is the bold fallback.

Verify: `vale --version` and `python lede.py --selftest` (prints `ok`).

## Note

Unicode-styled text renders visually everywhere but isn't real markup: screen
readers read it as "mathematical bold" and Ctrl-F for `August` won't match
`𝗔𝘂𝗴𝘂𝘀𝘁`. Accepted trade-off for the user-paste Telegram path — it's the only
formatting that survives a manual copy-send.
