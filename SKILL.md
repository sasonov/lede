---
name: lede
description: Turn raw notes, news, or bullet dumps into an editorial, emoji-accented message formatted for BOTH Discord and Telegram, ready to copy-paste and send AS A USER (no bot). Use when the user wants to broadcast, announce, post an update, or "make this look good for Discord/Telegram". Lints the prose against AI-slop with vale.
version: 1.0.0
author: sasonov
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Discord, Telegram, editorial, broadcast, announcement, formatting, emoji, vale, writing, news, copywriting]
    category: communication
    requires_toolsets: [terminal]
---

# Lede

Turn raw input (notes, news, links, bullets) into a polished editorial message.
The user **copies each finished message and sends it themselves** into a Discord
channel and a Telegram channel — as a normal user, no bot, no API. Everything
must render on a plain copy-paste-and-send:

- **Discord** renders markdown when a user pastes and sends → output markdown.
- **Telegram** does NOT parse markdown/HTML on a user paste → formatting must be
  **Unicode characters** + emoji (baked into the glyph, survives any paste).

## Runtime (any harness)

This skill is harness-agnostic — it works in Claude Code, Hermes, or any agent
with a terminal + file-writing tool. Two conventions:

- **`<skill-dir>`** below means the folder this `SKILL.md` lives in. Claude Code:
  `~/.claude/skills/lede`. Hermes: `~/.hermes/skills/<category>/lede`. Substitute
  the real path.
- **Never put message text inside a shell command.** Raw notes and drafts can
  contain `$(...)`, backticks, or `|` that the shell would execute. Always write
  the text to a temp file with your file tool, then pass `--file <path>` to
  `lede.py` (or pipe via stdin). The commands below only ever carry a filename.

## Inputs

- **Raw content** — the notes/news to shape. Required.
- **Tone** — `calm` (default) or `punchy`. Optional.

## Process

### 1. Draft the master (platform-neutral)

Write ONE editorial body in plain markdown. **Default shape — follow it when the
content fits, break it when it doesn't:**

- **Hook** — one sharp line, the single most important thing. No preamble.
- **A few tight sections** — a short bold label + 1–3 sentences each. Lead with
  what changed, not background. Group related facts.
- **Close only when there's a real one** — a consequence or a next step. Do NOT
  manufacture a takeaway; a hollow closer that restates the intro is itself
  AI-slop. If the content has no close, end on the last real point.

**Length: aim ≤ ~1900 characters.** This is a drafting guide, not the check —
formatting adds characters. The real validation is on the projected output (4).

**Emoji discipline** (load-bearing — emoji spam is itself AI-slop):
at most ONE meaningful emoji as a section-header accent. NO emoji bullet on every
line, NO 🚀🔥✅ clusters, NO mid-sentence emoji.

**Voice** — say it once, plainly. Active voice, concrete nouns, no hedging, no
build-up. `punchy` = shorter sentences, stronger verbs, a bolder hook — never
more emoji. Avoid these AI-slop tells (vale catches the lexical ones; the
structural ones are on you):
- **"not just X, but Y"** and "it's not about… it's about…" — say the one true thing.
- **Uniform sentence rhythm** — vary length or it reads like a bot.
- **Hollow openers** ("In today's world…", "As we all know…") — open on the point.
- No vague filler, no jargon without a plain-language anchor, no humor near bad
  news, don't lecture the reader (from impeccable's ux-writing).

### 2. Vale gate (lint the MASTER prose only)

Lint the neutral master, before formatting. **First, waive any alert on text
inside quotation marks or on a proper noun** — never edit a quote or a name to
satisfy the linter (a news tool must not misquote its source).

```bash
# Write the draft to a temp file first, then lint it. --config is REQUIRED
# (vale searches upward from the target file, and the draft lives elsewhere).
vale --config="<skill-dir>/.vale.ini" /path/to/draft.md
```

- **Clean** → proceed.
- **Alerts** (after the quote/name waiver) → revise those lines, run **once**
  more, then proceed and list any residual alerts. Do NOT loop.
- **Any vale failure** — binary missing, config not found, or nonzero without
  alerts → skip the gate, read the wordlists in `styles/Editorial/*.yml`,
  self-check the draft against them, and note "vale unavailable — reduced check."
  (This skill is **portable and vale-optional**, not self-contained.)

### 3. Project into the two send-ready messages

Prose is clean; only formatting changes. See `references/formatting.md`.

**Discord** (renders on user paste-and-send): `##` / `###` headers, `-` bullets,
`**bold**`, `*italic*`, `[label](url)`, ```` ```lang … ``` ```` code.

**Telegram** (must survive a manual paste → Unicode): author the message with
`**double-asterisk**` marking each span you want bold (headers, key terms), use
`•` bullets, one leading emoji per header, and **bare URLs** (Telegram
auto-links — never `[]()`). Then write it to a temp file and transpile the
markers to Unicode bold in one pass:

```bash
python "<skill-dir>/scripts/lede.py" bold --file telegram-draft.txt
```

The output is the final Telegram message (asterisks stripped, spans bolded). If
the command **exits nonzero**, a `**` marker is unmatched, empty, or spans a line
break — fix the markers and rerun; never send output with literal `**` in it.
No `<b>` or `#` — they show up literally. If python is unavailable, hand-convert
with the fallback map in `references/formatting.md`.

### 4. Validate length, then emit

**Count each projected message with the script — don't eyeball it** (Telegram's
surrogate-pair glyphs make ordinary character counts wrong). Write each message
to a temp file, then:

```bash
python "<skill-dir>/scripts/lede.py" count discord  --file discord-msg.txt   # limit 2000
python "<skill-dir>/scripts/lede.py" count telegram --file telegram-msg.txt  # limit 4096
```

If either prints `OVER` (nonzero exit), split into numbered parts (`(1/2)`) and
run `count` on **each part** until all pass; when the two channels split
differently, label each block by platform + part.

Emit two clearly labeled sections in this exact order:

1. Write `**Discord**` as a title on its own line **outside and above** the fenced
   block, then put only the copyable Discord message inside the fence.
2. Write `**Telegram**` as a title on its own line **outside and above** the fenced
   block, then put only the copyable Telegram message inside the fence.

The platform title must never appear inside the fenced message because the user
copies the block contents directly. Use `~~~` if the message itself contains
```` ``` ````. The platform titles are mandatory—never rely on block order to
identify the outputs. Apart from these titles, include no counts or commentary.
Add an extra line only when something needs action: an over-limit split or
unresolved Vale alerts.

### Links, images, code in the source
- **URLs** → Discord `[label](url)`; Telegram bare URL.
- **Images** → neither renders inline markdown images; list them as URLs.
- **Code** → Discord fenced block; Telegram indent or `•`-prefix, keep it short.
