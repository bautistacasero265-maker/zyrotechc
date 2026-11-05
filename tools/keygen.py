#!/usr/bin/env python3
"""Generador de licencias ZyroTech Pro (lo usás SOLO vos).
  python tools/keygen.py init            crea el par inicial (solo si todavía no existe)
  python tools/keygen.py export-public    deriva app/public_key.py desde tu clave privada existente
  python tools/keygen.py sign <CODIGO>   convierte el código de equipo del cliente en su licencia
"""
import base64, csv, datetime, os, re, sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

HERE = os.path.dirname(os.path.abspath(__file__))
PRIV = os.path.join(HERE, "zyrotech_private.pem")
PUBPY = os.path.join(HERE, "..", "app", "public_key.py")
LOG = os.path.join(HERE, "licencias_emitidas.csv")
MAGIC = b"ZT1"

def b32(raw): return base64.b32encode(raw).decode().rstrip("=")
def unb32(t):
    t = re.sub(r"[^A-Z2-7]", "", t.upper()); return base64.b32decode(t + "=" * (-len(t) % 8))
def group(t, n=5): return "-".join(t[i:i + n] for i in range(0, len(t), n))

def init():
    if os.path.exists(PRIV):
        sys.exit("Ya existe zyrotech_private.pem. Si la borrás, todas las licencias emitidas dejan de servir.")
    key = Ed25519PrivateKey.generate()
    with open(PRIV, "wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    with open(PUBPY, "w") as f:
        f.write("# Clave PÚBLICA (se puede subir a GitHub). La genera tools/keygen.py init\nPUBLIC_KEY_B32 = \"%s\"\n" % b32(pub))
    print("Listo. Guardá una copia de tools/zyrotech_private.pem en un lugar seguro (pendrive/nube privada). NO la subas a GitHub.")

def export_public():
    """Deriva solo la clave pública desde la privada existente, sin crear ni rotar claves."""
    if not os.path.exists(PRIV):
        sys.exit("No se encontró tools/zyrotech_private.pem. No generes otra clave si ya emitiste licencias.")
    key = serialization.load_pem_private_key(open(PRIV, "rb").read(), None)
    pub = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    encoded = b32(pub)
    if os.path.exists(PUBPY):
        with open(PUBPY, encoding="utf-8") as f:
            current = f.read()
        match = re.search(r'PUBLIC_KEY_B32\s*=\s*"([^"]*)"', current)
        if match and match.group(1) and match.group(1) != encoded:
            sys.exit("La clave pública actual no coincide con la privada. No se modificó ningún archivo.")
        if match and match.group(1) == encoded:
            print("La clave pública ya coincide con la clave privada existente.")
            return
    with open(PUBPY, "w", encoding="utf-8") as f:
        f.write("# Clave PÚBLICA derivada de tu clave privada existente. Se puede subir a GitHub.\n")
        f.write('PUBLIC_KEY_B32 = "%s"\n' % encoded)
    print("Clave pública exportada a app/public_key.py.")
    print("Subí solamente app/public_key.py. Nunca subas tools/zyrotech_private.pem.")


def sign(code):
    if not os.path.exists(PRIV): sys.exit("Falta la clave privada: corré primero `python tools/keygen.py init`.")
    payload = unb32(code)
    if payload[:3] != MAGIC or len(payload) != 4 + 6 * payload[3] or payload[3] < 2:
        sys.exit("Código de equipo inválido.")
    key = serialization.load_pem_private_key(open(PRIV, "rb").read(), None)
    lic = group(b32(payload + key.sign(payload)))
    new = not os.path.exists(LOG)
    with open(LOG, "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["fecha", "codigo_equipo"])
        w.writerow([datetime.datetime.now().isoformat(timespec="seconds"), code])
    print(lic)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["init"]: init()
    elif a[:1] == ["export-public"]: export_public()
    elif a[:1] == ["sign"] and len(a) == 2: sign(a[1])
    else: print(__doc__)
