#!/usr/bin/env python3
"""Stamp the download page's single-source RELEASE block with real values.

The page (civia-ota/index.html) renders every version / size label from one
JS object `RELEASE`. This script refreshes that object (and the no-JS
fallback text) from the actual build artefacts, so the badges, the CTA
button and the release notes can never drift apart again.

Sources (all auto-detected, overrideable via CLI flags):
  apkVer  <- civia-android/app/src/main/AndroidManifest.xml  versionName
  otaVer  <- civia-ota/version.json  version
  apkSize <- Civia.apk byte size, in MiB (1024-based, 1 decimal, to match
             the historical "1.7 MB" label)

Called automatically by update-web.sh and build.sh on each release.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PAGE = os.path.join(HERE, "index.html")
MANIFEST = os.path.join(ROOT, "civia-android", "app", "src", "main", "AndroidManifest.xml")


def size_mib(nbytes):
    return "%.1f MB" % (nbytes / 1048576.0)


def detect(args):
    apk_ver = args.apk_ver
    if not apk_ver:
        m = re.search(r'android:versionName="([^"]+)"', open(MANIFEST).read())
        if not m:
            sys.exit("stamp-release: cannot read versionName from " + MANIFEST)
        apk_ver = m.group(1)

    ota_ver = args.ota_ver
    if not ota_ver:
        ota_ver = json.load(open(os.path.join(HERE, "version.json")))["version"]

    apk_size = args.apk_size
    if not apk_size:
        apk = args.apk
        if not os.path.exists(apk):
            sys.exit("stamp-release: APK not found: " + apk)
        apk_size = size_mib(os.path.getsize(apk))

    return apk_ver, ota_ver, apk_size


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apk-ver", help="override APK versionName")
    ap.add_argument("--ota-ver", help="override OTA version")
    ap.add_argument("--apk-size", help="override APK size label")
    ap.add_argument("--apk", default=os.path.join(HERE, "Civia.apk"),
                    help="APK path used to compute size")
    args = ap.parse_args()

    apk_ver, ota_ver, apk_size = detect(args)
    s = open(PAGE).read()

    # 1) the single source of truth
    block = re.search(r"var RELEASE = \{.*?\};", s, re.S)
    if not block:
        sys.exit("stamp-release: RELEASE block not found in " + PAGE)
    b = block.group(0)
    for key, val in (("apkVer", apk_ver), ("otaVer", ota_ver), ("apkSize", apk_size)):
        b, n = re.subn(r"(%s:\s*')[^']*(')" % key,
                       lambda m, v=val: m.group(1) + v + m.group(2), b, count=1)
        if n != 1:
            sys.exit("stamp-release: cannot set RELEASE." + key)
    s = s[:block.start()] + b + s[block.end():]

    # 2) no-JS fallback labels (kept in sync with RELEASE)
    labels = {
        "apkBadge": "APK v" + apk_ver,
        "otaBadge": "OTA v" + ota_ver,
        "sizeBadge": apk_size,
        "ctaMeta": "v" + apk_ver + " · " + apk_size,
    }
    for key, text in labels.items():
        pat = r'(data-rel="%s">)[^<]*(</span>)' % key
        s, n = re.subn(pat, lambda m, t=text: m.group(1) + t + m.group(2), s, count=1)
        if n != 1:
            sys.exit("stamp-release: cannot set fallback for " + key)

    open(PAGE, "w").write(s)
    print("stamp-release: APK v%s / OTA v%s / %s" % (apk_ver, ota_ver, apk_size))


if __name__ == "__main__":
    main()
