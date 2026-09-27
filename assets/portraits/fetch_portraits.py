"""Lädt Porträts für den Grillbericht (assets/portraits/portraits.json) von Wikimedia Commons, macht sie schwarz-weiß, 128x128 quadratisch
und schreibt sie als WebP-Data-URIs nach portraits.json (id -> {src, credit}).

Aufruf: python3 fetch_portraits.py
"""
import base64, io, json, re, time, urllib.parse, urllib.request
from PIL import Image, ImageOps

UA = "grillmyidea-thinktank/1.0 (https://grillmyidea.eu; portrait build script)"
SIZE = 128

# id -> (Commons-Datei, Gesichts-Zuschnitt (cx, cy, Seitenlänge) in Pixeln des 500px-Thumbs)
PORTRAITS = {
    "sloan":    ("Alfred_Pritchard_Sloan_1937.jpg", (255, 200, 250)),
    "franklin": ("Joseph_Siffrein_Duplessis_-_Benjamin_Franklin_-_Google_Art_Project.jpg", (220, 225, 250)),
    "wedgwood": ("Josiah_Wedgwood_by_George_Stubbs,_1780,_enamel_on_a_Wedgwood_ceramic_tablet_-_Wedgwood_Museum_-_Barlaston,_Stoke-on-Trent,_England_-_DSC09537.jpg", (250, 265, 240)),
    "edison":   ("Thomas_Edison2.jpg", (262, 145, 200)),
    "fugger":   ("Albrecht_Dürer_080.jpg", (290, 225, 260)),
    "drucker":  ("Drucker5789.jpg", (222, 175, 220)),
    "lauder":   ("Estee_Lauder_NYWTS.jpg", (110, 210, 200)),
    "graham":   ("Benjamin Graham (1894-1976) portrait on 23 March 1950.jpg", (238, 135, 190)),
}


def get(url, tries=5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # 429 / Netzfehler: warten und nochmal
            wait = 3 * (i + 1)
            print(f"  retry in {wait}s ({e})")
            time.sleep(wait)
    raise RuntimeError(f"failed: {url}")


def info(filename):
    q = urllib.parse.urlencode({
        "action": "query", "format": "json", "prop": "imageinfo",
        "iiprop": "url|extmetadata", "iiurlwidth": 500, "titles": "File:" + filename,
    })
    page = next(iter(json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))["query"]["pages"].values()))
    ii = page["imageinfo"][0]
    m = ii["extmetadata"]
    strip = lambda s: re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()
    return ii["thumburl"], {
        "artist": strip(m.get("Artist", {}).get("value"))[:80],
        "license": m.get("LicenseShortName", {}).get("value", ""),
        "source": "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(filename),
    }


def to_bw_square(data, box):
    cx, cy, side = box
    im = Image.open(io.BytesIO(data)).convert("L")
    im = im.crop((cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)).resize((SIZE, SIZE), Image.LANCZOS)
    im = ImageOps.autocontrast(im, cutoff=1)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=72, method=6)
    return "data:image/webp;base64," + base64.b64encode(buf.getvalue()).decode()


out = {}
for pid, (fn, box) in PORTRAITS.items():
    print(pid)
    thumb, credit = info(fn)
    time.sleep(1.5)
    out[pid] = {"src": to_bw_square(get(thumb), box), "credit": credit}
    time.sleep(1.5)

import os
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "portraits.json"), "w", encoding="utf8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok", sum(len(v["src"]) for v in out.values()), "bytes")
