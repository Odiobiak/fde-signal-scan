# FDE Signal Scan

Archive and public site for the FDE Signal Scan, a tri-weekly research digest covering
MCP and agent protocols, voice AI, CCaaS, agent frameworks and observability, frontier
models and hardware, and two discovery lanes for emerging tools and new technique.

**Site:** https://odiobiak.github.io/fde-signal-scan/

## How it works

Anything that lands in `editions/` gets committed, pushed, and deployed. GitHub Actions
builds the site from the fragments; nothing generated is committed, so no two writers
can conflict over build output.

**Working now:** a launchd agent (`com.odi.signalscan-sync`, every 30 min plus at login)
runs `sync-from-local.sh`, which pulls, commits anything new in `editions/`, and pushes.
Actions then rebuilds and deploys. Drop an edition into `editions/` and it is live within
half an hour, no manual step.

**Not wired up yet:** the cloud **FDE Signal Scan** routine (Mon/Wed/Thu 06:30 ET) cannot
push here until the GitHub account is connected to Claude — the routine API rejects a
`git_repository` source with *"Connect your GitHub account before saving a routine that
uses a GitHub repository."* Until that is done, editions reach this repo only by being
placed in `editions/` by hand.

### Why this repo is not in ~/Documents

macOS TCC denies launchd agents access to `~/Documents`, `~/Desktop` and `~/Downloads` —
both exec and read. An agent rooted in Documents cannot even start its own script, and a
script elsewhere still cannot read Documents. So the drop point has to live outside those
folders, which is why this is `~/signal-scan` and not next to `~/Documents/AI_newsletter`.
The alternative would be granting Full Disk Access to `/bin/bash`, which is too broad.

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
