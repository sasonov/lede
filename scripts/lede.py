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


def comparable_text(s):
    """Normalize platform markup so formatting-only clones compare as identical."""
    text = _MARKDOWN_LINK_RE.sub(r"\1", s)
    text = re.sub(r"(?m)^#{1,6}\s+", "", text)
    for marker in ("**", "__", "~~", "||", "`", "*"):
        text = text.replace(marker, "")
    text = re.sub(r"(?m)^\s*[-+•]\s+", "", text)
    return " ".join(text.lower().split())


def similarity(discord_text, telegram_text):
    return SequenceMatcher(None, comparable_text(discord_text), comparable_text(telegram_text)).ratio()


def validate(platform, s):
    errors = []
    if _MATH_ALNUM_RE.search(s):
        errors.append("Unicode mathematical alphanumeric glyphs are forbidden; use native bold")
    if _DOT_BULLET_RE.search(s):
        errors.append("dot bullets are forbidden; use literal '- ' list markers")
    if _NON_HYPHEN_BULLET_RE.search(s):
        errors.append("list markers must be literal '- ', not '*' or '+'")
    if any(line.count("**") % 2 for line in s.splitlines()):
        errors.append("unbalanced or cross-line ** bold markers")
    if re.search(r"\*\*\s*\*\*", s):
        errors.append("empty ** bold span")
    if platform == "telegram" and _TELEGRAM_HEADING_RE.search(s):
        errors.append("Telegram headings must use normal bold, not #/## heading markers")
    if platform == "telegram" and _HTML_TAG_RE.search(s):
        errors.append("Telegram output must use native bold source, not HTML tags")
    if platform == "telegram" and _MARKDOWN_LINK_RE.search(s):
        errors.append("Telegram links must be bare URLs, not masked Markdown links")
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
    assert validate("telegram", "**broken")
    assert validate("telegram", "**crosses\nlines**")
    assert validate("telegram", "* Item")
    assert validate("telegram", "<b>Title</b>")
    assert validate("telegram", "[Docs](https://example.com)")
    assert emoji_count("🚀 Text 🎯") == 2
    assert similarity("## **Same text**", "**Same text**") == 1.0
    assert similarity("Discord opens with the launch details.", "Telegram starts with a short user call to action.") < 0.7
    print("ok")


def _compare_args(argv):
    if len(argv) != 4 or argv[0] != "--discord-file" or argv[2] != "--telegram-file":
        raise ValueError("compare needs --discord-file PATH --telegram-file PATH")
    with open(argv[1], encoding="utf-8") as f:
        discord_text = f.read()
    with open(argv[3], encoding="utf-8") as f:
        telegram_text = f.read()
    ratio = similarity(discord_text, telegram_text)
    print(f"platform similarity: {ratio:.3f} (must be < 0.900)")
    substantial = min(len(comparable_text(discord_text)), len(comparable_text(telegram_text))) >= 200
    if substantial and ratio >= 0.900:
        print("ERROR: Discord and Telegram are near-identical; author separate platform messages", file=sys.stderr)
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
