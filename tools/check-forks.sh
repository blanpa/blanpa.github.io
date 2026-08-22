#!/usr/bin/env bash
# Detects forked theme layouts that upstream has changed since you forked them.
#
# Eight files under layouts/ override a file of the same path in
# themes/blowfish. Overriding is silent by design: when the submodule is
# bumped and upstream rewrites one of those files, the build stays green and
# your copy quietly becomes the old version. Nothing else in the repo notices.
#
# This records the hash of each theme original at the moment the fork was
# accepted, and compares on every run.
#
#   tools/check-forks.sh            # check — exits 1 on drift
#   tools/check-forks.sh --update   # accept the current theme state as the baseline
#
# Runs in CI (ci.yml), which is where it matters: Dependabot's monthly theme
# bump arrives as a pull request, and this is what turns "the theme changed"
# into "these two of your forks need re-reading".

set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

THEME=themes/blowfish/layouts
MANIFEST=tools/forks.sha256

if [ ! -d "$THEME" ]; then
  echo "check-forks: $THEME is missing — run 'git submodule update --init'." >&2
  exit 1
fi

# Every layout of ours that shadows a theme file, i.e. the actual forks.
# Extension hooks (extend-head, extend-footer, home/custom, comments) have no
# theme counterpart and never show up here.
list_forks() {
  git ls-files layouts | sed 's|^layouts/||' | while IFS= read -r rel; do
    [ -e "$THEME/$rel" ] && echo "$rel"
  done | sort
}

hash_of() { sha256sum "$THEME/$1" | cut -d' ' -f1; }

if [ "${1:-}" = "--update" ]; then
  {
    echo "# sha256 of the themes/blowfish original for each file we fork."
    echo "# Regenerate with: tools/check-forks.sh --update"
    list_forks | while IFS= read -r rel; do echo "$(hash_of "$rel")  $rel"; done
  } > "$MANIFEST"
  echo "check-forks: baseline written to $MANIFEST"
  exit 0
fi

if [ ! -f "$MANIFEST" ]; then
  echo "check-forks: no baseline yet — run 'tools/check-forks.sh --update'." >&2
  exit 1
fi

status=0
recorded=$(grep -v '^#' "$MANIFEST" | grep -v '^[[:space:]]*$')

# 1. A fork whose upstream original changed since the baseline.
while IFS= read -r line; do
  want=${line%% *}
  rel=${line##*  }
  if [ ! -e "$THEME/$rel" ]; then
    echo "check-forks: upstream DELETED $rel — layouts/$rel is now an orphan fork." >&2
    status=1
    continue
  fi
  got=$(hash_of "$rel")
  if [ "$want" != "$got" ]; then
    echo "check-forks: upstream CHANGED $rel since the fork was taken." >&2
    echo "             compare:  git diff --no-index $THEME/$rel layouts/$rel" >&2
    status=1
  fi
done <<< "$recorded"

# 2. A newly forked file that was never recorded.
while IFS= read -r rel; do
  grep -q "  $rel\$" "$MANIFEST" || {
    echo "check-forks: layouts/$rel forks a theme file but is not in the baseline." >&2
    status=1
  }
done < <(list_forks)

if [ $status -ne 0 ]; then
  cat >&2 <<'MSG'

Re-read the affected fork against the new upstream version, port anything you
want, then accept the new baseline:

    tools/check-forks.sh --update

MSG
else
  echo "check-forks: $(list_forks | wc -l) forks, all matching their recorded upstream version."
fi

exit $status
