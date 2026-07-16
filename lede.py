#!/usr/bin/env python3
"""lede — helpers for the dispatch/lede skill.

  python lede.py bold "August 1"          ASCII -> Unicode sans-serif bold
  python lede.py count discord  "<msg>"   code-point length  (limit 2000)
  python lede.py count telegram "<msg>"   UTF-16 code units  (limit 4096)
  python lede.py --selftest

`count` prints "<platform>: <n>/<limit> OK|OVER" and exits 1 when OVER, so it can
gate a message before you send it. Text may be an argument or piped on stdin.
In bold, only A-Z a-z 0-9 convert; emoji, punctuation, and URLs pass through.
"""
import sys

LIMITS = {"discord": 2000, "telegram": 4096}


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


def length(platform, s):
    if platform == "telegram":     # UTF-16 code units: astral chars cost 2
        return sum(2 if ord(c) > 0xFFFF else 1 for c in s)
    return len(s)                  # discord: code points


def _read(arg):
    if arg is not None:
        return arg
    sys.stdin.reconfigure(encoding="utf-8")
    return sys.stdin.read()


def _selftest():
    assert all(ord(bold(chr(o))) - 0x1D5D4 == o - 0x41 for o in range(0x41, 0x5B))
    assert all(ord(bold(chr(o))) - 0x1D5EE == o - 0x61 for o in range(0x61, 0x7B))
    assert all(ord(bold(chr(o))) - 0x1D7EC == o - 0x30 for o in range(0x30, 0x3A))
    assert bold(" .:/!?-") == " .:/!?-"            # non-alphanumerics untouched
    assert length("discord", "abc") == 3
    assert length("telegram", bold("ab")) == 4     # bold letters are 2 units each
    print("ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # astral glyphs need UTF-8 (Windows)
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        _selftest()
    elif a[:1] == ["bold"]:
        sys.stdout.write(bold(_read(a[1] if len(a) > 1 else None)))
    elif a[:1] == ["count"] and len(a) >= 2 and a[1] in LIMITS:
        n = length(a[1], _read(a[2] if len(a) > 2 else None))
        ok = n <= LIMITS[a[1]]
        sys.stdout.write(f"{a[1]}: {n}/{LIMITS[a[1]]} {'OK' if ok else 'OVER'}\n")
        sys.exit(0 if ok else 1)
    else:
        sys.stderr.write(__doc__)
        sys.exit(2)
