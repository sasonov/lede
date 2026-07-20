# lede

Turn raw notes and news into an editorial, emoji-accented message formatted for
**Discord** and **Telegram** — ready to copy-paste and send yourself as a user
(no bot, no API). Prose is linted against AI-slop with [vale](https://vale.sh).

It's an agent **skill** in the standard `SKILL.md` format, so it runs in
[Claude Code](https://claude.com/claude-code), [Hermes](https://github.com/NousResearch/hermes-agent),
or any harness that loads skills: install it, then ask the agent to turn a pile
of notes into two send-ready channel posts.

## What it produces

Feed it raw input (notes, bullets, links, news). It writes one clean editorial
master — a hook, a few tight sections, an optional close — lints it, then hands
you two messages:

- **Discord** — native markdown (`##` headers, `-` bullets, `[masked](links)`).
  Renders when you paste and send.
- **Telegram** — Unicode 𝗯𝗼𝗹𝗱 + emoji + `•` + bare URLs. Telegram doesn't parse
  markdown on a user paste, so the formatting is baked into the characters and
  survives the paste.

You copy each message and send it into the channel yourself. Discord is shown in
a fenced block so its markdown stays literal. Telegram is shown as ordinary
Unicode text, never as a code block, so copying it does not preserve unwanted
preformatted styling.

## Requirements

| Need | Why | Required? |
|------|-----|-----------|
| **An agent that loads `SKILL.md` skills** | Claude Code, Hermes, etc. | yes |
| **git** | to clone / update the skill | yes (install only) |
| **Python 3.7+** | `scripts/lede.py` — Telegram bold glyphs + message length checks | recommended |
| **vale** | the AI-slop lint gate | recommended |

The skill still runs with neither Python nor vale — it degrades to a manual bold
map and a heuristic self-check. Install both for the full experience.

## Install

### Claude Code

Clone straight into your skills folder, then start a new session:

```bash
# macOS / Linux
git clone https://github.com/sasonov/lede.git ~/.claude/skills/lede
```
```powershell
# Windows (PowerShell)
git clone https://github.com/sasonov/lede.git "$env:USERPROFILE\.claude\skills\lede"
```

Update later: `git -C ~/.claude/skills/lede pull`

### Hermes

Skills live under `~/.hermes/skills/<category>/<name>/`. Clone into the
`communication` category (matches the skill's own `metadata.hermes.category`):

```bash
git clone https://github.com/sasonov/lede.git ~/.hermes/skills/communication/lede
```

Or use the CLI, which resolves GitHub skill repos and runs a safety scan:

```bash
hermes skills install sasonov/lede --category communication
```

Then `hermes skills list` should show `lede`. Update later with `git pull` in
that folder.

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
# adjust the path to wherever you installed the skill
python ~/.claude/skills/lede/scripts/lede.py --selftest   # prints: ok
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

🚀 𝘃𝟮.𝟯 𝗶𝘀 𝗹𝗶𝘃𝗲

𝗗𝗮𝗿𝗸 𝗺𝗼𝗱𝗲 landed, and cold starts are 𝟰𝟬% 𝗳𝗮𝘀𝘁𝗲𝗿.

𝗛𝗲𝗮𝗱𝘀 𝘂𝗽 — 𝗯𝗿𝗲𝗮𝗸𝗶𝗻𝗴 𝗰𝗵𝗮𝗻𝗴𝗲: old API keys stop working 𝗔𝘂𝗴𝘂𝘀𝘁 𝟭. Rotate yours before then.

Docs: https://example.com/v2

## How it works

1. **Draft** one platform-neutral editorial master (hook → tight sections →
   optional close); emoji only as section accents, never per-line spam.
2. **Lint** the master with vale against AI-slop wordlists (banned tells, hedges,
   "not just X but Y"); revise once, then report residuals. Quotes and proper
   nouns are never edited to satisfy the linter.
3. **Project** into Discord markdown and Telegram Unicode (`scripts/lede.py bold`).
4. **Length-gate** each message with `scripts/lede.py count` (Discord 2000 code
   points / Telegram 4096 UTF-16 units); split into numbered parts if over.

Message text is always passed to the helper via `--file` (or stdin), never as a
shell argument — so pasted content with `$(...)`, backticks, or `|` can't be
executed by the shell.

## The `scripts/lede.py` helper

```bash
# author the Telegram message with **double-asterisk** bold spans, then:
python scripts/lede.py bold  --file telegram.txt        # -> Unicode bold, markers stripped
python scripts/lede.py count discord  --file discord.txt   # code points, limit 2000
python scripts/lede.py count telegram --file telegram.txt  # UTF-16 units, limit 4096 (exit 1 if OVER)
python scripts/lede.py --selftest                       # -> ok
```

## Files

```
SKILL.md                  the instructions the agent follows
references/formatting.md  Discord markdown + Telegram Unicode map
scripts/lede.py           bold converter + per-platform length checker
.vale.ini                 vale config (local styles, no `vale sync`)
styles/Editorial/*.yml    Slop / Hedging / NotJust wordlists
```

## Note on Telegram Unicode

The Telegram output uses Unicode math-bold characters. They render visually
everywhere, but they aren't real markup: screen readers announce them as
"mathematical bold," and Ctrl-F for `August` won't match `𝗔𝘂𝗴𝘂𝘀𝘁`. It's the
only formatting that survives a manual copy-paste into Telegram as a user — an
accepted trade-off for this workflow.
