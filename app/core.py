"""Núcleo compartido Free/Pro: registro, PowerShell, tweaks, hardware, medición. Solo stdlib."""
import base64, ctypes, json, os, re, socket, statistics, subprocess, sys, time

IS_WIN = sys.platform == "win32"
if IS_WIN:
    import winreg
    from ctypes import wintypes

BASE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "ZyroTech")
NOWIN = 0x08000000


def data_path(name):
    os.makedirs(DATA, exist_ok=True)
    return os.path.join(DATA, name)

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError): return default

def save_json(path, obj):
    with open(path, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)

def ps(cmd):
    full = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; $ProgressPreference='SilentlyContinue'; " + cmd
    enc = base64.b64encode(full.encode("utf-16le")).decode()
    r = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", creationflags=NOWIN if IS_WIN else 0)
    if r.returncode != 0: raise RuntimeError((r.stderr or r.stdout).strip()[:300] or "PowerShell falló")
    return r.stdout

def is_admin():
    return IS_WIN and ctypes.windll.shell32.IsUserAnAdmin() != 0


# ---------- registro ----------
def _hive(path):
    h, sub = path.split("\\", 1)
    return {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}[h], sub

def _vt(): return {"REG_DWORD": winreg.REG_DWORD, "REG_SZ": winreg.REG_SZ, "REG_BINARY": winreg.REG_BINARY}

def reg_get(a):
    h, sub = _hive(a["path"])
    try:
        with winreg.OpenKey(h, sub, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k: v, t = winreg.QueryValueEx(k, a["name"])
    except FileNotFoundError:
        return None, None
    names = {v_: k_ for k_, v_ in _vt().items()}
    if t not in names: raise RuntimeError(f"tipo de valor no soportado en {a['path']}")
    return (v.hex() if t == winreg.REG_BINARY else v), names[t]

def reg_set(a):
    h, sub = _hive(a["path"])
    if a["value"] is None:
        try:
            with winreg.OpenKey(h, sub, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k: winreg.DeleteValue(k, a["name"])
        except FileNotFoundError: pass
        return
    t = _vt()[a["vtype"]]
    v = bytes.fromhex(a["value"]) if t == winreg.REG_BINARY else a["value"]
    with winreg.CreateKeyEx(h, sub, 0, winreg.KEY_SET_VALUE | winreg.KEY_WOW64_64KEY) as k: winreg.SetValueEx(k, a["name"], 0, t, v)

def snapshot(a):
    v, t = reg_get(a)
    return {"type": "reg", "path": a["path"], "name": a["name"], "value": v, "vtype": t or a["vtype"]}

def run_undo(undo):
    errs = []
    for u in reversed(undo):
        try:
            if u["type"] == "reg": reg_set(u)
            else: ps(u["cmd"])
        except Exception as e: errs.append(str(e))
    return errs

def apply_tweak(t):
    """Aplica y devuelve las acciones para deshacerlo. Si falla a mitad, revierte lo hecho."""
    undo = []
    try:
        for a in t["actions"]:
            if a["type"] == "reg":
                undo.append(snapshot(a)); reg_set(a)
            else:
                cap = ps(a["capture"]).strip() if a.get("capture") else ""
                ps(a["cmd"])
                if a.get("undo"): undo.append({"type": "ps", "cmd": a["undo"].replace("{captured}", cap)})
    except Exception:
        run_undo(undo); raise
    return undo


# ---------- seguridad ----------
def create_restore_point():
    ps("Enable-ComputerRestore -Drive 'C:\\' -ErrorAction SilentlyContinue; "
       "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\SystemRestore' -Name SystemRestorePointCreationFrequency -Value 0 -Type DWord; "
       "Checkpoint-Computer -Description 'ZyroTech - antes de optimizar' -RestorePointType MODIFY_SETTINGS")

def backup_registry():
    d = os.path.join(DATA, "backups"); os.makedirs(d, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for i, key in enumerate([r"HKLM\SOFTWARE\Policies", r"HKLM\SYSTEM\CurrentControlSet\Control", r"HKCU\Control Panel",
                             r"HKCU\Software\Microsoft\Windows\CurrentVersion", r"HKCU\System\GameConfigStore"]):
        subprocess.run(["reg", "export", key, os.path.join(d, f"{stamp}-{i}.reg"), "/y"], check=True, capture_output=True, creationflags=NOWIN)
    return stamp


# ---------- hardware ----------
def scan_raw():
    out = ps(r"""$g=@(Get-CimInstance Win32_VideoController | % Name) -join '|'
$c=(Get-CimInstance Win32_Processor | Select -First 1).Name
$r=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1GB)
$d=$null; $p=$null; $ssd=$false
try {
  $d=Get-Partition -DriveLetter C -ErrorAction Stop | Get-Disk -ErrorAction Stop | Select-Object -First 1
  if($d) {
    $p=Get-PhysicalDisk -ErrorAction SilentlyContinue | Where-Object { $_.DeviceId -eq [string]$d.Number } | Select-Object -First 1
    if($p) { $ssd=($p.MediaType -eq 'SSD' -or $p.BusType -eq 'NVMe') }
    else { $ssd=([string]$d.BusType -match 'NVMe|SSD' -or [string]$d.FriendlyName -match '\\bSSD\\b|NVMe') }
  }
} catch { $ssd=$false }
$lap=[bool](Get-CimInstance Win32_SystemEnclosure | ? { $_.ChassisTypes | ? { $_ -in 8,9,10,11,12,14,18,21,30,31,32 } })
$o=Get-CimInstance Win32_OperatingSystem
$w=[bool](Get-NetAdapter -Physical -ErrorAction SilentlyContinue | ? { $_.PhysicalMediaType -match '802.11|Native' })
[pscustomobject]@{gpu=$g;cpu=$c;ram=$r;ssd=$ssd;laptop=$lap;build=[int]$o.BuildNumber;os=$o.Caption;wifi=$w} | ConvertTo-Json -Compress""")
    return json.loads(out)

def hw_profile(raw):
    gpu, cpu = raw["gpu"].lower(), raw["cpu"].lower()
    return {"nvidia": "nvidia" in gpu or "geforce" in gpu, "amd": "amd" in gpu or "radeon" in gpu, "intel": "intel" in gpu,
            "cpu_intel": "intel" in cpu, "cpu_amd": "amd" in cpu, "ram": int(raw["ram"]), "ssd": bool(raw["ssd"]), "laptop": bool(raw["laptop"]),
            "win11": int(raw["build"]) >= 22000, "wifi": bool(raw["wifi"]), "gpu_name": raw["gpu"].split("|")[-1] or "GPU", "cpu_name": raw["cpu"].strip(),
            "os": raw.get("os", "Windows")}

def applicable(t, hw):
    q = t.get("req") or {}
    if "gpu" in q and not hw.get(q["gpu"]): return False
    if "cpu" in q and not hw.get("cpu_" + q["cpu"]): return False
    if q.get("ssd") and not hw["ssd"]: return False
    if q.get("ram_min", 0) > hw["ram"]: return False
    if q.get("win11") and not hw["win11"]: return False
    if q.get("desktop") and hw["laptop"]: return False
    if q.get("wifi") and not hw["wifi"]: return False
    return True

_TASK_STATE_CACHE = None


def clear_tweak_detection_cache():
    """Invalida las lecturas compartidas después de aplicar o revertir cambios."""
    global _TASK_STATE_CACHE
    _TASK_STATE_CACHE = None


def _scheduled_task_state(path, name):
    """Lee todas las tareas en una única llamada a PowerShell por análisis."""
    global _TASK_STATE_CACHE
    if _TASK_STATE_CACHE is None:
        try:
            raw = ps("Get-ScheduledTask | Select-Object TaskPath,TaskName,State | ConvertTo-Json -Compress")
            data = json.loads(raw) if raw.strip() else []
            if isinstance(data, dict):
                data = [data]
            cache = {}
            for item in data:
                key = (str(item.get("TaskPath", "")).lower(), str(item.get("TaskName", "")).lower())
                cache[key] = str(item.get("State", "")).lower()
            _TASK_STATE_CACHE = cache
        except Exception:
            _TASK_STATE_CACHE = {}
    return _TASK_STATE_CACHE.get((str(path).lower(), str(name).lower()))


def tweak_status(t):
    """Lee el estado actual: active, inactive, partial o unknown."""
    if not IS_WIN: return "unknown"
    checks = t.get("detect", t.get("actions", []))
    states = []
    for a in checks:
        try:
            kind = a.get("type")
            if kind == "reg":
                value, vtype = reg_get(a)
                want = a.get("value")
                if value is None:
                    states.append(want is None)
                elif a.get("vtype") == "REG_BINARY":
                    states.append(str(value).lower() == str(want).lower())
                else:
                    states.append(type(value) is type(want) and value == want)
                continue
            if kind == "scheduled_task":
                state = _scheduled_task_state(a["path"], a["name"])
                if state is None: states.append(None)
                else: states.append(state == str(a.get("state", "Disabled")).lower())
                continue
            # Sin una lectura fiable no inferimos el estado por el historial.
            states.append(None)
        except Exception:
            states.append(None)
    if not states or any(s is None for s in states): return "unknown"
    if all(states): return "active"
    if any(states): return "partial"
    return "inactive"

def coverage(tweaks, applied, include_locked=True):
    """% del peso de tweaks reversibles ya aplicado (cobertura, no promesa de FPS)."""
    pool = [t for t in tweaks if t["mode"] == "track" and (include_locked or not t.get("locked"))]
    tot = sum(t["w"] for t in pool)
    return 0 if not tot else round(100 * sum(t["w"] for t in pool if t["id"] in applied) / tot)


# ---------- medición ----------
def timer_resolution_ms():
    mn, mx, cur = ctypes.c_ulong(), ctypes.c_ulong(), ctypes.c_ulong()
    ctypes.windll.ntdll.NtQueryTimerResolution(ctypes.byref(mn), ctypes.byref(mx), ctypes.byref(cur))
    return cur.value / 10000.0

def sleep_probe(n=100):
    """Mide Sleep(1) real (kernel32, obedece la resolución del timer). Devuelve (promedio_ms, p95_ms)."""
    k, xs = ctypes.windll.kernel32, []
    for _ in range(n):
        t = time.perf_counter(); k.Sleep(1); xs.append((time.perf_counter() - t) * 1000)
    xs.sort()
    return statistics.fmean(xs), xs[int(len(xs) * 0.95) - 1]

DNS_SERVERS = [("Cloudflare", "1.1.1.1"), ("Google", "8.8.8.8"), ("Quad9", "9.9.9.9"), ("OpenDNS", "208.67.222.222"), ("AdGuard", "94.140.14.14"), ("CleanBrowsing", "185.228.168.9")]
_NAMES = ["www.google.com", "www.youtube.com", "www.wikipedia.org", "www.amazon.com", "www.twitch.tv", "www.reddit.com", "store.steampowered.com", "www.microsoft.com"]

def dns_query_packet(name, qid):
    return qid + b"\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00" + b"".join(bytes([len(p)]) + p.encode() for p in name.split(".")) + b"\x00\x00\x01\x00\x01"

def dns_rtt(server, port=53, rounds=6, timeout=1.5):
    """Mediana en ms de consultas UDP reales; None si no responde."""
    xs = []
    for i in range(rounds):
        qid = os.urandom(2); s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.settimeout(timeout)
        try:
            t = time.perf_counter(); s.sendto(dns_query_packet(_NAMES[i % len(_NAMES)], qid), (server, port))
            data, _ = s.recvfrom(1024); dt = (time.perf_counter() - t) * 1000
            if data[:2] == qid: xs.append(dt)
        except OSError: pass
        finally: s.close()
    return statistics.median(xs) if len(xs) >= max(2, rounds // 2) else None
