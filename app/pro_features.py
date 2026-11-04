"""Solo Pro: licencia atada al equipo, Game Booster, perfiles, DNS, limpieza de RAM."""
import base64, ctypes, hashlib, json, os, re, subprocess, threading
import core, public_key

MAGIC = b"ZT1"
GENERIC = {"", "none", "default string", "to be filled by o.e.m.", "not applicable", "system serial number", "unknown", "0",
           "ffffffff-ffff-ffff-ffff-ffffffffffff", "00000000-0000-0000-0000-000000000000", "n/a", "o.e.m.", "type1productconfigid"}


# ---------- identidad del equipo ----------
def _valid(v):
    v = (v or "").strip().lower()
    return v not in GENERIC and len(v) >= 4 and len(set(v)) > 2

def fingerprint():
    """Lista de huellas (6 bytes) de componentes del equipo; ignora valores genéricos de fábrica."""
    out = core.ps(r"""$c=@{}
$c.cpu=(Get-CimInstance Win32_Processor | Select -First 1).ProcessorId
$c.board=(Get-CimInstance Win32_BaseBoard | Select -First 1).SerialNumber
$c.uuid=(Get-CimInstance Win32_ComputerSystemProduct).UUID
$c.bios=(Get-CimInstance Win32_BIOS).SerialNumber
try{$c.disk=(Get-Partition -DriveLetter C | Get-Disk).SerialNumber}catch{}
$c.guid=(Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography').MachineGuid
$c | ConvertTo-Json -Compress""")
    comps = json.loads(out)
    return sorted({hashlib.sha256(f"{k}:{str(v).strip().lower()}".encode()).digest()[:6] for k, v in comps.items() if _valid(str(v))})

def _b32(raw): return base64.b32encode(raw).decode().rstrip("=")
def _unb32(text):
    t = re.sub(r"[^A-Z2-7]", "", text.upper()); return base64.b32decode(t + "=" * (-len(t) % 8))
def group(text, n=5): return "-".join(text[i:i + n] for i in range(0, len(text), n))

def machine_payload(comps): return MAGIC + bytes([len(comps)]) + b"".join(comps)
def machine_code(comps): return group(_b32(machine_payload(comps)))


# ---------- licencia (firma Ed25519: no se puede fabricar sin la clave privada del vendedor) ----------
def verify(license_text, comps):
    """Devuelve (ok, motivo)."""
    if not public_key.PUBLIC_KEY_B32:
        return False, "Falta la clave pública (ejecutá: python tools/keygen.py init y recompilá)."
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        raw = _unb32(license_text)
        payload, sig = raw[:-64], raw[-64:]
        Ed25519PublicKey.from_public_bytes(_unb32(public_key.PUBLIC_KEY_B32)).verify(sig, payload)
    except InvalidSignature:
        return False, "Licencia inválida."
    except Exception:
        return False, "Licencia con formato incorrecto."
    if payload[:3] != MAGIC or len(payload) < 4 or len(payload) != 4 + 6 * payload[3]:
        return False, "Licencia con formato incorrecto."
    lic = {payload[4 + 6 * i: 10 + 6 * i] for i in range(payload[3])}
    need = max(2, len(lic) - 2)
    if len(lic & set(comps)) < min(need, len(lic)):
        return False, "Esta licencia pertenece a otro equipo."
    return True, "ok"

def save_license(text):
    text = re.sub(r"\s+", "", text)
    with open(core.data_path("license.key"), "w") as f: f.write(text)
    try:  # segunda copia por si borran el archivo
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\ZyroTech") as k: winreg.SetValueEx(k, "License", 0, winreg.REG_SZ, text)
    except Exception: pass

def load_license():
    try:
        with open(core.data_path("license.key")) as f:
            t = f.read().strip()
            if t: return t
    except OSError: pass
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\ZyroTech") as k: return winreg.QueryValueEx(k, "License")[0]
    except Exception: return ""


# ---------- perfiles ----------
PROFILE_MODULES = {
    "Lite": {"Gaming", "Energía", "Interfaz", "Privacidad"},
    "Medio": {"Gaming", "Energía", "Interfaz", "Privacidad", "Red", "Periféricos", "Inicio", "Debloat", "Kernel"},
    # Avanzado agrega servicios y tareas, con exclusiones por riesgo y nombre abajo.
    "Avanzado": {"Gaming", "Energía", "Interfaz", "Privacidad", "Red", "Periféricos", "Inicio", "Debloat", "Kernel", "Seguridad básica", "Servicios", "Tareas"},
}
PROFILE_SKIP_NAMES = ("WSearch", "Windows Search", "Hibernación", "DNS ", "Quitar app", "Defender", "Windows Update")
PROFILE_BLOCK_BADGES = {"Breaking", "Irreversible", "Seguridad", "Beta"}

def profile_preview(name, tweaks, hw, statuses):
    """Propone solo cambios reversibles, medibles y compatibles; informa los omitidos."""
    modules = PROFILE_MODULES[name]
    result = {"apply": [], "active": [], "partial": [], "incompatible": [], "unsafe": [], "locked": [], "once": []}
    for t in tweaks:
        if t["module"] not in modules:
            continue
        if t.get("locked"):
            result["locked"].append(t)
        elif t["mode"] != "track":
            result["once"].append(t)
        elif t.get("risk") == "extreme" or t.get("badge") in PROFILE_BLOCK_BADGES or any(x.lower() in t["name"].lower() for x in PROFILE_SKIP_NAMES):
            result["unsafe"].append(t)
        elif not core.applicable(t, hw) or statuses.get(t["id"]) == "unknown":
            result["incompatible"].append(t)
        elif statuses.get(t["id"]) == "active":
            result["active"].append(t)
        elif statuses.get(t["id"]) == "partial":
            result["partial"].append(t)
            result["apply"].append(t)
        else:
            result["apply"].append(t)
    return result


# ---------- DNS ----------
def apply_dns(server, alt=None):
    sv = f"'{server}'" + (f",'{alt}'" if alt else "")
    core.ps(f"Get-NetAdapter -Physical | ? Status -eq Up | Set-DnsClientServerAddress -ServerAddresses ({sv})")
    return [{"type": "ps", "cmd": "Get-NetAdapter -Physical | Set-DnsClientServerAddress -ResetServerAddresses"}]


# ---------- Game Booster ----------
GAMES = {"valorant-win64-shipping.exe", "cs2.exe", "fortniteclient-win64-shipping.exe", "cod.exe", "r5apex.exe", "rocketleague.exe", "league of legends.exe",
         "overwatch.exe", "dota2.exe", "rainbowsix.exe", "tslgame.exe", "gta5.exe", "eldenring.exe", "cyberpunk2077.exe", "rustclient.exe", "destiny2.exe",
         "robloxplayerbeta.exe", "minecraft.exe", "apexlegends.exe", "hogwartslegacy.exe", "rdr2.exe", "witcher3.exe"}

class GameBooster:
    """Detecta juegos abiertos: prioridad Alta al proceso, timer 0.5 ms y purga de standby. Al cerrarse el juego restaura el timer."""
    def __init__(self, extra, log):
        self.extra, self.log, self.stop_ev, self.active, self.boosted = set(extra), log, threading.Event(), False, set()

    def start(self):
        self.stop_ev = threading.Event(); ev = self.stop_ev
        threading.Thread(target=self._loop, args=(ev,), daemon=True).start()

    def stop(self):
        self.stop_ev.set()
        if self.active: core.set_timer(False); self.active = False

    def _running(self):
        out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True, creationflags=core.NOWIN, encoding="utf-8", errors="replace").stdout
        procs = {}
        for line in out.splitlines():
            parts = [p.strip('"') for p in line.split('","')]
            if len(parts) > 1 and parts[1].isdigit(): procs[int(parts[1])] = parts[0].lower()
        return procs

    def _loop(self, ev):
        names = GAMES | self.extra
        while not ev.wait(4):
            try:
                games = {pid: n for pid, n in self._running().items() if n in names}
                if games and not self.active:
                    core.set_timer(True); self.active = True
                    try: core.purge_standby()
                    except Exception: pass
                    self.log("Game Booster: juego detectado, timer 0.5 ms activo.")
                for pid in set(games) - self.boosted:
                    h = ctypes.windll.kernel32.OpenProcess(0x200, False, pid)
                    if h: ctypes.windll.kernel32.SetPriorityClass(h, 0x80); ctypes.windll.kernel32.CloseHandle(h)
                self.boosted = set(games)
                if not games and self.active:
                    core.set_timer(False); self.active = False; self.log("Game Booster: juego cerrado, todo restaurado.")
            except Exception:
                pass


# ---------- Limpiador de RAM ----------
class RamCleaner:
    """Purga la standby list cuando ocupa >=40% de la RAM y queda libre <15%."""
    def __init__(self, log, every=30, standby_pct=40, free_pct=15):
        self.log, self.every, self.sp, self.fp, self.ev = log, every, standby_pct, free_pct, threading.Event()

    def start(self):
        self.ev = threading.Event(); ev = self.ev
        def loop():
            while not ev.wait(self.every):
                try:
                    m = core.memory_state(); t = m["total"]
                    if m["standby"] * 100 >= self.sp * t and m["free"] * 100 < self.fp * t:
                        core.purge_standby(); self.log("RAM: standby list purgada.")
                except Exception: pass
        threading.Thread(target=loop, daemon=True).start()

    def stop(self): self.ev.set()
