#!/usr/bin/env bash
# Prepare an upstream source *snapshot for audit*, not a complete license offer.
set -euo pipefail

REV=c19416e75cbc15f9a27f7e967ee81cb108761e30
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_DIR="${1:-$HOME/freej2me-web-git-backup}"
OUT="${2:-$HOME/freej2me-web-source-snapshot-c19416e.tar.gz}"

if [[ ! -d "$GIT_DIR" ]]; then
  echo "Not found: $GIT_DIR" >&2
  echo 'Pass the path to the ORIGINAL freej2me-web .git directory as first argument.' >&2
  exit 1
fi
if [[ "$(git --git-dir="$GIT_DIR" rev-parse "$REV^{commit}")" != "$REV" ]]; then
  echo "Requested source commit $REV not found in $GIT_DIR" >&2
  exit 1
fi
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
mkdir -p "$TMP/freej2me-web-$REV" "$TMP/pop-mobile-adapters"
git --git-dir="$GIT_DIR" archive "$REV" | tar -xf - -C "$TMP/freej2me-web-$REV"
cp "$REPO_ROOT/server.py" "$TMP/pop-mobile-adapters/server.py"
cp "$REPO_ROOT/tools/build_pages.py" "$TMP/pop-mobile-adapters/build_pages.py"
cp "$REPO_ROOT/THIRD_PARTY_NOTICES.md" "$TMP/THIRD_PARTY_NOTICES.md"
cat > "$TMP/README-SOURCE-STATUS.txt" <<'EOF'
PoP Mobile source audit snapshot

Contents: the full upstream freej2me-web commit c19416e75cbc15f9a27f7e967ee81cb108761e30
plus PoP Mobile's build-time/runtime adapter scripts and notices.

THIS SNAPSHOT IS NOT YET VERIFIED AS COMPLETE CORRESPONDING SOURCE.
In particular, the FluidSynth and FFmpeg/x264 sources, source modifications,
license notices, and exact build dependency revisions must be checked against
the binary WebAssembly outputs. See docs/SOURCE_COMPLIANCE.md in PoP Mobile.

This archive must not be described as satisfying all GPL/LGPL obligations
without an audit and supplementation where required.
EOF
mkdir -p "$(dirname "$OUT")"
tar -czf "$OUT" -C "$TMP" .
sha256sum "$OUT"
echo "Created upstream source audit snapshot: $OUT"
