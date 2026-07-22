---
name: lede
description: Turn raw notes, news, or bullet dumps into an editorial, emoji-accented message formatted for BOTH Discord and Telegram, ready to copy-paste and send AS A USER (no bot). Use when the user wants to broadcast, announce, post an update, or "make this look good for Discord/Telegram". Lints the prose against AI-slop with vale.
version: 1.2.0
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

Turn raw input (notes, news, links, bullets) into **two separately authored
messages**: one for Discord and one for Telegram. The user copies and sends each
finished message themselves. Preserve native formatting on both platforms:

- **Discord** → output standard Discord markdown.
- **Telegram** → output normal bold entities/markdown on a rendering surface such
  as Hermes Telegram. Native Telegram formatting survives copy-paste in this
  workflow. Never replace letters with Unicode mathematical-bold characters.

## Runtime (any harness)

This skill is harness-agnostic: it works in Claude Code, Hermes, or any agent
with a terminal + file-writing tool. Two conventions:

- **`<skill-dir>`** below means the folder this `SKILL.md` lives in. Claude Code:
  `~/.claude/skills/lede`. Hermes: `~/.hermes/skills/<category>/lede`. Substitute
  the real path.
- **Never put message text inside a shell command.** Raw notes and drafts can
  contain `$(...)`, backticks, or `|` that the shell would execute. Always write
  the text to a temp file with your file tool, then pass `--file <path>` to
  `lede.py` (or pipe via stdin). The commands below only ever carry a filename.

## Inputs

- **Raw content**: the notes/news to shape. Required.
- **Tone**: `calm` (default) or `punchy`. Optional.

## Process

### 1. Build the fact brief

Extract a short platform-neutral checklist of required facts, names, dates,
links, warnings, and calls to action. This is a factual source sheet, not reusable
finished prose. Both platform drafts must preserve every required fact.

Choose a shape from the facts instead of forcing every announcement into the
same template. **Default to prose-first.** Use compact bullets, Q&A, a timeline,
a warning-first structure, or a single-update paragraph only when that shape
makes the facts easier to find. Labels are optional and must name genuinely
different operational facts. Never require a hook, section stack, CTA, or close
when the source does not supply one. Do not use more than two generic labels.

**Length:** aim for ≤ ~1900 characters per platform draft. This is a drafting
guide, not the check. The real validation is in step 5.

**Emoji density:** use roughly one-third more emoji than a minimalist corporate
post. A standard announcement should normally contain **2–4 meaningful emoji
accents** across the title and selected factual anchors. Place emoji independently
after each platform's prose is final. Do not put emoji on every bullet, stack decorative
clusters (`🚀🔥✅`), or interrupt sentences with them.

**Voice**: say it once, plainly. Active voice, concrete nouns, no hedging, no
build-up. `punchy` means tighter editing, not fake urgency, clipped sentence
stacks, or a manufactured hook. Avoid these AI-slop tells:
- **No em dashes (`—`) in drafted copy.** Use a comma, colon, semicolon, period,
  or parentheses instead. Vale and the platform checker must both reject them.
- **"not just X, but Y"** and "it's not about… it's about…": say the one true thing.
- **Uniform sentence rhythm**: vary length or it reads like a bot.
- **Hollow openers** ("In today's world…", "As we all know…"): open on the point.
- No vague filler, no jargon without a plain-language anchor, no humor near bad
  news, don't lecture the reader (from impeccable's ux-writing).

### 2. Write two separate send-ready messages

Use the same fact brief, but **author Discord and Telegram independently**. They
must be separate messages, not one body with formatting swapped. Multi-section
posts must use different information architecture, not merely synonyms: change
the opening, order, grouping, rhythm, and close to fit each platform. Do not copy the complete prose from one draft into the other.
Short fixed facts may match verbatim. See `references/formatting.md`.

**Discord** (renders on user paste-and-send): `##` / `###` headers, `-` bullets,
`**bold**`, `*italic*`, `[label](url)`, ```` ```lang … ``` ```` code.

**Telegram:** use `**normal bold**` for the title, headers, and key terms; use
literal `-` list markers; use 2–4 meaningful emoji accents for a normal post; and
use **bare URLs**. Do not use `##` headings, `•` list markers, HTML tags, or Unicode
mathematical-bold glyphs. Emit Telegram as ordinary rendered text, not a code
block, so the user copies native formatting rather than raw markup.

### 3. Mandatory editorial anti-slop review

Before Vale, record an internal **pass or revise** decision for every question
below. Do not emit the checklist. Any failure requires one rewrite and a second
review. A draft cannot proceed with a failed item.

1. Does every section add a new fact rather than restate one?
2. Are there no more than two label-plus-explanation sections?
3. Are generic imperative or question labels absent?
4. Is every urgency claim supported by a sourced deadline or consequence?
5. Does the copy avoid telling readers obvious things or manufacturing stakes?
6. Is the hook specific enough that it could not introduce another product?
7. Does any CTA name a concrete action, destination, and reason?
8. Do sentence lengths and openings visibly vary?
9. Does the close add information instead of summarizing the opening?
10. Would deleting any section remove a real fact? If not, delete that section.

### 4. Vale gate both drafts

Lint **both platform drafts separately**. Waive only an attributed, source-verbatim
quotation or the exact proper-name span. Never waive a whole sentence merely
because it contains a quote or name.

```bash
# Write the draft to a temp file first, then lint it. --config is REQUIRED
# (vale searches upward from the target file, and the draft lives elsewhere).
# Hermes Docker installs may keep user binaries outside PATH.
VALE_BIN="$(command -v vale 2>/dev/null || true)"
[ -n "$VALE_BIN" ] || VALE_BIN="$HOME/.local/bin/vale"
"$VALE_BIN" --config="<skill-dir>/.vale.ini" /path/to/discord-draft.md /path/to/telegram-draft.md
```

For this Hermes profile, the verified skill directory is
`/opt/data/skills/communication/lede` and Vale is installed at
`/opt/data/home/.local/bin/vale`. Continue to resolve paths dynamically when
possible so the skill remains portable.

- **Clean** → proceed.
- **Alerts** (after the narrow quote/name waiver) → revise those lines and run
  once more. Residual alerts block delivery in the verified Hermes environment.
- **Any Vale execution failure in Hermes** blocks delivery. Do not treat a
  missing binary, missing config, or unexplained nonzero exit as a pass.
- In other portable environments only, report "Vale unavailable: reduced check"
  and perform a manual wordlist check rather than claiming full validation.

### 5. Validate structure, separation, and length, then emit

**Validate and count each projected message with the script: don't eyeball it.**
The checker rejects generic label stacks, unsupported urgency, em dashes,
malformed bold markers, Unicode mathematical-bold glyphs, `•` list markers, and whole-message code/quote wrappers. Telegram count strips
supported formatting markers first, then counts UTF-16 units in the rendered
text. Write each message to a temp file:

```bash
python "<skill-dir>/scripts/lede.py" check discord  --file discord-msg.txt
python "<skill-dir>/scripts/lede.py" check telegram --file telegram-msg.txt
python "<skill-dir>/scripts/lede.py" compare --discord-file discord-msg.txt --telegram-file telegram-msg.txt
```

`compare` rejects identical and near-identical drafts using character, token, and
section-order checks. If it fails, rewrite one platform version; cosmetic marker
or synonym changes do not count as separate authorship.

If either prints `OVER` (nonzero exit), split into numbered parts (`(1/2)`) and
run `check` on **each part** until all pass; when the two channels split
differently, label each block by platform + part.

Emit two clearly labeled sections in this exact order:

1. Write `**Discord**` as a title on its own line **outside and above** the fenced
   block, then put only the copyable Discord message inside the fence.
2. Write `**Telegram**` as a title on its own line, add one blank line, then emit
   the copyable Telegram message as **ordinary rendered text with no fence**.

The platform title must never appear inside either copyable message. Discord's
message stays fenced so its markdown source remains literal; use `~~~` if the
message itself contains ```` ``` ````. **Never fence, quote, indent, or wrap the
Telegram message in inline code.** Telegram preserves a copied fenced block as
preformatted/code text, which breaks the intended paste-and-send result. The
platform titles are mandatory; never rely on output order to identify them.
Apart from these titles, include no counts or commentary. Add an extra line only
when something needs action: an over-limit split or unresolved Vale alerts.

### Links, images, code in the source
- **URLs** → Discord `[label](url)`; Telegram bare URL.
- **Images** → neither renders inline markdown images; list them as URLs.
- **Code** → Discord fenced block; Telegram inline code or a short fenced block.
