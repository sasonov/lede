# lede

Turn raw notes and news into an editorial, emoji-accented message formatted for
**Discord** and **Telegram** — ready to copy-paste and send yourself as a user
(no bot, no API). Prose is linted against AI-slop with [vale](https://vale.sh).

It's a [Claude Code](https://claude.com/claude-code) **skill**: install it, then
ask Claude to turn a pile of notes into two send-ready channel posts.

## What it produces

Feed it raw input (notes, bullets, links, news). It writes one clean editorial
master — a hook, a few tight sections, an optional close — lints it, then hands
you two messages:

- **Discord** — native markdown (`##` headers, `-` bullets, `[masked](links)`).
  Renders when you paste and send.
- **Telegram** — Unicode 𝗯𝗼𝗹𝗱 + emoji + `•` + bare URLs. Telegram doesn't parse
  markdown on a user paste, so the formatting is baked into the characters and
  survives the paste.

You copy each block and send it into the channel yourself.

## Requirements

| Need | Why | Required? |
|------|-----|-----------|
| **Claude Code** | it's a Claude Code skill | yes |
| **git** | to clone / update the skill | yes (install only) |
| **Python 3.7+** | `lede.py` — Telegram bold glyphs + message length checks | recommended |
| **vale** | the AI-slop lint gate | recommended |

The skill still runs with neither Python nor vale — it degrades to a manual bold
map and a heuristic self-check. Install both for the full experience.

## Install

Clone straight into your Claude Code skills folder:

**macOS / Linux**
```bash
git clone https://github.com/sasonov/lede.git ~/.claude/skills/lede
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/sasonov/lede.git "$env:USERPROFILE\.claude\skills\lede"
```

Start a new Claude Code session so it discovers the skill. Update later with:
```bash
git -C ~/.claude/skills/lede pull
```

### Install the dependencies

**vale** — the anti-slop gate (no `vale sync` needed; the styles ship in the repo):

| OS | Command |
|----|---------|
| macOS / Linux | `brew install vale` |
| Windows | `winget install errata-ai.Vale` or `scoop install vale` |
| any | [download a release](https://github.com/errata-ai/vale/releases) |

**Python 3.7+** — from your package manager or [python.org](https://www.python.org/downloads/).
Most systems already have it.

## Verify

```bash
python ~/.claude/skills/lede/lede.py --selftest   # prints: ok
vale --version
```

## Use

In Claude Code, just describe the task — the skill triggers on its own:

> Turn these release notes into a Discord and Telegram post:
> *(paste your notes)*

…or invoke it by name: **"use the lede skill on this."** Optional tone flag:
`calm` (default) or `punchy`. Claude drafts, lints, and hands you the two
send-ready blocks. Copy → paste → send.

### Example

**Input**
```
- v2.3 shipped today
- new dark mode, 40% faster cold start
- breaking: old API keys stop working aug 1
- docs: example.com/v2
```

**Discord**
```
## 🚀 v2.3 is live

**Dark mode** landed, and cold starts are **40% faster**.

**Heads up — breaking change:** old API keys stop working **August 1**. Rotate
yours before then.

Docs: [example.com/v2](https://example.com/v2)
```

**Telegram**
```
🚀 𝘃𝟮.𝟯 𝗶𝘀 𝗹𝗶𝘃𝗲

𝗗𝗮𝗿𝗸 𝗺𝗼𝗱𝗲 landed, and cold starts are 𝟰𝟬% 𝗳𝗮𝘀𝘁𝗲𝗿.

𝗛𝗲𝗮𝗱𝘀 𝘂𝗽 — 𝗯𝗿𝗲𝗮𝗸𝗶𝗻𝗴 𝗰𝗵𝗮𝗻𝗴𝗲: old API keys stop working 𝗔𝘂𝗴𝘂𝘀𝘁 𝟭. Rotate yours before then.

Docs: https://example.com/v2
```

## How it works

1. **Draft** one platform-neutral editorial master (hook → tight sections →
   optional close); emoji only as section accents, never per-line spam.
2. **Lint** the master with vale against AI-slop wordlists (banned tells, hedges,
   "not just X but Y"); revise once, then report residuals. Quotes and proper
   nouns are never edited to satisfy the linter.
3. **Project** into Discord markdown and Telegram Unicode (`lede.py bold`).
4. **Length-gate** each message with `lede.py count` (Discord 2000 code points /
   Telegram 4096 UTF-16 units); split into numbered parts if over.

## The `lede.py` helper

```bash
python lede.py bold "August 1"          # -> 𝗔𝘂𝗴𝘂𝘀𝘁 𝟭
python lede.py count discord  "<msg>"   # code-point length,  limit 2000
python lede.py count telegram "<msg>"   # UTF-16 code units,  limit 4096  (exit 1 if OVER)
python lede.py --selftest               # -> ok
```

## Files

```
SKILL.md                 the instructions Claude follows
reference/formatting.md  Discord markdown + Telegram Unicode map
lede.py                  bold converter + per-platform length checker
.vale.ini                vale config (local styles, no `vale sync`)
styles/Editorial/*.yml   Slop / Hedging / NotJust wordlists
```

## Note on Telegram Unicode

The Telegram output uses Unicode math-bold characters. They render visually
everywhere, but they aren't real markup: screen readers announce them as
"mathematical bold," and Ctrl-F for `August` won't match `𝗔𝘂𝗴𝘂𝘀𝘁`. It's the
only formatting that survives a manual copy-paste into Telegram as a user — an
accepted trade-off for this workflow.
