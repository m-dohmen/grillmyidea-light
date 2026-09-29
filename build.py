#!/usr/bin/env python3
"""Baut dist/thinktank.skill (Zip mit Ordner thinktank/) für Claude und Codex."""
import os
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "dist", "thinktank.skill")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for base, dirs, files in os.walk(os.path.join(ROOT, "thinktank")):
        dirs[:] = sorted(d for d in dirs if d != "__pycache__")
        for f in sorted(files):
            if f == ".DS_Store" or f.endswith(".pyc"):
                continue
            path = os.path.join(base, f)
            z.write(path, os.path.relpath(path, ROOT))
print(OUT)
