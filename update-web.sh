#!/bin/bash
# Regenerate the online web bundle + version.json for OTA hot update.
#
# Usage:
#   ./update-web.sh 1.0.2 https://your.host/ota
#
#   arg1 = new WEB_VERSION (must be greater than the current one)
#   arg2 = the public base URL where this civia-ota directory is hosted
#          (no trailing slash)
set -e
VER="${1:?usage: ./update-web.sh <version> <base-url>}"
BASE="${2:?usage: ./update-web.sh <version> <base-url>}"
BASE="${BASE%/}"
case "$BASE" in
  */version.json) BASE="${BASE%/version.json}" ;;
esac
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$HERE/../civia-app"

rm -rf "$HERE/www"
mkdir -p "$HERE/www"
cp "$APP/index.html" "$HERE/www/"
cp -R "$APP/assets" "$HERE/www/assets"

# Stamp the new version AND the FULL manifest url (base + /version.json).
# Two things are CRITICAL here:
#   1. A leftover __UPDATE_URL__ placeholder means the hot-applied bundle can
#      never check for updates again.
#   2. Stamping only the bare base url made the native checkUpdate fetch the
#      download page (HTML) and fail with "<!DOCTYPE ... cannot be converted".
python3 - "$HERE/www/index.html" "$VER" "$BASE" <<'PY'
import sys, re
p, ver, base = sys.argv[1], sys.argv[2], sys.argv[3]
u = base.strip().rstrip('/') + '/version.json'
s = open(p).read()
s = re.sub(r"const WEB_VERSION = '[\d.]+';", "const WEB_VERSION = '" + ver + "';", s, count=1)
s = s.replace('__UPDATE_URL__', u)
assert "const WEB_VERSION = '" + ver + "';" in s, "WEB_VERSION stamp not found"
assert "const UPDATE_URL = '" + u + "';" in s, "UPDATE_URL must be the full version.json url"
assert '__UPDATE_URL__' not in s, "UPDATE_URL placeholder left in bundle"
open(p, 'w').write(s)
PY

cd "$HERE/www" && rm -f "$HERE/web.zip" && zip -qr "$HERE/web.zip" index.html assets

cat > "$HERE/version.json" <<EOF
{
  "version": "$VER",
  "url": "$BASE/web.zip",
  "notes": "在线热更新"
}
EOF

echo "OK: web.zip + version.json regenerated for v$VER"
echo "    upload civia-ota/ to $BASE (index.html, version.json, web.zip, Civia.apk)"
