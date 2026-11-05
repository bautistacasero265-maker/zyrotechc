#!/usr/bin/env python3
"""Exporta la clave PÚBLICA ZyroTech desde una clave privada existente.

La clave privada nunca se copia ni se modifica. La herramienta guarda únicamente
PUBLIC_KEY_B32 en app/public_key.py para que GitHub Actions pueda compilar Pro.
"""
import base64
import os
import tkinter as tk
from tkinter import filedialog, messagebox

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def derive_public_key(private_path):
    """Devuelve la clave pública Ed25519 en Base32 sin padding."""
    with open(private_path, "rb") as f:
        private_bytes = f.read()
    key = serialization.load_pem_private_key(private_bytes, password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise ValueError("El archivo no contiene una clave privada Ed25519 de ZyroTech.")
    public_bytes = key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    return base64.b32encode(public_bytes).decode("ascii").rstrip("=")


def public_key_module(encoded):
    """Genera el contenido Python de la clave pública."""
    if not encoded or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for ch in encoded):
        raise ValueError("La clave pública Base32 no es válida.")
    return (
        "# Clave PÚBLICA ZyroTech. Se puede subir a GitHub.\n"
        f'PUBLIC_KEY_B32 = "{encoded}"\n'
    )


def main():
    root = tk.Tk()
    root.withdraw()
    root.update_idletasks()

    private_path = filedialog.askopenfilename(
        parent=root,
        title="Seleccioná tu clave privada ZyroTech existente",
        filetypes=[("Clave privada PEM", "*.pem"), ("Todos los archivos", "*.*")],
    )
    if not private_path:
        root.destroy()
        return

    try:
        encoded = derive_public_key(private_path)
        output = public_key_module(encoded)
    except Exception as exc:
        messagebox.showerror("ZyroTech Key Export", f"No se pudo leer la clave privada.\n\n{exc}", parent=root)
        root.destroy()
        return

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(private_path)))
    default_dir = os.path.join(project_root, "app")
    initial_dir = default_dir if os.path.isdir(default_dir) else os.path.dirname(private_path)
    output_path = filedialog.asksaveasfilename(
        parent=root,
        title="Guardá la clave pública para compilar Pro",
        initialdir=initial_dir,
        initialfile="public_key.py",
        defaultextension=".py",
        filetypes=[("Archivo Python", "*.py")],
    )
    if not output_path:
        root.destroy()
        return

    try:
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                existing = f.read()
            if 'PUBLIC_KEY_B32 = "' in existing:
                current = existing.split('PUBLIC_KEY_B32 = "', 1)[1].split('"', 1)[0]
                if current and current != encoded:
                    messagebox.showerror(
                        "ZyroTech Key Export",
                        "El archivo seleccionado contiene otra clave pública. No se modificó.",
                        parent=root,
                    )
                    root.destroy()
                    return
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(output)
        messagebox.showinfo(
            "ZyroTech Key Export",
            "Clave pública exportada correctamente.\n\n"
            "Subí solamente public_key.py al repositorio.\n"
            "No subas ni compartas el archivo PEM privado.",
            parent=root,
        )
    except OSError as exc:
        messagebox.showerror("ZyroTech Key Export", f"No se pudo guardar el archivo.\n\n{exc}", parent=root)
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
