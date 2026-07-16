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
message with **markers**, then run it once. With no `**` it bolds the entire
input (single term). Only A-Z a-z 0-9 convert; emoji, punctuation, URLs pass
through. `count` prints "<platform>: <n>/<limit> OK|OVER" and exits 1 when OVER.
"""
import re
import sys

LIMITS = {"discord": 2000, "telegram": 4096}
_SPAN = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


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
    # **marked** spans -> bold (markers stripped); no markers -> bold whole string.
    return _SPAN.sub(lambda m: bold(m.group(1)), s) if "**" in s else bold(s)


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
    assert apply_bold("a **b** c") == "a " + bold("b") + " c"   # markers transpiled
    assert apply_bold("plain") == bold("plain")                 # no markers -> whole
    assert length("discord", "abc") == 3
    assert length("telegram", bold("ab")) == 4             # bold letters are 2 units
    print("ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # astral glyphs need UTF-8 (Windows)
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        _selftest()
    elif a[:1] == ["bold"]:
        sys.stdout.write(apply_bold(_resolve(a[1:])))
    elif a[:1] == ["count"] and len(a) >= 2 and a[1] in LIMITS:
        n = length(a[1], _resolve(a[2:]))
        ok = n <= LIMITS[a[1]]
        sys.stdout.write(f"{a[1]}: {n}/{LIMITS[a[1]]} {'OK' if ok else 'OVER'}\n")
        sys.exit(0 if ok else 1)
    else:
        sys.stderr.write(__doc__)
        sys.exit(2)
