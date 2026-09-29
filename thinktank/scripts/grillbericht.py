#!/usr/bin/env python3
"""Erzeugt den HTML-Grillbericht des incubateai Thinktanks und öffnet ihn.

Aufruf:
  python3 grillbericht.py <daten.json> [--out VERZEICHNIS] [--no-open]
  python3 grillbericht.py - < daten.json

Die Eingabe enthält nur Inhalte (Idee, Voten, Entscheidung). Das Skript prüft sie
und setzt sie in den Datenblock der Vorlage ein. Namen, Rollen, Porträts, Titel und
GoatCounter ergänzt die Vorlage selbst. Nur Standardbibliothek, keine Abhängigkeiten.
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "assets", "grillbericht-template.html")

STAMM = ["franklin", "wedgwood", "edison", "fugger", "drucker"]
RESERVE = ["lauder", "graham"]
EMPFEHLUNGEN = ["freigeben", "freigeben-mit-auflagen", "überarbeiten", "verwerfen", "vertagt"]
GARSTUFEN = {"Roh": 10, "Rare": 30, "Medium rare": 55, "Medium": 70, "Medium well": 85, "Well done": 100}
KONFIDENZ = ["hoch", "mittel", "niedrig"]
STATUS = ["Nutzerangabe", "Beleg", "Schluss", "Annahme", "Offen"]


def fail(msg):
    sys.exit(f"Fehler in den Grillbericht-Daten: {msg}")


def need(obj, key, typ, where):
    v = obj.get(key)
    if not isinstance(v, typ) or (isinstance(v, (str, list)) and not v):
        fail(f"{where}.{key} fehlt oder ist leer")
    return v


def slugify(text):
    for k, v in {"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"}.items():
        text = text.replace(k, v)
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:40] or "idee"


def build(d):
    idee = need(d, "idee", dict, "")
    need(idee, "titel", str, "idee"); need(idee, "pitch", str, "idee")
    idee.setdefault("vortragende", "Ideengeber:in")
    idee.setdefault("kontextdateien", [])

    rat, ids = [], []
    for i, r in enumerate(need(d, "rat", list, "")):
        w = f"rat[{i}]"
        pid = need(r, "id", str, w)
        if pid not in STAMM + RESERVE:
            fail(f"{w}.id '{pid}' unbekannt (erlaubt: {', '.join(STAMM + RESERVE)})")
        if pid in ids:
            fail(f"{w}.id '{pid}' doppelt")
        ids.append(pid)
        score = r.get("score")
        if not isinstance(score, int) or not 1 <= score <= 100:
            fail(f"{w}.score muss eine ganze Zahl 1–100 sein")
        if r.get("konfidenz") not in KONFIDENZ:
            fail(f"{w}.konfidenz muss {KONFIDENZ} sein")
        for k in ("kernsatz", "pruefung", "einwand"):
            need(r, k, str, w)
        ups = r.get("upvotes") or ([r["upvote"]] if r.get("upvote") else [])
        if not ups:
            fail(f"{w}.upvotes fehlt (auch der niedrigste Score nennt mindestens einen)")
        for j, u in enumerate(ups):
            if not (isinstance(u.get("plus"), int) and isinstance(u.get("neu"), int) and u.get("wenn")):
                fail(f"{w}.upvotes[{j}] braucht plus (int), neu (int), wenn (Text)")
        m = {k: r[k] for k in ("id", "score", "konfidenz", "kernsatz", "pruefung", "einwand")}
        m["upvotes"] = ups[:3]
        m["auflagen"] = r.get("auflagen") or []
        rat.append(m)
    missing = [p for p in STAMM if p not in ids]
    if missing:
        fail(f"Stammrat unvollständig, es fehlen: {', '.join(missing)}")
    rat.sort(key=lambda m: (STAMM + RESERVE).index(m["id"]))

    e = need(d, "entscheidung", dict, "")
    if e.get("empfehlung") not in EMPFEHLUNGEN:
        fail(f"entscheidung.empfehlung muss eins von {EMPFEHLUNGEN} sein")
    if e.get("garstufe") not in GARSTUFEN:
        fail(f"entscheidung.garstufe muss eins von {list(GARSTUFEN)} sein")
    need(e, "kurzurteil", str, "entscheidung")
    for k in ("konsens", "dissens", "annahmen", "offen"):
        e.setdefault(k, [])
    se = need(e, "staerksterEinwand", dict, "entscheidung")
    need(se, "von", str, "entscheidung.staerksterEinwand"); need(se, "text", str, "entscheidung.staerksterEinwand")
    for j, a in enumerate(e["annahmen"]):
        if a.get("status") not in STATUS:
            fail(f"entscheidung.annahmen[{j}].status muss eins von {STATUS} sein")
    g = need(e, "gespraech", dict, "entscheidung")
    need(g, "mitWem", str, "entscheidung.gespraech"); need(g, "fragen", list, "entscheidung.gespraech")
    t = need(e, "test", dict, "entscheidung")
    for k in ("ziel", "erfolg", "abbruch"):
        need(t, k, str, "entscheidung.test")
    need(t, "schritte", list, "entscheidung.test")

    vorsitz = {"urteil": need(need(d, "vorsitz", dict, ""), "urteil", str, "vorsitz")}

    datum = d.get("datum") or dt.date.today().isoformat()
    return {
        "entwurf": bool(d.get("entwurf")), "datum": datum, "idee": idee, "vorsitz": vorsitz, "rat": rat, "entscheidung": e,
    }, datum


def render(data):
    js = json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")
    html = open(TEMPLATE, encoding="utf8").read()
    if html.count("__THINKTANK_DATA__") != 1:
        sys.exit("Vorlage beschädigt: Platzhalter __THINKTANK_DATA__ nicht genau einmal vorhanden")
    return html.replace("__THINKTANK_DATA__", js), slugify(data["idee"]["titel"])


def open_file(path):
    try:
        if sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        elif os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", path], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("daten", help="JSON-Datei oder - für stdin")
    ap.add_argument("--out", default=".", help="Zielverzeichnis (Standard: aktuelles)")
    ap.add_argument("--no-open", action="store_true", help="Datei nicht öffnen")
    a = ap.parse_args()
    raw = sys.stdin.read() if a.daten == "-" else open(a.daten, encoding="utf8").read()
    try:
        d = json.loads(raw)
    except json.JSONDecodeError as ex:
        fail(f"kein gültiges JSON ({ex})")
    data, datum = build(d)
    html, slug = render(data)
    os.makedirs(a.out, exist_ok=True)
    path = os.path.abspath(os.path.join(a.out, f"thinktank-{slug}-{datum}.html"))
    open(path, "w", encoding="utf8").write(html)
    opened = False if a.no_open else open_file(path)
    print(path)
    if not a.no_open and not opened:
        print("Hinweis: Datei konnte nicht automatisch geöffnet werden.", file=sys.stderr)


if __name__ == "__main__":
    main()
