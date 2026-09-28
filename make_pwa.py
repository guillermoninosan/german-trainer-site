#!/usr/bin/env python3
"""Build the deployable PWA into dist/ from index.template.html + trainer-src/data.json
(+ firebase_config.json, once Guille has created his Firebase project - see README.md).

Run this instead of make_artifact.py when publishing the standalone installable app.
Usage: python3 make_pwa.py
Output: dist/  (index.html, manifest.json, service-worker.js, icons/, favicon.png)
        -> zip it and drag-and-drop onto Netlify, or push it to the chosen host.
"""
import hashlib
import json
import re
import shutil
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE.parent / "trainer-src"
DIST = HERE / "dist"

tpl = (HERE / "index.template.html").read_text(encoding="utf8")
data = json.loads((SRC / "data.json").read_text(encoding="utf8"))

cfg_path = HERE / "firebase_config.json"
if cfg_path.exists():
    fb_config = json.loads(cfg_path.read_text(encoding="utf8"))
else:
    fb_config = None
    print("NOTE: firebase_config.json not found - shipping with sync disabled "
          "(app still works, just device-local). See README.md to add it.")

assert "const DATA = /*__DATA__*/null;" in tpl, "index.template.html data placeholder not found"
js_data = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
tpl = tpl.replace("const DATA = /*__DATA__*/null;", "const DATA = " + js_data + ";")

fb_placeholder_re = re.compile(
    r"const FIREBASE_CONFIG = /\*__FIREBASE_CONFIG__\*/\{.*?\};", re.S
)
assert fb_placeholder_re.search(tpl), "index.template.html firebase config placeholder not found"
if fb_config:
    js_fb = json.dumps(fb_config, ensure_ascii=False, separators=(",", ":"))
    tpl = fb_placeholder_re.sub("const FIREBASE_CONFIG = " + js_fb + ";", tpl)
# else: leave the REPLACE_ME placeholder in place - initFirebase() detects it and
# gracefully runs in local-only (no sync) mode.

DIST.mkdir(exist_ok=True)
(DIST / "index.html").write_text(tpl, encoding="utf8")

# manifest.json + service-worker.js, with the cache version auto-bumped from a hash
# of this build's content, so every rebuild forces installed devices to refresh
# instead of serving a stale cached index.html forever - no manual "bump the version"
# step to remember.
digest = hashlib.sha256(tpl.encode("utf8")).hexdigest()[:10]
sw = (HERE / "service-worker.js").read_text(encoding="utf8")
sw = re.sub(r"const CACHE_VERSION = '.*?';", f"const CACHE_VERSION = 'v-{digest}';", sw)
(DIST / "service-worker.js").write_text(sw, encoding="utf8")

shutil.copy(HERE / "manifest.json", DIST / "manifest.json")
shutil.copy(HERE / "favicon.png", DIST / "favicon.png")
if (DIST / "icons").exists():
    shutil.rmtree(DIST / "icons")
shutil.copytree(HERE / "icons", DIST / "icons")

total = sum(f.stat().st_size for f in DIST.rglob("*") if f.is_file())
print(f"Built dist/ ({total / 1024:.1f} KB total, cache version v-{digest})")
for f in sorted(DIST.rglob("*")):
    if f.is_file():
        print(" ", f.relative_to(DIST))
