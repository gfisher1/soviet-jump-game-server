#!/usr/bin/env sh
# Attach one or more files to the Gitea release for $TAG, creating the
# release if it does not exist yet. Idempotent: re-running a tag reuses the
# existing release and keeps already-uploaded assets.
#
# Required env: GITEA_URL, REPO (owner/name), TOKEN, TAG
# Usage: publish-release.sh <asset> [asset...]
set -eu

[ "$#" -ge 1 ] || { echo "usage: publish-release.sh <asset> [asset...]" >&2; exit 1; }

API="$GITEA_URL/api/v1/repos/$REPO"
AUTH="Authorization: token $TOKEN"

first_id() { grep -o '"id":[0-9]*' | head -1 | cut -d: -f2; }

BODY=$(printf '{"tag_name":"%s","name":"%s","body":"Automated release %s.\\n\\nAssets below may include a gzipped, `docker load`-able image tarball, for hosts that cannot reach the container registry.\\n\\nRegistry image: `git.gfi.sh/%s:%s`"}' \
  "$TAG" "$TAG" "$TAG" "$REPO" "$TAG")

# 1. create the release (if it already exists, look it up instead)
RID=$(curl -sS -X POST -H "$AUTH" -H "Content-Type: application/json" \
        --data "$BODY" "$API/releases" 2>/dev/null | first_id || true)
if [ -z "${RID:-}" ]; then
  RID=$(curl -fsS -H "$AUTH" "$API/releases/tags/$TAG" | first_id)
fi
echo "release id: $RID"

# 2. upload each asset (an existing asset of the same name is left as-is)
for ASSET in "$@"; do
  [ -f "$ASSET" ] || { echo "asset not found: $ASSET" >&2; exit 1; }
  NAME=$(basename "$ASSET")
  if curl -fsS -X POST -H "$AUTH" \
       -H "Content-Type: application/octet-stream" \
       --data-binary "@$ASSET" \
       "$API/releases/$RID/assets?name=$NAME" > /dev/null; then
    echo "uploaded $NAME"
  else
    echo "asset upload failed (already attached?) - leaving it as-is: $NAME"
  fi
done
