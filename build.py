#!/usr/bin/env python3
"""Build the FDE Signal Scan static site from the edition archive.

Input:  editions/<YYYY-MM-DD>-edition-<NNN>.html  -- Claude artifact body fragments
        editions/<YYYY-MM-DD>-edition-<NNN>.md    -- markdown archive of the same edition

Output: _site/index.html              -- the newest edition
        _site/archive.html            -- list of every edition
        _site/editions/<stem>.html    -- each edition, standalone
        _site/editions/<stem>.md      -- markdown, copied verbatim

An artifact fragment has no <!doctype>/<html>/<head>/<body> -- the artifact host
adds those at publish time. GitHub Pages does not, so this wraps each fragment in
the equivalent skeleton and hoists its <title> and <link rel=stylesheet> into head.
"""

import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EDITIONS = ROOT / "editions"
OUT = ROOT / "_site"

STEM_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-edition-(\d+)$")
TITLE_RE = re.compile(r"<title>(.*?)</title>\s*", re.I | re.S)
LINK_RE = re.compile(r"<link\b[^>]*\brel=[\"']?stylesheet[\"']?[^>]*>\s*", re.I)

# Mirrors the artifact host's skeleton: charset + viewport, light/dark color-scheme,
# zero body margin, 14px system font on an off-white ground. Editions override most
# of this from their own <style>, but a fragment that relies on the default still works.
RESET = """  :root{color-scheme:light dark}
  body{margin:0;font:14px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;background:#f7f8f7;color:#15191b}
  @media (prefers-color-scheme:dark){body{background:#14181a;color:#e8edea}}
  img{max-width:100%}
  [hidden]{display:none!important}"""

# The bar inherits the edition's own custom properties where they exist, so it
# themes with the page instead of fighting it.
NAV_CSS = """  .sitebar{
    display:flex;gap:18px;align-items:baseline;flex-wrap:wrap;
    padding:10px 28px;
    border-bottom:1px solid var(--line,#dde3e0);
    background:var(--card,#fff);color:var(--muted,#5c6b67);
    font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12px;
    letter-spacing:.04em;text-transform:uppercase;
  }
  .sitebar b{color:var(--ink,#15191b);font-weight:600}
  .sitebar a{color:var(--muted,#5c6b67);text-decoration:none;border-bottom:1px solid transparent}
  .sitebar a:hover{color:var(--accent,#0f7b62);border-bottom-color:var(--accent,#0f7b62)}
  .sitebar .spacer{margin-left:auto}"""


def nav(prefix, current, edition_label):
    """prefix is the relative path back to the site root ('' or '../')."""
    def link(href, text, key):
        if key == current:
            return "<b>%s</b>" % text
        return '<a href="%s%s">%s</a>' % (prefix, href, text)

    return (
        '<nav class="sitebar">'
        "<b>FDE Signal Scan</b>"
        + link("index.html", "Latest", "latest")
        + link("archive.html", "Archive", "archive")
        + '<span class="spacer">%s</span>' % html.escape(edition_label)
        + "</nav>"
    )


def wrap(fragment, prefix, current, edition_label):
    """Turn an artifact body fragment into a standalone HTML document."""
    title = "FDE Signal Scan"
    m = TITLE_RE.search(fragment)
    if m:
        title = m.group(1).strip()
        fragment = TITLE_RE.sub("", fragment, count=1)

    links = LINK_RE.findall(fragment)
    fragment = LINK_RE.sub("", fragment)

    head = [
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        "<title>%s</title>" % html.escape(title),
    ]
    head.extend(link.strip() for link in links)
    head.append("<style>\n%s\n%s\n</style>" % (RESET, NAV_CSS))

    return (
        "<!doctype html>\n<html lang=\"en\">\n<head>\n"
        + "\n".join(head)
        + "\n</head>\n<body>\n"
        + nav(prefix, current, edition_label)
        + "\n"
        + fragment.lstrip()
        + "\n</body>\n</html>\n"
    )


def discover():
    """Every edition that has an HTML fragment, newest first."""
    found = []
    for path in sorted(EDITIONS.glob("*.html")):
        m = STEM_RE.match(path.stem)
        if not m:
            print("skip (unrecognised name): %s" % path.name, file=sys.stderr)
            continue
        date, number = m.group(1), int(m.group(2))
        found.append(
            {
                "stem": path.stem,
                "date": date,
                "number": number,
                "label": "Edition %03d - %s" % (number, date),
                "html": path,
                "md": path.with_suffix(".md"),
            }
        )
    found.sort(key=lambda e: (e["number"], e["date"]), reverse=True)
    return found


ARCHIVE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FDE Signal Scan - Archive</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500&display=swap">
<style>
  :root{color-scheme:light dark;--paper:#f5f7f6;--card:#fff;--ink:#15191b;--muted:#5c6b67;--line:#dde3e0;--accent:#0f7b62}
  @media (prefers-color-scheme:dark){:root{--paper:#14181a;--card:#1b2124;--ink:#e8edea;--muted:#9aa8a4;--line:#2e3937;--accent:#4fbf9f}}
%(nav_css)s
  *{box-sizing:border-box}
  body{margin:0;background:var(--paper);color:var(--ink);font-family:"IBM Plex Sans",system-ui,sans-serif;font-size:16px;line-height:1.6}
  .wrap{max-width:760px;margin:0 auto;padding:44px 28px 96px}
  h1{font-family:Archivo,system-ui,sans-serif;font-size:30px;margin:0 0 6px}
  .sub{color:var(--muted);font-size:14px;margin:0 0 34px}
  ul{list-style:none;padding:0;margin:0}
  li{border-top:1px solid var(--line);padding:16px 0;display:flex;gap:16px;align-items:baseline;flex-wrap:wrap}
  li a{color:var(--ink);font-weight:500;text-decoration:none;border-bottom:1px solid var(--accent)}
  li a:hover{color:var(--accent)}
  .date,.md{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:13px;color:var(--muted)}
  .md{margin-left:auto}
  .md a{color:var(--muted);border-bottom:1px solid var(--line)}
  .md a:hover{color:var(--accent);border-bottom-color:var(--accent)}
  .empty{color:var(--muted)}
</style>
</head>
<body>
%(nav)s
<div class="wrap">
<h1>Archive</h1>
<p class="sub">Every edition of the FDE Signal Scan, newest first.</p>
<ul>
%(rows)s
</ul>
</div>
</body>
</html>
"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "editions").mkdir(parents=True)
    # Serve the tree as-is; no Jekyll processing.
    (OUT / ".nojekyll").write_text("")

    editions = discover()
    if not editions:
        print("no editions found in %s" % EDITIONS, file=sys.stderr)

    rows = []
    for edition in editions:
        fragment = edition["html"].read_text(encoding="utf-8")
        page = wrap(fragment, "../", "edition", edition["label"])
        (OUT / "editions" / (edition["stem"] + ".html")).write_text(page, encoding="utf-8")

        md_cell = "&mdash;"
        if edition["md"].exists():
            shutil.copyfile(edition["md"], OUT / "editions" / (edition["stem"] + ".md"))
            md_cell = '<a href="editions/%s.md">markdown</a>' % edition["stem"]
        else:
            print("warning: no markdown for %s" % edition["stem"], file=sys.stderr)

        rows.append(
            '<li><span class="date">%s</span>'
            '<a href="editions/%s.html">Edition %03d</a>'
            '<span class="md">%s</span></li>'
            % (edition["date"], edition["stem"], edition["number"], md_cell)
        )

    if not rows:
        rows.append('<li class="empty">No editions published yet.</li>')

    # index.html is the newest edition, so the bare Pages URL is always current.
    if editions:
        newest = editions[0]
        fragment = newest["html"].read_text(encoding="utf-8")
        (OUT / "index.html").write_text(
            wrap(fragment, "", "latest", newest["label"]), encoding="utf-8"
        )
    else:
        (OUT / "index.html").write_text(
            ARCHIVE_TEMPLATE
            % {"nav_css": NAV_CSS, "nav": nav("", "latest", "no editions"), "rows": rows[0]},
            encoding="utf-8",
        )

    (OUT / "archive.html").write_text(
        ARCHIVE_TEMPLATE
        % {
            "nav_css": NAV_CSS,
            "nav": nav("", "archive", "%d edition%s" % (len(editions), "" if len(editions) == 1 else "s")),
            "rows": "\n".join(rows),
        },
        encoding="utf-8",
    )

    print("built %d edition(s) into %s" % (len(editions), OUT))


if __name__ == "__main__":
    build()
