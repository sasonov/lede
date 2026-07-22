#!/usr/bin/env python3
"""Validate and count Discord/Telegram announcement drafts.

Usage:
  python lede.py check discord  --file discord.txt
  python lede.py check telegram --file telegram.txt
  python lede.py compare --discord-file discord.txt --telegram-file telegram.txt
  python lede.py count discord  --file discord.txt
  python lede.py count telegram --file telegram.txt
  python lede.py --selftest

Message text must be supplied with --file or stdin, never interpolated into a
shell command. Discord count measures raw message content. Telegram count first
removes supported formatting syntax and then measures rendered UTF-16 code units.
"""
import re
import sys
from difflib import SequenceMatcher

LIMITS = {"discord": 2000, "telegram": 4096}
_MATH_ALNUM_RE = re.compile(r"[\U0001D400-\U0001D7FF]")
_EM_DASH_RE = re.compile(r"—")
_DOT_BULLET_RE = re.compile(r"(?m)^\s*•\s+")
_NON_HYPHEN_BULLET_RE = re.compile(r"(?m)^\s*[+*]\s+")
_TELEGRAM_HEADING_RE = re.compile(r"(?m)^#{1,6}\s+")
_MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HTML_TAG_RE = re.compile(r"</?(?:b|strong|i|em|u|s|code|pre|a)(?:\s+[^>]*)?>", re.I)
_EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "]"
)
_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?", re.I)
_BOLD_LABEL_RE = re.compile(r"^\s*\*\*([^*]{2,60})\*\*(?::)?(?:\s+.*)?$")
_HEADING_LABEL_RE = re.compile(r"^\s*#{1,6}\s+(.{2,60})$")
_GENERIC_LABEL_RE = re.compile(
    r"^(?:what(?:'s| is)?\b|why\b|how\b|get ready\b|act now\b|do not wait\b|"
    r"watch for\b|if the\b|next steps?\b|what you need to do\b)",
    re.I,
)
_UNSUPPORTED_URGENCY_RE = re.compile(
    r"\b(?:act now|do not wait|cannot wait|do not miss your chance|"
    r"before it is too late|risk falling behind)\b",
    re.I,
)


def utf16_length(s):
    return sum(2 if ord(c) > 0xFFFF else 1 for c in s)


def _strip_paired(text, marker):
    if text.count(marker) % 2:
        return text
    return text.replace(marker, "")


def telegram_visible_text(s):
    """Approximate rendered Telegram text for the skill's supported syntax."""
    text = _MARKDOWN_LINK_RE.sub(r"\1", s)
    for marker in ("**", "__", "~~", "||", "`"):
        text = _strip_paired(text, marker)
    return text


def length(platform, s):
    if platform == "telegram":
        return utf16_length(telegram_visible_text(s))
    return len(s)


def emoji_count(s):
    """Return an approximate emoji accent count for editorial guidance."""
    return len(_EMOJI_RE.findall(s))


def whole_message_wrapper(s):
    """Detect wrappers that make the entire Telegram post copy as code/quote."""
    lines = s.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    nonblank = [line for line in lines if line.strip()]
    if not nonblank:
        return None
    opening = re.match(r"^\s*(`{3,}|~{3,})[^\n]*$", nonblank[0])
    if opening and re.match(rf"^\s*{re.escape(opening.group(1))}\s*$", nonblank[-1]):
        return "code fence"
    if all(re.match(r"^\s*>", line) for line in nonblank):
        return "blockquote"
    if all(line.startswith(("    ", "\t")) for line in nonblank):
        return "indented code block"
    return None


def comparable_text(s):
    """Normalize platform markup so formatting-only clones compare as identical."""
    text = _MARKDOWN_LINK_RE.sub(r"\1", s)
    text = re.sub(r"(?m)^#{1,6}\s+", "", text)
    for marker in ("**", "__", "~~", "||", "`", "*"):
        text = text.replace(marker, "")
    text = re.sub(r"(?m)^\s*[-+•]\s+", "", text)
    return " ".join(text.lower().split())


def similarity(discord_text, telegram_text):
    return SequenceMatcher(
        None,
        comparable_text(discord_text),
        comparable_text(telegram_text),
        autojunk=False,
    ).ratio()


def token_similarity(discord_text, telegram_text):
    left = set(_WORD_RE.findall(comparable_text(discord_text)))
    right = set(_WORD_RE.findall(comparable_text(telegram_text)))
    if not left and not right:
        return 1.0
    return len(left & right) / len(left | right)


def section_labels(s):
    labels = []
    for line in s.splitlines():
        match = _HEADING_LABEL_RE.match(line) or _BOLD_LABEL_RE.match(line)
        if match:
            label = re.sub(r"[^a-z0-9']+", " ", match.group(1).lower()).strip()
            if label:
                labels.append(label)
    return labels


def structural_errors(s):
    errors = []
    generic = [label for label in section_labels(s) if _GENERIC_LABEL_RE.search(label)]
    if len(generic) >= 3:
        errors.append("formulaic generic-label stack; use prose-first structure or fact-specific labels")
    if _UNSUPPORTED_URGENCY_RE.search(s):
        errors.append("unsupported urgency language; state the sourced deadline or consequence directly")
    return errors


def validate(platform, s):
    errors = structural_errors(s)
    if _MATH_ALNUM_RE.search(s):
        errors.append("Unicode mathematical alphanumeric glyphs are forbidden; use native bold")
    if _EM_DASH_RE.search(s):
        errors.append("em dashes are forbidden; use a comma, colon, semicolon, period, or parentheses")
    if _DOT_BULLET_RE.search(s):
        errors.append("dot bullets are forbidden; use literal '- ' list markers")
    if _NON_HYPHEN_BULLET_RE.search(s):
        errors.append("list markers must be literal '- ', not '*' or '+'")
    if any(line.count("**") % 2 for line in s.splitlines()):
        errors.append("unbalanced or cross-line ** bold markers")
    if re.search(r"\*\*[ \t]*\*\*", s):
        errors.append("empty ** bold span")
    if platform == "telegram" and _TELEGRAM_HEADING_RE.search(s):
        errors.append("Telegram headings must use normal bold, not #/## heading markers")
    if platform == "telegram" and _HTML_TAG_RE.search(s):
        errors.append("Telegram output must use native bold source, not HTML tags")
    if platform == "telegram" and _MARKDOWN_LINK_RE.search(s):
        errors.append("Telegram links must be bare URLs, not masked Markdown links")
    if platform == "telegram" and (wrapper := whole_message_wrapper(s)):
        errors.append(f"Telegram output must be ordinary rendered text, not a whole-message {wrapper}")
    return errors


def _resolve(rest):
    if rest[:1] == ["--file"]:
        if len(rest) != 2:
            raise ValueError("--file needs exactly one path")
        with open(rest[1], encoding="utf-8") as f:
            return f.read()
    if rest:
        raise ValueError("pass message text via --file or stdin, not an inline argument")
    return sys.stdin.read()


def _report(platform, text, *, validate_first):
    errors = validate(platform, text) if validate_first else []
    n = length(platform, text)
    limit = LIMITS[platform]
    status = "OK" if n <= limit else "OVER"
    print(f"{platform}: {n}/{limit} {status}")
    if validate_first:
        print(f"emoji accents: {emoji_count(text)} (typical target: 2-4)")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 0 if status == "OK" and not errors else 1


def _selftest():
    assert utf16_length("a🚀") == 3
    assert telegram_visible_text("**Bold** - item") == "Bold - item"
    assert length("telegram", "**Bold** 🚀") == utf16_length("Bold 🚀")
    assert length("discord", "**Bold** 🚀") == len("**Bold** 🚀")
    assert validate("telegram", "**Title**\n\n- Item") == []
    assert validate("discord", "## 🚀 Title\n\n- Item") == []
    assert validate("telegram", "## Title")
    assert validate("telegram", "• Item")
    assert validate("telegram", "𝗕𝗼𝗹𝗱")
    assert validate("telegram", "Label — text")
    assert validate("discord", "Label — text")
    assert validate("telegram", "**broken")
    assert validate("telegram", "**crosses\nlines**")
    assert validate("telegram", "* Item")
    assert validate("telegram", "<b>Title</b>")
    assert validate("telegram", "[Docs](https://example.com)")
    assert validate("telegram", "```text\n**Title**\n\n- Item\n```")
    assert validate("telegram", "> **Title**\n>\n> - Item")
    assert validate("telegram", "    **Title**\n\n    - Item")
    assert validate("telegram", "**Title**\n\n`short code`\n\n- Item") == []
    assert validate("telegram", "**What changed**\nFact.\n\n**Why it matters**\nFiller.\n\n**What's next**\nMore filler.")
    assert validate("discord", "## Act now\nDo not wait before it is too late.")
    assert emoji_count("🚀 Text 🎯") == 2
    assert similarity("## **Same text**", "**Same text**") == 1.0
    assert similarity("Discord opens with the launch details.", "Telegram starts with a short user call to action.") < 0.7
    assert token_similarity("One shared fixed fact", "One shared fixed fact") == 1.0
    print("ok")


def _compare_args(argv):
    if len(argv) != 4 or argv[0] != "--discord-file" or argv[2] != "--telegram-file":
        raise ValueError("compare needs --discord-file PATH --telegram-file PATH")
    with open(argv[1], encoding="utf-8") as f:
        discord_text = f.read()
    with open(argv[3], encoding="utf-8") as f:
        telegram_text = f.read()
    left = comparable_text(discord_text)
    right = comparable_text(telegram_text)
    char_ratio = similarity(discord_text, telegram_text)
    token_ratio = token_similarity(discord_text, telegram_text)
    labels_left = section_labels(discord_text)
    labels_right = section_labels(telegram_text)
    print(f"platform character similarity: {char_ratio:.3f}")
    print(f"platform token similarity: {token_ratio:.3f}")
    errors = []
    minimum = min(len(left), len(right))
    if minimum >= 40 and left == right:
        errors.append("Discord and Telegram are identical after formatting is removed")
    elif minimum >= 80 and max(char_ratio, token_ratio) >= 0.860:
        errors.append("Discord and Telegram are near-identical; author separate platform messages")
    if len(labels_left) >= 3 and labels_left == labels_right:
        errors.append("Discord and Telegram reuse the same multi-section information architecture")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    return 0


def main(argv):
    if argv == ["--selftest"]:
        _selftest()
        return 0
    if len(argv) >= 2 and argv[0] in {"check", "count"} and argv[1] in LIMITS:
        try:
            text = _resolve(argv[2:])
        except (OSError, ValueError) as exc:
            print(f"lede: {exc}", file=sys.stderr)
            return 2
        return _report(argv[1], text, validate_first=argv[0] == "check")
    if argv[:1] == ["compare"]:
        try:
            return _compare_args(argv[1:])
        except (OSError, ValueError) as exc:
            print(f"lede: {exc}", file=sys.stderr)
            return 2
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
