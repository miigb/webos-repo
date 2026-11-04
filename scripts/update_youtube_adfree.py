#!/usr/bin/env python3
"""
Automated Updater & Hover-Preview Patcher for YouTube AdFree (Universal Web)
============================================================================
Fetches the latest stable (or specified tag) Universal Web `_all.ipk` release from
NicholasBly/youtube-webos, automatically injects the LG webOS 6 Hover Video Previews
with Sound & Resume patch:
  1. Restores `_TV_O18/$firmwareVersion$` User-Agent and `"wolwowlan": true` in `appinfo.json`
  2. Patches `userScript.js` so `forcePreviews` defaults to `"force_on"` and writes a
     valid non-expiring `{data: true, creation, expiration}` envelope across all
     `yt.leanback.*::inline-playback-enabled` namespaces immediately on startup.
  3. Updates `/Users/miguelbrito/Downloads/Software/webOS/`, `webos-repo/packages/`,
     `webos-repo/manifests/`, `apps.json`, and `api/apps.json` with `?v=<sha256[:8]>`.
"""

import argparse
import glob
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request

REPO_DIR = "/Users/miguelbrito/Development/DS218/webos-repo"
DOWNLOADS_DIR = "/Users/miguelbrito/Downloads/Software/webOS"
RESTORE_SKILL_SH = "/Users/miguelbrito/Development/DS218/.agents/skills/restore-lg-tv/scripts/restore_tv.sh"
GLOBAL_SKILL_SH = os.path.expanduser("~/.gemini/config/skills/restore-lg-tv/scripts/restore_tv.sh")
DESKTOP_RESTORE_SH = "/Users/miguelbrito/Downloads/Software/webOS/restore-lg-tv.sh"


def fetch_release_info(tag=None):
    if tag:
        candidates = [tag, tag.lstrip("v"), f"v{tag.lstrip('v')}"]
        data = None
        for t in candidates:
            url = f"https://api.github.com/repos/NicholasBly/youtube-webos/releases/tags/{t}"
            req = urllib.request.Request(url, headers={"User-Agent": "DS218-Updater/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    break
            except Exception:
                continue
        if not data:
            raise RuntimeError(f"Could not find release tag {tag}")
    else:
        url = "https://api.github.com/repos/NicholasBly/youtube-webos/releases/latest"
        req = urllib.request.Request(url, headers={"User-Agent": "DS218-Updater/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    version = data["tag_name"].lstrip("v")
    for asset in data.get("assets", []):
        name = asset["name"]
        if name.endswith("_all.ipk") and "webOS22" not in name:
            return version, name, asset["browser_download_url"]
    raise RuntimeError(f"Could not find Universal Web *_all.ipk in release {data.get('tag_name')}")


def patch_ipk_bytes(raw_bytes):
    assert raw_bytes[:8] == b"!<arch>\n", "Invalid Debian ar header in IPK"
    pos = 8
    members = []
    while pos < len(raw_bytes):
        hdr = raw_bytes[pos : pos + 60]
        name = hdr[:16].decode("ascii").strip()
        size = int(hdr[48:58].decode("ascii").strip())
        pos += 60
        data = raw_bytes[pos : pos + size]
        if size % 2 == 1:
            pos += 1
        pos += size
        members.append((hdr, name, data))

    new_members = []
    for hdr, name, data in members:
        if name.startswith("data.tar.gz"):
            in_tar = tarfile.open(fileobj=io.BytesIO(data), mode="r:gz")
            out_buf = io.BytesIO()
            out_tar = tarfile.open(fileobj=out_buf, mode="w:gz", format=tarfile.GNU_FORMAT)
            for ti in in_tar.getmembers():
                fobj = in_tar.extractfile(ti) if ti.isfile() else None
                if ti.name.endswith("appinfo.json") and fobj is not None:
                    appinfo = json.loads(fobj.read().decode("utf-8"))
                    appinfo.setdefault("vendorExtension", {})[
                        "userAgent"
                    ] = "$browserName$/$browserVersion$ ($platformName$-$platformVersion$), _TV_O18/$firmwareVersion$ (LG, $modelName$, $networkMode$)"
                    appinfo["wolwowlan"] = True
                    b_new = (json.dumps(appinfo, indent=2) + "\n").encode("utf-8")
                    ti.size = len(b_new)
                    out_tar.addfile(ti, io.BytesIO(b_new))
                    print("[OK] Patched appinfo.json with _TV_O18 User-Agent and wolwowlan")
                elif ti.name.endswith("userScript.js") and fobj is not None:
                    s = fobj.read().decode("utf-8")
                    # 1. Default forcePreviews to force_on in schema if present
                    s = re.sub(
                        r'\["forcePreviews",\s*\{default:"disabled"',
                        '["forcePreviews",{default:"force_on"',
                        s,
                    )
                    # 2. Ensure any bare {data:t} inline-playback write includes creation/expiration
                    s = s.replace(
                        '"yt.leanback.default::inline-playback-enabled",JSON.stringify({data:t})',
                        '"yt.leanback.default::inline-playback-enabled",JSON.stringify({data:t,creation:Date.now(),expiration:Date.now()+31536e6})',
                    ).replace(
                        '"yt.leanback.default::inline-playback-enabled",{data:t}',
                        '"yt.leanback.default::inline-playback-enabled",{data:t,creation:Date.now(),expiration:Date.now()+31536e6}',
                    )
                    # 3. Prepend version-agnostic multi-profile hover preview bootstrap IIFE
                    preview_iife = (
                        '(function(){try{'
                        'var cfgRaw=localStorage.getItem("ytaf-configuration"),cfg=cfgRaw?JSON.parse(cfgRaw):{};'
                        'if(!cfg.forcePreviews||cfg.forcePreviews==="disabled"){cfg.forcePreviews="force_on";localStorage.setItem("ytaf-configuration",JSON.stringify(cfg))}'
                        'var en=cfg.forcePreviews!=="force_off";'
                        'function syncPreviews(){try{'
                        'var now=Date.now(),env=JSON.stringify({data:en,creation:now,expiration:now+31536e6}),prefixes={"yt.leanback.default::":!0};'
                        'for(var i=0;i<localStorage.length;i++){var k=localStorage.key(i);if(k&&0===k.indexOf("yt.leanback.")){var p=k.indexOf("::");p>0&&(prefixes[k.slice(0,p+2)]=!0)}}'
                        'Object.keys(prefixes).forEach(function(px){localStorage.setItem(px+"inline-playback-enabled",env)})'
                        '}catch(e){}}'
                        'syncPreviews();setTimeout(syncPreviews,1000);setTimeout(syncPreviews,2600);'
                        '}catch(e){}})();\n'
                    )
                    if "syncPreviews()" not in s:
                        s = preview_iife + s
                    b_new = s.encode("utf-8")
                    ti.size = len(b_new)
                    out_tar.addfile(ti, io.BytesIO(b_new))
                    print("[OK] Patched userScript.js with version-agnostic multi-profile hover previews")
                else:
                    out_tar.addfile(ti, fobj)
            out_tar.close()
            data = out_buf.getvalue()
            hdr = hdr[:48] + f"{len(data):<10}".encode("ascii") + hdr[58:]
        new_members.append((hdr, data))

    out = io.BytesIO()
    out.write(b"!<arch>\n")
    for hdr, data in new_members:
        out.write(hdr)
        out.write(data)
        if len(data) % 2 == 1:
            out.write(b"\n")
    return out.getvalue()


def main():
    parser = argparse.ArgumentParser(description="Update and patch YouTube AdFree Universal Web with Hover Previews")
    parser.add_argument("--tag", help="Specific release tag (default: latest stable)")
    parser.add_argument("--install", action="store_true", help="Install onto LG TV after patching")
    parser.add_argument("--push", action="store_true", help="Commit and push webos-repo to GitHub")
    args = parser.parse_args()

    version, filename, download_url = fetch_release_info(args.tag)
    print(f"Downloading {filename} (version {version}) from {download_url}...")
    req = urllib.request.Request(download_url, headers={"User-Agent": "DS218-Updater/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw_ipk = resp.read()

    patched_ipk = patch_ipk_bytes(raw_ipk)
    sha256 = hashlib.sha256(patched_ipk).hexdigest()
    h8 = sha256[:8]
    size = len(patched_ipk)

    for dest_dir in [DOWNLOADS_DIR, f"{REPO_DIR}/packages"]:
        os.makedirs(dest_dir, exist_ok=True)
        with open(f"{dest_dir}/{filename}", "wb") as f:
            f.write(patched_ipk)

    slug = version.replace(".", "-")
    manifest_name = f"youtube-leanback-v4-universal-{slug}.manifest.json"
    icon_name = f"youtube.leanback.v4_{version}_all.png"
    src_icon = f"{REPO_DIR}/icons/youtube.leanback.v4_0.8.4_all.png"
    dst_icon = f"{REPO_DIR}/icons/{icon_name}"
    if os.path.exists(src_icon) and not os.path.exists(dst_icon):
        shutil.copyfile(src_icon, dst_icon)

    manifest_obj = {
        "id": "youtube.leanback.v4",
        "version": version,
        "type": "web",
        "title": f"YouTube AdFree (Universal Web v{version})",
        "appDescription": f"Working Universal Web release (v{version}) for LG webOS 3.0-6.0 with Hover Video Previews (Sound & Resume), AdBlock, SponsorBlock, and webOS 6 Spatial Navigation speedups.",
        "iconUri": f"https://miigb.github.io/webos-repo/icons/{icon_name}",
        "sourceUrl": "https://github.com/NicholasBly/youtube-webos",
        "rootRequired": False,
        "ipkUrl": f"https://raw.githubusercontent.com/miigb/webos-repo/main/packages/{filename}?v={h8}",
        "ipkHash": {"sha256": sha256},
        "ipkSize": size,
    }
    with open(f"{REPO_DIR}/manifests/{manifest_name}", "w") as f:
        json.dump(manifest_obj, f, indent=2)

    for cpath in [f"{REPO_DIR}/apps.json", f"{REPO_DIR}/packages.json", f"{REPO_DIR}/api/apps.json", f"{REPO_DIR}/api/packages.json"]:
        with open(cpath, "r") as f:
            cat = json.load(f)
        for pkg in cat.get("packages", []):
            if pkg.get("manifest", {}).get("id") == "youtube.leanback.v4":
                pkg["id"] = f"youtube-leanback-v4-universal-{slug}"
                pkg["title"] = manifest_obj["title"]
                pkg["iconUri"] = manifest_obj["iconUri"]
                pkg["manifestUrl"] = f"https://miigb.github.io/webos-repo/manifests/{manifest_name}?v={h8}"
                pkg["manifest"] = manifest_obj
                pkg["shortDescription"] = f"Working Universal Web v{version} for webOS 3.0-6.0 (Hover Previews + AdBlock + SponsorBlock)"
        with open(cpath, "w") as f:
            json.dump(cat, f, indent=2)

    for sh_path in [RESTORE_SKILL_SH, GLOBAL_SKILL_SH, DESKTOP_RESTORE_SH]:
        if os.path.exists(sh_path):
            with open(sh_path, "r") as f:
                s = f.read()
            s2 = re.sub(r"youtube\.leanback\.v4_[0-9a-zA-Z._-]+_all\.ipk", filename, s)
            with open(sh_path, "w") as f:
                f.write(s2)

    print(f"[OK] Updated {filename} (size={size}, sha256={sha256})")

    if args.install:
        env = os.environ.copy()
        env["PATH"] = f"/opt/homebrew/bin:/usr/local/bin:{env.get('PATH', '')}"
        subprocess.run(["ares-install", "--device", "tv", f"{DOWNLOADS_DIR}/{filename}"], env=env, check=True)

    if args.push:
        subprocess.run(["git", "-C", REPO_DIR, "add", "-A"], check=True)
        subprocess.run(["git", "-C", REPO_DIR, "commit", "-m", f"Update YouTube AdFree Universal Web to v{version} with hover previews"], check=False)
        subprocess.run(["git", "-C", REPO_DIR, "push", "origin", "main"], check=True)


if __name__ == "__main__":
    main()
