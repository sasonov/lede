#!/usr/bin/env python3
"""lede — helpers for the lede skill (Discord + Telegram formatting).

  python lede.py bold  --file TG.txt             **marked** spans -> Unicode bold
  python lede.py count discord  --file D.txt       code-point length  (limit 2000)
  python lede.py count telegram --file T.txt       UTF-16 code units  (limit 4096)
  python lede.py --selftest

Pass content with `--file PATH` (write it there first) or pipe it on stdin —
NEVER as an inline argument, so untrusted text containing shell metacharacters
(`$(...)`, backticks, `;`, `|`) can never be interpreted by the shell.

`bold` transpiles spans wrapped in **double asterisks** (same as Discord bold) to
Unicode sans-serif bold and removes the asterisks — author the whole Telegram
message with **markers**, then run it once. Each span must be non-empty, on a
single line, and balanced; any malformed or leftover `**` marker makes `bold`
exit nonzero so the error can't ship silently. Text with no `**` passes through
unchanged. Only A-Z a-z 0-9 convert; emoji, punctuation, URLs pass through.
`count` prints "<platform>: <n>/<limit> OK|OVER" and exits 1 when OVER.
"""
import re
import sys

LIMITS = {"discord": 2000, "telegram": 4096}
# span content: non-empty, no '*' inside, no newline (spans don't cross lines).
_SPAN = re.compile(r"\*\*([^*\n]+?)\*\*")


def bold(s):
    out = []
    for c in s:
        o = ord(c)
        if 0x41 <= o <= 0x5A:      # A-Z
            out.append(chr(o - 0x41 + 0x1D5D4))
        elif 0x61 <= o <= 0x7A:    # a-z
            out.append(chr(o - 0x61 + 0x1D5EE))
        elif 0x30 <= o <= 0x39:    # 0-9
            out.append(chr(o - 0x30 + 0x1D7EC))
        else:
            out.append(c)
    return "".join(out)


def apply_bold(s):
    """Transpile **marked** spans to Unicode bold and strip the markers.
    Raises ValueError if any `**` survives — i.e. a marker was unmatched, empty,
    or tried to span a newline. Text with no markers returns unchanged."""
    result = _SPAN.sub(lambda m: bold(m.group(1)), s)
    if "**" in result:
        raise ValueError(
            "malformed bold marker(s) — each **span** must be non-empty, "
            "balanced, and on one line"
        )
    return result


def length(platform, s):
    if platform == "telegram":     # UTF-16 code units: astral chars cost 2
        return sum(2 if ord(c) > 0xFFFF else 1 for c in s)
    return len(s)                  # discord: code points


def _resolve(rest):
    """Text from `--file PATH`, else an inline literal, else stdin."""
    if rest[:1] == ["--file"]:
        if len(rest) < 2:
            sys.stderr.write("--file needs a path\n")
            sys.exit(2)
        with open(rest[1], encoding="utf-8") as f:
            return f.read()
    if rest:
        return rest[0]             # short, trusted literal only
    sys.stdin.reconfigure(encoding="utf-8")
    return sys.stdin.read()


def _selftest():
    assert all(ord(bold(chr(o))) - 0x1D5D4 == o - 0x41 for o in range(0x41, 0x5B))
    assert all(ord(bold(chr(o))) - 0x1D5EE == o - 0x61 for o in range(0x61, 0x7B))
    assert all(ord(bold(chr(o))) - 0x1D7EC == o - 0x30 for o in range(0x30, 0x3A))
    assert bold(" .:/!?-") == " .:/!?-"                     # non-alnum untouched
    assert apply_bold("a **b** c") == "a " + bold("b") + " c"   # span transpiled
    assert apply_bold("**a**\n**b**") == bold("a") + "\n" + bold("b")  # per-line spans
    assert apply_bold("no bold here") == "no bold here"     # no markers -> unchanged
    for bad in ("**unmatched", "a ****b", "**crosses\nlines**", "**a** stray **"):
        try:
            apply_bold(bad)
            raise AssertionError(f"malformed marker not rejected: {bad!r}")
        except ValueError:
            pass
    assert length("discord", "abc") == 3
    assert length("telegram", bold("ab")) == 4             # bold letters are 2 units
    print("ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # astral glyphs need UTF-8 (Windows)
    sys.stderr.reconfigure(encoding="utf-8")   # error text may contain non-ASCII too
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        _selftest()
    elif a[:1] == ["bold"]:
        try:
            sys.stdout.write(apply_bold(_resolve(a[1:])))
        except ValueError as e:
            sys.stderr.write(f"bold: {e}\n")
            sys.exit(1)
    elif a[:1] == ["count"] and len(a) >= 2 and a[1] in LIMITS:
        n = length(a[1], _resolve(a[2:]))
        ok = n <= LIMITS[a[1]]
        sys.stdout.write(f"{a[1]}: {n}/{LIMITS[a[1]]} {'OK' if ok else 'OVER'}\n")
        sys.exit(0 if ok else 1)
    else:
        sys.stderr.write(__doc__)
        sys.exit(2)
