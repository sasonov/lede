---
name: lede
description: Turn raw notes, news, or bullet dumps into an editorial, emoji-accented message formatted for BOTH Discord and Telegram, ready to copy-paste and send AS A USER (no bot). Use when the user wants to broadcast, announce, post an update, or "make this look good for Discord/Telegram". Also covers maintenance and downtime notices, which always ship with a matching branded status card it renders and hands over. Lints the prose against AI-slop with vale.
version: 1.3.0
author: sasonov
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Discord, Telegram, editorial, broadcast, announcement, maintenance, downtime, status, formatting, emoji, vale, writing, news, copywriting]
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
  **Separate every paragraph with a blank line** (see step 2).

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
- **Maintenance**: when the broadcast is a downtime notice, the `brand`
  (`predixa` | `tmx`), the `state` (`scheduled` | `underway` | `restored`), and
  the window times. Optional; absent means the ordinary text-only run. See step 4b.

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

**Blank line between every paragraph.** Telegram has no paragraph spacing of its
own: consecutive lines are drawn flush against each other, so a message written
with single newlines arrives in the channel as one unbroken wall of text, no
matter how well the sentences are written. One blank line between paragraphs is
what makes it scannable in a feed, and it is the single most common way this
skill's output goes wrong. Consecutive `-` list items are the one exception:
they belong tight together, with a blank line before the list and after it. The
checker in step 5 enforces this.

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

### 4b. Maintenance broadcasts: render the status card

**Only when the message is a downtime notice**, skip this step otherwise. When it
is one, the card is **part of the deliverable**, not an extra: a maintenance
broadcast never ships text-only. If an input is missing (brand, state, or the
times), ask for that one thing, then render. Never drop the card silently.

Neither platform renders an inline image, so the card is an **attachment**: the
user sends it alongside the message from the file picker. It is never pasted, so
it stays out of both messages in step 5.

Pick the design by what the message is doing:

| design | shape | reach for it when |
|---|---|---|
| `status-plate` | two large times on a coloured panel | the **notice**, where the window is the news |
| `station-rail` | a three-stop timeline that fills in | **underway / restored**, where progress is the news |

Write the copy to a JSON file (never inline, same rule as `lede.py`), then:

```bash
python "<skill-dir>/scripts/card.py" --brand tmx --design station-rail \
    --state underway --fields /path/to/copy.json --out /path/to/card.png
```

`copy.json` holds `HEADLINE` + `FOIL` (the headline splits into a plain clause
and an italic one) plus the design's time fields: `TIME_START`/`TIME_END` for the
plate, `TIME_NOTICE`/`TIME_WINDOW`/`TIME_RESTORED` for the rail. Every field is
budgeted; over-long or blank copy fails the run rather than shipping a broken
card. `TIME_START` is the one exception: the plate has no zone for it when
`--state restored`.

**Default copy**, what the design ships. Use it unless the incident needs
something more specific, and keep the prose saying the same thing as the card:

| state | brand | HEADLINE | FOIL |
|---|---|---|---|
| scheduled | predixa | `Markets go quiet for a moment,` | `then open again.` |
| scheduled | tmx | `Routing pauses for planned work,` | `funds stay put.` |
| underway | predixa | `Trading is paused while we work,` | `positions are safe.` |
| underway | tmx | `Swaps are paused while we work,` | `nothing is at risk.` |
| restored | predixa | `Maintenance is finished,` | `markets are open.` |
| restored | tmx | `Maintenance is finished,` | `swaps are live.` |

Write time ranges as `02:00 to 04:00 UTC`, not with a dash: the card's mono zones
are narrow and a dash reads as a hyphenated word at card size.

**Getting the PNG to the user** depends on the surface you are answering in:

- **A chat surface that can send files** (a Telegram or Discord session): send
  the PNG into the chat as an image, so it is one forward away from the channel.
  Use whatever your runtime actually offers for this. If it offers nothing, say
  so and fall back to the path. Never report a card as sent when only the file
  exists.
- **Hermes Telegram lossless-delivery rule:** apply this only when the current
  runtime is a Hermes Telegram chat and the agent itself is uploading the card
  into that chat. Include the literal `[[as_document]]` directive in the same
  response as the `MEDIA:` path so Hermes routes the untouched full-resolution
  PNG through Telegram `sendDocument`, never a native photo bubble. The directive
  applies to every media path in that response, so do not mix preview-only images
  into the same delivery. Do not resize or ZIP the PNG unless the user explicitly
  asks for an alternate format. **Do not emit `[[as_document]]` or `MEDIA:` in
  Claude Code, a plain terminal, or any non-Hermes runtime:** those surfaces do
  not deliver the attachment; follow the terminal rule below and print the
  absolute PNG path instead.
- **A terminal** (Claude Code, plain CLI): print the **absolute** path, since the
  user picks it in a file dialog. Step 5 says where that line goes.

The Vale gate in step 4 covers the **message prose only**. Card copy is design,
not prose; `card.py`'s budgets are its check.

If the templates are missing, `card.py` prints the one command that regenerates
them. They are built from a single design master in X-Workflow, so this skill's
copies and that repo's never drift.

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
when something needs action: an over-limit split, unresolved Vale alerts, or a
card from step 4b. Those lines go **above** both sections and never inside a
message: `Attach: <absolute path>` on a terminal, or `Attached above.` when you
sent the PNG into the chat.

### Links, images, code in the source
- **URLs** → Discord `[label](url)`; Telegram bare URL.
- **Images** → neither renders inline markdown images; list them as URLs.
- **Code** → Discord fenced block; Telegram inline code or a short fenced block.
