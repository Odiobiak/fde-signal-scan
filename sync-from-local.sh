#!/bin/bash
# Mirror new Signal Scan editions from the local sync folder into this repo and push.
#
# The cloud scan pushes editions directly. This is the backstop for when that push
# fails or the cloud run never happened: the device-bound "Signal Scan local sync"
# routine drops editions into $SRC, and this picks up anything the repo is missing.
#
# Copies only. It never overwrites a file already in editions/ and never deletes
# anything, so an edition Odi has annotated in either place is safe.
#
# Installed as a launchd agent: ~/Library/LaunchAgents/com.odi.signalscan-sync.plist

set -uo pipefail

# launchd gives a minimal PATH; the git credential helper shells out to gh.
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"

# Overridable so the script can be exercised against a scratch folder and clone.
SRC="${SIGNALSCAN_SRC:-$HOME/Documents/AI_newsletter}"
REPO="${SIGNALSCAN_REPO:-$HOME/Documents/fde-signal-scan}"
LOG="$REPO/.sync.log"

log() { printf '%s  %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" >> "$LOG"; }

# Keep the log from growing without bound.
if [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 2000 ]; then
  tail -n 500 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
fi

[ -d "$SRC" ]  || { log "ERROR source folder missing: $SRC"; exit 1; }
[ -d "$REPO/.git" ] || { log "ERROR not a git repo: $REPO"; exit 1; }

cd "$REPO" || exit 1

# Take whatever the cloud run pushed before deciding what is missing, otherwise we
# re-add editions that are already upstream and collide on push.
if ! git pull --rebase --autostash --quiet 2>>"$LOG"; then
  log "ERROR git pull failed; leaving the tree alone"
  exit 1
fi

copied=0
shopt -s nullglob
for src in "$SRC"/*.md "$SRC"/*.html; do
  name="$(basename "$src")"
  case "$name" in
    [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-edition-[0-9]*) ;;
    *) continue ;;                       # not an edition file
  esac
  [ -e "editions/$name" ] && continue    # already have it; never overwrite
  cp "$src" "editions/$name" && { log "added editions/$name"; copied=$((copied + 1)); }
done

if [ "$copied" -eq 0 ]; then
  log "in sync, nothing to add"
  exit 0
fi

git add editions
git -c user.name="Signal Scan local sync" \
    -c user.email="odiche.obiakarije@nice.com" \
    commit --quiet -m "Backfill $copied edition file(s) from local sync folder" 2>>"$LOG"

if git push --quiet origin main 2>>"$LOG"; then
  log "pushed $copied file(s); Pages will rebuild"
else
  log "ERROR push failed; commit is local and the next run will retry"
  exit 1
fi
