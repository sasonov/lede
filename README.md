# lede

Turn raw notes and news into an editorial, emoji-accented message formatted for
**Discord** and **Telegram**, ready to copy-paste and send yourself as a user
(no bot, no API). Prose is linted against AI-slop with [vale](https://vale.sh).

It's an agent **skill** in the standard `SKILL.md` format, so it runs in
[Claude Code](https://claude.com/claude-code), [Hermes](https://github.com/NousResearch/hermes-agent),
or any harness that loads skills: install it, then ask the agent to turn a pile
of notes into two send-ready channel posts.

## What it produces

Feed it raw input (notes, bullets, links, news). It writes one clean editorial
fact brief, then independently writes and lints two platform-specific messages:

- **Discord:** native markdown (`##` headers, `-` bullets, `[masked](links)`).
  Renders when you paste and send.
- **Telegram:** native bold + emoji + `-` bullets + bare URLs. The Telegram
  rendering surface creates normal formatting entities that survive this
  workflow's copy-paste. Unicode mathematical bold is forbidden.

You copy each message and send it into the channel yourself. Discord is shown in
a fenced block so its markdown stays literal. Telegram is shown as ordinary
rendered text, never as a code block, so native formatting is preserved.

## Requirements

| Need | Why | Required? |
|------|-----|-----------|
| **An agent that loads `SKILL.md` skills** | Claude Code, Hermes, etc. | yes |
| **git** | to clone / update the skill | yes (install only) |
| **Python 3.7+** | `scripts/lede.py`: formatting validation + message length checks | recommended |
| **vale** | the AI-slop lint gate | recommended |

The skill still runs with neither Python nor vale, but loses automated formatting,
length, and prose checks. Install both for the full experience.

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

**vale**: the anti-slop gate (no `vale sync` needed; the styles ship in the repo):

| OS | Command |
|----|---------|
| macOS / Linux | `brew install vale` |
| Windows | `winget install errata-ai.Vale` or `scoop install vale` |
| any | [download a release](https://github.com/errata-ai/vale/releases) |

**Python 3.7+**: from your package manager or [python.org](https://www.python.org/downloads/).
Most systems already have it.

## Verify

```bash
# adjust the path to wherever you installed the skill
python ~/.claude/skills/lede/scripts/lede.py --selftest   # prints: ok
vale --version
```

## Use

In Claude Code, just describe the task: the skill triggers on its own:

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

**Heads up, breaking change:** old API keys stop working **August 1**. Rotate
yours before then.

Docs: [example.com/v2](https://example.com/v2)
```

**Telegram**

**⚠️ Rotate old API keys by August 1**

Old API keys stop working on August 1. Rotate yours before then.

🚀 v2.3 shipped today with dark mode and **40% faster cold starts**.

📚 Docs: https://example.com/v2

## How it works

1. **Extract** one platform-neutral fact brief: facts only, not reusable prose.
2. **Author** Discord and Telegram independently with different information architecture.
3. **Review** both drafts against the mandatory structural anti-slop rubric.
4. **Lint** both drafts separately with Vale against AI-slop wordlists.
5. **Validate** structure, formatting, and length with `scripts/lede.py check`, then enforce
   separate authorship with `scripts/lede.py compare`.

Message text is always passed to the helper via `--file` (or stdin), never as a
shell argument: so pasted content with `$(...)`, backticks, or `|` can't be
executed by the shell.

## The `scripts/lede.py` helper

```bash
python scripts/lede.py check discord  --file discord.txt
python scripts/lede.py check telegram --file telegram.txt
python scripts/lede.py compare --discord-file discord.txt --telegram-file telegram.txt
python scripts/lede.py count discord  --file discord.txt
python scripts/lede.py count telegram --file telegram.txt
python scripts/lede.py --selftest                       # -> ok
```

## Files

```
SKILL.md                  the instructions the agent follows
references/formatting.md  native Discord + Telegram formatting rules
scripts/lede.py           formatting validator + per-platform length checker
.vale.ini                 vale config (local styles, no `vale sync`)
styles/Editorial/*.yml    lexical slop, hedging, urgency, and punctuation rules
```

## Telegram accessibility

Use native Telegram bold only. Unicode mathematical alphanumeric characters are
not real formatting, harm search and screen-reader output, and are rejected by
the validator. The validator also rejects wrapping the entire Telegram message
in a code block, blockquote, or indented code block.
