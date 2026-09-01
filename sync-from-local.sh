#!/bin/bash
# Commit and push any Signal Scan edition that has landed in editions/ but is not
# yet in git, then let GitHub Actions rebuild the site.
#
# The cloud scan pushes editions directly. This is the backstop for when that push
# fails or the cloud run never happened: the device-bound "Signal Scan local sync"
# routine drops editions into editions/, and this publishes whatever is new.
#
# This repo deliberately lives outside ~/Documents. macOS TCC refuses launchd agents
# access to Documents, Desktop and Downloads, so a job rooted there cannot even exec
# its own script. Everything this touches must stay under ~/signal-scan.
#
# It only ever adds. Nothing is overwritten or deleted, so an edition annotated by
# hand is safe.
#
# Installed as a launchd agent: ~/Library/LaunchAgents/com.odi.signalscan-sync.plist

set -uo pipefail

# launchd gives a minimal PATH; the git credential helper shells out to gh.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

REPO="${SIGNALSCAN_REPO:-$HOME/signal-scan}"
LOG="$REPO/.sync.log"

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }

# Keep the log from growing without bound.
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 2000 ]; then
  tail -n 500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

[ -d "$REPO/.git" ] || { log "ERROR not a git repo: $REPO"; exit 1; }
cd "$REPO" || exit 1

# Take whatever the cloud run pushed before deciding what is new, otherwise the
# push below collides with an edition that is already upstream.
if ! git pull --rebase --autostash --quiet 2>>"$LOG"; then
  log "ERROR git pull failed; leaving the tree alone"
  exit 1
fi

git add editions

count=$(git diff --cached --name-only -- editions | wc -l | tr -d ' ')
if [ "$count" -eq 0 ]; then
  log "in sync, nothing to publish"
  exit 0
fi

git diff --cached --name-only -- editions | while read -r f; do log "staged $f"; done

git -c user.name="Signal Scan local sync" \
    -c user.email="odiche.obiakarije@nice.com" \
    commit --quiet -m "Publish $count edition file(s) picked up locally" 2>>"$LOG"

if git push --quiet origin main 2>>"$LOG"; then
  log "pushed $count file(s); Pages will rebuild"
else
  log "ERROR push failed; commit is local and the next run will retry"
  exit 1
fi
