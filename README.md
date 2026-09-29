# grillmyidea light · Thinktank-Skill

Ein Rat aus fünf Denkstilen (Franklin, Wedgwood, Edison, Fugger, Drucker; Vorsitz Sloan) prüft eine Geschäftsidee und erstellt einen interaktiven HTML-Grillbericht mit Voten, Dissens, riskantesten Annahmen und 7-Tage-Test.

Abgespeckte Variante des Thinktanks von [grillmyidea.eu](https://grillmyidea.eu).

## Installation

- **Claude (App, Cowork):** `dist/thinktank.skill` unter *Einstellungen → Fähigkeiten* hochladen. Code-Ausführung muss aktiv sein, sonst kann der Skill Skript und Vorlage nicht lesen.
- **Claude Code:** Ordner `thinktank/` nach `~/.claude/skills/` kopieren.
- **Codex:** Ordner `thinktank/` nach `~/.codex/skills/` kopieren.

Aufruf zum Beispiel: „Lass meine Idee vom Thinktank grillen: …“

## Aufbau

```
thinktank/
  SKILL.md                         Anweisungen für das Modell
  agents/openai.yaml               Anzeigename für Codex
  scripts/grillbericht.py          prüft die Daten, schreibt und öffnet den Bericht
  assets/grillbericht-template.html  vollständige Vorlage, einziger Platzhalter __THINKTANK_DATA__
  assets/portraits/                Porträts (WebP) und Skript zum Neuladen
  examples/                        Beispieldaten und gerenderter Beispielbericht
```

Ohne Shell setzt das Modell das JSON direkt in die Vorlage ein; Personen, Porträts, Titel und Statistik ergänzt die Vorlage selbst.

## Entwicklung

```
python3 thinktank/scripts/grillbericht.py thinktank/examples/beispiel-daten.json --out /tmp
python3 build.py    # erzeugt dist/thinktank.skill
```

Porträts neu laden: `python3 thinktank/assets/portraits/fetch_portraits.py` (schreibt `portraits.json` und den Porträt-Block der Vorlage).
