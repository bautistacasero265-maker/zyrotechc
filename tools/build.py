#!/usr/bin/env python3
"""Build reproducible de ZyroTech Free para Windows."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
BUILD = ROOT / "build"
STAGE = BUILD / "stage_free"
DIST = ROOT / "dist"


def prepare_stage() -> Path:
    """Crea una carpeta limpia con los únicos archivos necesarios para Free."""
    shutil.rmtree(STAGE, ignore_errors=True)
    STAGE.mkdir(parents=True, exist_ok=True)
    for filename in ("core.py", "zyrotech.py", "tweaks_free.json"):
        source = APP / filename
        if not source.is_file():
            raise FileNotFoundError(f"Falta un archivo de ZyroTech Free: {source}")
        shutil.copy2(source, STAGE / filename)
    return STAGE


def build() -> Path:
    stage = prepare_stage()
    catalog = stage / "tweaks_free.json"
    command = [
        sys.executable, "-m", "PyInstaller",
        "--onefile", "--noconsole", "--uac-admin",
        "--name", "ZyroTech-Free",
        "--collect-all", "customtkinter",
        "--add-data", f"{catalog}{os.pathsep}.",
        "--distpath", str(DIST),
        "--workpath", str(BUILD / "work_free"),
        "--specpath", str(BUILD),
        "zyrotech.py",
    ]
    subprocess.run(command, cwd=stage, check=True)
    executable = DIST / "ZyroTech-Free.exe"
    if not executable.is_file():
        raise RuntimeError("PyInstaller terminó sin generar ZyroTech-Free.exe")
    print(f"Build completado: {executable}")
    return executable


if __name__ == "__main__":
    build()
