# FDE Signal Scan

Archive and public site for the FDE Signal Scan, a tri-weekly research digest covering
MCP and agent protocols, voice AI, CCaaS, agent frameworks and observability, frontier
models and hardware, and two discovery lanes for emerging tools and new technique.

**Site:** https://odiobiak.github.io/fde-signal-scan/

## How it works

Two scheduled Claude agents write into `editions/`; GitHub Actions builds and deploys
the site. Nothing generated is committed, so the two agents can never conflict over
build output.

| | Runs | Writes |
|---|---|---|
| **FDE Signal Scan** (cloud) | Mon/Wed/Thu 06:30 ET | `editions/<stem>.html` + `.md`, pushed right after publishing |
| **Signal Scan local sync** (this Mac) | 09:00 and 16:00 weekdays | backfills any edition the cloud run missed |

The local sync is a catch-up job: it reconciles whatever is absent and does nothing
when the archive is already complete. A missed run self-heals on the next one.

## Layout

```
editions/
  YYYY-MM-DD-edition-NNN.html   Claude artifact body fragment, saved verbatim
  YYYY-MM-DD-edition-NNN.md     full edition as markdown
build.py                        wraps fragments into standalone pages, builds the index
.github/workflows/pages.yml     builds on push to main, deploys to Pages
```

An artifact fragment starts at `<title>` with no `<!doctype>`, `<html>`, `<head>` or
`<body>` — the artifact host supplies those at publish time. `build.py` adds the
equivalent skeleton, hoists the fragment's `<title>` and stylesheet links into `<head>`,
and prepends a nav bar that inherits the edition's own CSS custom properties.

## Build locally

```sh
python3 build.py          # writes _site/
python3 -m http.server -d _site 8000
```

`_site/` is generated and gitignored.

## Adding an edition by hand

Drop both files into `editions/` using the `YYYY-MM-DD-edition-NNN` stem, commit, push.
The highest edition number becomes `index.html`. A `.html` with no matching `.md` still
builds; the archive row just omits the markdown link.
