#!/usr/bin/env python3
r"""card — render the maintenance status card that goes with a lede broadcast.

  python card.py --brand predixa --design station-rail --state underway \
      --fields copy.json --out /tmp/maintenance.png
  python card.py --selftest

Fills a fixed 1600x600 template from `<skill-dir>/cards/` and renders a 2x PNG
(3200x1200) with the headless browser it finds. The PNG is an ATTACHMENT: the
user picks it in Discord/Telegram's file picker, it is never pasted.

Copy arrives as a JSON object in `--fields`, never as inline arguments — same
rule as lede.py, so text containing `$(...)`, backticks or `;` can't reach the
shell. Values are HTML-escaped before they touch the template.

  --design status-plate   two big times on a wash panel. Best for the notice.
      fields: HEADLINE FOIL TIME_START TIME_END
  --design station-rail   a three-stop timeline. Best for underway/restored.
      fields: HEADLINE FOIL TIME_NOTICE TIME_WINDOW TIME_RESTORED

Every field is required and budgeted: each zone always renders, so blank or
over-long copy fails the run rather than shipping a broken card. The one
exception is TIME_START when --state restored, which has no zone in that state.

Pure stdlib. Browser override via $CARD_BROWSER (point it at the executable).
Upstream of the templates and of find_browser/render_png below:
X-Workflow/tools/{build_card_template,make_card}.py — the templates are
generated there from one design master, so both copies stay identical.
"""
import argparse
import glob
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS_DIR = os.path.join(SKILL_DIR, "cards")
TOKEN_RE = re.compile(r"\{\{([A-Z_0-9]+)\}\}")
BRACE_RE = re.compile(r"\{\{[^{}]*\}\}")

BRANDS = ("predixa", "tmx")
STATES = ("scheduled", "underway", "restored")

# Char budget per zone, measured on max-fill renders. The time zones are
# monospaced so the budget is exact; HEADLINE/FOIL are Inter and wrap to two
# lines. Over-budget copy bleeds out of its box instead of clipping.
SPECS = {
    "status-plate": {"HEADLINE": 40, "FOIL": 28, "TIME_START": 15, "TIME_END": 15},
    "station-rail": {"HEADLINE": 40, "FOIL": 28, "TIME_NOTICE": 22,
                     "TIME_WINDOW": 22, "TIME_RESTORED": 22},
}

# The card's own words, per brand and state — what the design ships. Use them
# unless the incident needs something more specific; the prose in the broadcast
# should say the same thing as the card.
COPY = {
    ("status-plate", "predixa", "scheduled"): ("Markets go quiet for a moment,", "then open again."),
    ("status-plate", "tmx", "scheduled"): ("Routing pauses for planned work,", "funds stay put."),
    ("status-plate", "predixa", "underway"): ("Trading is paused while we work,", "positions are safe."),
    ("status-plate", "tmx", "underway"): ("Swaps are paused while we work,", "nothing is at risk."),
    ("status-plate", "predixa", "restored"): ("Maintenance is finished,", "markets are open."),
    ("status-plate", "tmx", "restored"): ("Maintenance is finished,", "swaps are live."),
}
for _b, _s in [(b, s) for b in BRANDS for s in STATES]:
    COPY[("station-rail", _b, _s)] = COPY[("status-plate", _b, _s)]


def check_spec(design, state, fields):
    """Hard-fail on copy that would render a blank or overflowing card zone."""
    problems = []
    for tok in sorted(SPECS[design]):
        # The plate's restored panel reads "Back online" (TIME_END) then a fixed
        # "All normal" — TIME_START has no zone there.
        if tok == "TIME_START" and state == "restored":
            continue
        v = str(fields.get(tok, "")).strip()
        if not v:
            problems.append("%s is empty, but that zone always renders on the "
                            "card. Give it real copy." % tok)
        elif len(v) > SPECS[design][tok]:
            problems.append("%s is %d chars, max %d before it overflows - shorten it"
                            % (tok, len(v), SPECS[design][tok]))
    if problems:
        raise ValueError("card copy does not fit %s:\n  %s"
                         % (design, "\n  ".join(problems)))


def fill(template, state, fields):
    """Fill {{TOKEN}}s with escaped values. STATE is whitelisted separately: it
    lands inside a CSS attribute selector in a <style> block, and escaping cannot
    secure that. A raw newline is not an HTML metacharacter, so html.escape()
    passes it through, and CSS ends the string early on it however the quotes
    were escaped. Only the whitelist stops the value becoming live CSS."""
    if state not in STATES:
        raise ValueError("state must be one of %s, got %r" % (", ".join(STATES), state))
    bad = sorted({t for t in BRACE_RE.findall(template) if not TOKEN_RE.fullmatch(t)})
    if bad:
        raise ValueError("template has malformed tokens: %s" % ", ".join(bad))
    values = dict(fields, STATE=state)

    # Single pass over the ORIGINAL template, so a value containing "{{X}}" can
    # never bleed into another field.
    def repl(m):
        name = m.group(1)
        if name not in values:
            raise ValueError("no value for template token {{%s}}" % name)
        return html.escape(str(values[name]))

    return TOKEN_RE.sub(repl, template)


BROWSER_NAMES = ["msedge", "chrome", "chromium", "chromium-browser",
                 "google-chrome", "google-chrome-stable", "microsoft-edge",
                 "microsoft-edge-stable"]


def _platform_candidates():
    """OS-conventional install locations, derived from registry/env, never from a
    literal drive path."""
    if sys.platform == "win32":
        try:
            import winreg
            app_paths = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
            for exe in ("msedge.exe", "chrome.exe"):
                for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    try:
                        with winreg.OpenKey(hive, app_paths + "\\" + exe) as k:
                            yield winreg.QueryValueEx(k, None)[0]
                    except OSError:
                        pass
        except ImportError:
            pass
        roots = (os.environ.get(v) for v in
                 ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"))
        for root in filter(None, roots):
            for rel in (r"Microsoft\Edge\Application\msedge.exe",
                        r"Google\Chrome\Application\chrome.exe",
                        r"Chromium\Application\chrome.exe"):
                yield os.path.join(root, rel)
    elif sys.platform == "darwin":
        for base in ("/Applications", os.path.expanduser("~/Applications")):
            yield base + "/Google Chrome.app/Contents/MacOS/Google Chrome"
            yield base + "/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            yield base + "/Chromium.app/Contents/MacOS/Chromium"


def _playwright_candidates():
    """Chromium from `playwright install chromium`, wherever its cache lives."""
    if sys.platform == "win32":
        cache = os.path.join(os.environ.get("LOCALAPPDATA", ""), "ms-playwright")
    elif sys.platform == "darwin":
        cache = os.path.expanduser("~/Library/Caches/ms-playwright")
    else:
        cache = os.path.expanduser("~/.cache/ms-playwright")
    for pat in ("chromium-*/chrome-linux64/chrome",
                "chromium-*/chrome-linux/chrome",
                "chromium-*/chrome-win64/chrome.exe",
                "chromium-*/chrome-win/chrome.exe",
                "chromium-*/chrome-mac/Chromium.app/Contents/MacOS/Chromium"):
        for p in sorted(glob.glob(os.path.join(cache, pat)), reverse=True):
            yield p                      # newest install first


def find_browser():
    env = os.environ.get("CARD_BROWSER")
    if env and os.path.isfile(env):
        return env
    for name in BROWSER_NAMES:
        p = shutil.which(name)
        if p:
            return p
    for c in _platform_candidates():
        if c and os.path.isfile(c):
            return c
    for c in _playwright_candidates():
        return c                         # glob only yields existing files
    return None


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError("not a PNG: %s" % path)
    return struct.unpack(">II", head[16:24])


def render_png(browser, html_path, png_path):
    if os.path.exists(png_path):
        os.remove(png_path)              # never accept a stale PNG as success
    # ignore_cleanup_errors: the detached Windows child (below) can still hold
    # the profile lockfile for a moment after the PNG lands.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        url = "file:///" + os.path.abspath(html_path).replace("\\", "/")
        cmd = [browser, "--headless=new", "--no-sandbox", "--disable-gpu",
               "--disable-dev-shm-usage",
               "--hide-scrollbars", "--force-device-scale-factor=2",
               "--window-size=1600,600",
               "--screenshot=" + os.path.abspath(png_path), url]
        if os.name == "nt":
            # Windows Edge/Chrome without an own profile dir quietly hand the
            # headless run off to an already-running browser instance and exit 0
            # WITHOUT writing the screenshot. A temp profile forces a real
            # headless process.
            cmd.insert(1, "--user-data-dir=" + os.path.join(profile, "udd"))
        # On POSIX isolate via a scratch $HOME instead: on some sandboxed hosts
        # an explicit --user-data-dir makes Chrome hang on a GCM registration
        # attempt during startup.
        env = dict(os.environ, HOME=profile)
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90, env=env)
        if r.returncode != 0:
            raise RuntimeError("browser render failed (exit %s).\nstderr:\n%s"
                               % (r.returncode, (r.stderr or "")[-1500:]))
        # Windows Edge: the launcher exits 0 immediately while a detached child
        # does the render, so the PNG can land seconds after subprocess.run
        # returns. Poll for a stable size instead of trusting the exit code.
        last = -1
        for _ in range(60):
            if os.path.exists(png_path):
                size = os.path.getsize(png_path)
                if size and size == last:
                    break
                last = size
            time.sleep(0.5)
        else:
            raise RuntimeError("browser exited 0 but wrote no stable PNG within "
                               "30s: %s\nstderr:\n%s"
                               % (png_path, (r.stderr or "")[-1500:]))
    w, h = png_size(png_path)
    if (w, h) != (3200, 1200):
        raise RuntimeError("unexpected PNG size %dx%d (want 3200x1200); render is wrong"
                           % (w, h))


def make(brand, design, state, fields, out_png):
    if brand not in BRANDS:
        raise ValueError("brand must be one of %s, got %r" % (", ".join(BRANDS), brand))
    if design not in SPECS:
        raise ValueError("design must be one of %s, got %r" % (", ".join(SPECS), design))
    tpl_path = os.path.join(CARDS_DIR, "%s-maintenance-%s.html" % (brand, design))
    if not os.path.exists(tpl_path):
        raise ValueError(
            "no template: %s\nThe maintenance cards are generated from the design "
            "master in X-Workflow; run\n  LEDE_SKILL_DIR=%s python tools/"
            "build_card_template.py --all\nthere to (re)write this skill's copy."
            % (tpl_path, SKILL_DIR))
    check_spec(design, state, fields)
    with open(tpl_path, encoding="utf-8") as f:
        filled = fill(f.read(), state, fields)

    out_png = os.path.abspath(out_png)
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    html_path = os.path.splitext(out_png)[0] + ".html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(filled)

    browser = find_browser()
    if not browser:
        raise ValueError(
            "No headless browser found. A PNG is required.\n"
            "Install Chrome/Edge/Chromium (PATH, registry, Program Files, and\n"
            "/Applications are searched automatically), or:\n"
            "  pip install playwright && playwright install chromium\n"
            "(its cache is auto-detected). $CARD_BROWSER overrides the search.")
    render_png(browser, html_path, out_png)
    return html_path, out_png


def selftest():
    tpl = ('<style>#card [data-when~="{{STATE}}"]{display:flex}</style>'
           '<h2>{{HEADLINE}} <em>{{FOIL}}</em></h2><b>{{TIME_END}}</b>')
    out = fill(tpl, "underway", {"HEADLINE": "A & B <x>", "FOIL": "y", "TIME_END": "z"})
    assert "{{" not in out, out
    assert "A &amp; B &lt;x&gt;" in out, out                  # escaping applied
    assert '[data-when~="underway"]' in out, out              # state reached the CSS

    # a value carrying another token is left verbatim, never re-substituted
    bleed = fill(tpl, "scheduled",
                 {"HEADLINE": "see {{TIME_END}}", "FOIL": "f", "TIME_END": "PWNED"})
    assert "see {{TIME_END}}" in bleed, bleed
    assert "PWNED" not in bleed.split("</h2>")[0], bleed

    for bad in ("Scheduled", "", 'x"] ,* {display:none!important} [x="',
                'x\n] ,* {display:none!important} [x'):
        try:
            fill(tpl, bad, {"HEADLINE": "h", "FOIL": "f", "TIME_END": "t"})
            raise AssertionError("should reject state %r" % bad)
        except ValueError as e:
            assert "state" in str(e), e
    try:
        fill("<i>{{ stateName }}</i>", "underway", {})
        raise AssertionError("should flag malformed token")
    except ValueError as e:
        assert "malformed" in str(e), e
    try:
        fill(tpl, "underway", {"HEADLINE": "h", "FOIL": "f"})
        raise AssertionError("should flag missing TIME_END")
    except ValueError as e:
        assert "TIME_END" in str(e), e

    plate = {"HEADLINE": "Trading is paused while we work,",
             "FOIL": "positions are safe.",
             "TIME_START": "02:00 UTC", "TIME_END": "04:00 UTC"}
    check_spec("status-plate", "underway", plate)
    check_spec("status-plate", "restored", dict(plate, TIME_START=""))  # no zone
    for k, bad_v in (("TIME_START", ""), ("TIME_END", "x" * 16), ("HEADLINE", "x" * 41)):
        try:
            check_spec("status-plate", "underway", dict(plate, **{k: bad_v}))
            raise AssertionError("should reject %s=%r" % (k, bad_v))
        except ValueError as e:
            assert k in str(e), e
    check_spec("station-rail", "restored",
               {"HEADLINE": "Maintenance is finished,", "FOIL": "swaps are live.",
                "TIME_NOTICE": "Posted 01 Aug", "TIME_WINDOW": "02:00 to 04:00 UTC",
                "TIME_RESTORED": "Complete"})

    # every shipped default fits its own budget
    for (design, brand, state), (head, foil) in COPY.items():
        assert len(head) <= SPECS[design]["HEADLINE"], (design, brand, state, head)
        assert len(foil) <= SPECS[design]["FOIL"], (design, brand, state, foil)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--brand", choices=BRANDS)
    ap.add_argument("--design", choices=sorted(SPECS))
    ap.add_argument("--state", choices=STATES)
    ap.add_argument("--fields", help="path to a JSON object of TOKEN:VALUE copy")
    ap.add_argument("--out", help="destination .png")
    args = ap.parse_args()

    if args.selftest:
        selftest()
        return
    for req in ("brand", "design", "state", "fields", "out"):
        if not getattr(args, req):
            ap.error("--%s is required" % req)

    try:
        with open(args.fields, encoding="utf-8") as f:
            fields = json.load(f)
        if not isinstance(fields, dict):
            raise ValueError("--fields must hold a JSON object of TOKEN:VALUE pairs")
        html_path, png_path = make(args.brand, args.design, args.state, fields, args.out)
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError,
            json.JSONDecodeError) as e:
        raise SystemExit("error: %s" % e)

    print("html: %s" % html_path)
    print("attach this PNG: %s" % png_path)


if __name__ == "__main__":
    main()
