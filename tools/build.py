#!/usr/bin/env python3
"""Compila ZyroTech-Free.exe y ZyroTech-Pro.exe (correr en Windows).
  python tools/build.py          ambas
  python tools/build.py free     solo Free
  python tools/build.py pro      solo Pro (exige haber corrido keygen init)
  python tools/build.py --stage-only   arma las carpetas sin compilar (pruebas)
Free NO incluye el código ni las acciones de los tweaks Pro."""
import json, os, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP, BUILD = os.path.join(ROOT, "app"), os.path.join(ROOT, "build")

def free_tweaks(full):
    return [t if t["tier"] == "free" else {**{k: v for k, v in t.items() if k != "actions"}, "locked": True} for t in full]

def stage(edition):
    d = os.path.join(BUILD, "stage_" + edition); shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    files = ["core.py", "zyrotech.py", "config.py"] + (["pro_features.py", "public_key.py"] if edition == "pro" else [])
    for f in files: shutil.copy(os.path.join(APP, f), d)
    open(os.path.join(d, "edition.py"), "w").write(f'EDITION = "{edition}"\n')
    full = json.load(open(os.path.join(ROOT, "tweaks.json"), encoding="utf-8"))
    json.dump(full if edition == "pro" else free_tweaks(full), open(os.path.join(d, f"tweaks_{edition}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return d

def compile_(edition):
    if edition == "pro":
        ns = {}; exec(open(os.path.join(APP, "public_key.py")).read(), ns)
        if not ns.get("PUBLIC_KEY_B32"): sys.exit("Falta la clave pública: corré primero `python tools/keygen.py init`.")
    d = stage(edition); name = "ZyroTech-" + edition.capitalize()
    cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--uac-admin", "--noconsole", "--name", name, "--collect-all", "customtkinter",
           "--add-data", f"{os.path.abspath(os.path.join(d, f'tweaks_{edition}.json'))}{os.pathsep}.", "--distpath", os.path.join(ROOT, "dist"), "--workpath", os.path.join(BUILD, "work_" + edition),
           "--specpath", BUILD] + (["--hidden-import", "cryptography.hazmat.primitives.asymmetric.ed25519"] if edition == "pro" else []) + ["zyrotech.py"]
    subprocess.run(cmd, cwd=d, check=True); print("OK ->", os.path.join(ROOT, "dist", name + ".exe"))

if __name__ == "__main__":
    a = sys.argv[1:]
    if "--stage-only" in a: [stage(e) for e in ("free", "pro")]; sys.exit(0)
    for e in (a if a else ["free", "pro"]): compile_(e)
