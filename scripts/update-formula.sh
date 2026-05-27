#!/usr/bin/env bash
# Bump Formula/weave-viewer.rb (version + sha256) and refresh
# docs/feature-support.md from a published weave-v* release. Local equivalent of
# .github/workflows/bump-formula.yml — for manual/offline use. Does NOT commit.
#
# Usage:  scripts/update-formula.sh [weave-vX.Y.Z]   # default: latest release
set -euo pipefail

REPO_SLUG="kolore-org/homebrew-weave"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TAG="${1:-}"
if [ -z "$TAG" ]; then
  TAG="$(gh release list --repo "$REPO_SLUG" --limit 1 --json tagName --jq '.[0].tagName')"
fi
case "$TAG" in
  weave-v*) ;;
  *) echo "Tag '$TAG' is not a weave-v* release tag." >&2; exit 1 ;;
esac
VERSION="${TAG#weave-v}"
echo "Syncing formula to $TAG (version $VERSION)"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
gh release download "$TAG" --repo "$REPO_SLUG" \
  --pattern 'weave-viewer-cli-macos-arm64.tar.gz.sha256' \
  --pattern 'feature-support.md' \
  --dir "$TMP" --clobber
SHA="$(cut -d' ' -f1 < "$TMP/weave-viewer-cli-macos-arm64.tar.gz.sha256")"
[ -n "$SHA" ] || { echo "ERROR: empty sha256 from release asset" >&2; exit 1; }

F=Formula/weave-viewer.rb
# Portable in-place edit (BSD/macOS + GNU): rewrite via temp file.
# Bump version + sha256, and the weave-v<ver> path segment in the url in lockstep.
sed -e "s/^  version \".*\"/  version \"$VERSION\"/" \
    -e "s/^  sha256 \".*\"/  sha256 \"$SHA\"/" \
    -e "/^  url /s#weave-v[^/]*/#weave-v$VERSION/#" "$F" > "$F.tmp" && mv "$F.tmp" "$F"
grep -q "version \"$VERSION\"" "$F" && grep -q "sha256 \"$SHA\"" "$F" \
  && grep -q "weave-v$VERSION/" "$F" \
  || { echo "ERROR: formula substitution did not apply" >&2; exit 1; }

mkdir -p docs
cp "$TMP/feature-support.md" docs/feature-support.md

echo "Updated:"
echo "  $F  -> version $VERSION, sha256 $SHA"
echo "  docs/feature-support.md  <- $TAG asset"
echo "Review with 'git diff', then commit."
