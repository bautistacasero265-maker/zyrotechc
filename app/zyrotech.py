"""ZyroTech Optimizer (Free / Pro). Ejecutar como Administrador."""
import os, sys, threading, time, webbrowser
import customtkinter as ctk
from tkinter import messagebox
import config, core, edition

PRO = edition.EDITION == "pro"
try:
    import pro_features as pro
except ImportError:
    pro = None
if PRO and pro is None: sys.exit("Falta pro_features.py")

# ---------- Identidad visual ZyroTech ----------
BG, SIDE, CARD, CARD2, LINE = "#080D13", "#0B131D", "#111C28", "#172636", "#26394B"
TEXT, MUTE, RED, GOLD, GREEN = "#F1F6FA", "#8FA4B7", "#FF647C", "#FFC86D", "#55E6AD"
CYAN, BLUE, PURPLE = "#72D8F4", "#5DA8FF", "#A78BFA"
ACC = CYAN if PRO else GREEN
ACC_TXT = "#071018"
HOVER = "#203648"
BADGE = {"Breaking": RED, "Seguridad": RED, "Irreversible": RED, "Beta": "#8B5CF6", "Energía": "#F59E0B", "Info": "#3B82F6", "Reinicio": "#3B82F6", "Una vez": "#6B7280", "PRO": GOLD}
WARN_BANNER = ("Algunos cambios marcados bajan la seguridad del equipo (Defender, Windows Update, virtualización o mitigaciones de CPU). "
               "Podés desmarcarlos cuando quieras.")
BAD_FOR_AUTO = {"Breaking", "Irreversible", "Beta", "Seguridad"}
ORDER = ["Privacidad", "Debloat", "Gaming", "Kernel", "Energía", "Red", "Periféricos", "Interfaz", "Servicios", "Tareas", "Inicio", "Mantenimiento", "Seguridad básica", "Seguridad"]


def load_tweaks():
    f = os.path.join(core.BASE, f"tweaks_{edition.EDITION}.json")
    if os.path.exists(f): return core.load_json(f, [])
    full = core.load_json(os.path.join(core.BASE, "..", "tweaks.json"), [])  # modo desarrollo
    if PRO: return full
    return [t if t["tier"] == "free" else {**{k: v for k, v in t.items() if k != "actions"}, "locked": True} for t in full]


def headless_revert():
    st = core.load_json(core.data_path("state.json"), {"applied": {}})
    for tid in list(reversed(list(st["applied"]))):
        core.run_undo(st["applied"].pop(tid)); core.save_json(core.data_path("state.json"), st)
    print("Todos los cambios de ZyroTech fueron revertidos.")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.wm_title("ZyroTech " + ("Pro" if PRO else "Free"))
        self.geometry("1280x800"); self.minsize(1000, 650); self.configure(fg_color=BG)
        self.f_logo = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.f_h1 = ctk.CTkFont(family="Segoe UI", size=27, weight="bold")
        self.f_h2 = ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
        self.f_b = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        self.f_n = ctk.CTkFont(family="Segoe UI", size=13)
        self.f_s = ctk.CTkFont(family="Segoe UI", size=11)
        self.f_big = ctk.CTkFont(family="Segoe UI", size=42, weight="bold")
        self.f_mono = ctk.CTkFont(family="Cascadia Code", size=11)
        ctk.set_widget_scaling(1.0)
        self.st = core.load_json(core.data_path("state.json"), {"applied": {}})
        self.hist = core.load_json(core.data_path("history.json"), [])
        self.settings = core.load_json(core.data_path("settings.json"), {"games": [], "last_latency": None})
        self.tweaks, self.vis, self.vars, self.hw, self.statuses = [], [], {}, None, {}
        self.restore_ok, self.cat, self.page, self.licensed, self.comps = False, None, None, not PRO, []
        self.booster = self.ram = None; self.pending_lbl = self.banner = None
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)
        self.topbar = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, height=68)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew"); self.topbar.grid_propagate(False)
        brand = ctk.CTkFrame(self.topbar, fg_color="transparent"); brand.pack(side="left", padx=22, pady=12)
        mark = ctk.CTkFrame(brand, fg_color=ACC, corner_radius=11, width=42, height=42); mark.pack(side="left"); mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="ZT", font=self.f_logo, text_color=ACC_TXT).pack(expand=True)
        namebox = ctk.CTkFrame(brand, fg_color="transparent"); namebox.pack(side="left", padx=12)
        ctk.CTkLabel(namebox, text="ZYROTECH", font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"), text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(namebox, text="OPTIMIZER SUITE", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color=MUTE).pack(anchor="w", pady=(1, 0))
        top_right = ctk.CTkFrame(self.topbar, fg_color="transparent"); top_right.pack(side="right", padx=22)
        self.edition_tag = ctk.CTkLabel(top_right, text="PRO EDITION" if PRO else "FREE EDITION", fg_color=CARD2, text_color=ACC, corner_radius=8, font=self.f_s, padx=12, pady=6)
        self.edition_tag.pack(side="right", padx=(10, 0))
        ctk.CTkLabel(top_right, text="●  LOCAL MODE", font=self.f_s, text_color=GREEN).pack(side="right")
        self.side = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, width=226); self.side.grid(row=1, column=0, sticky="nsew"); self.side.grid_propagate(False)
        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0); self.content.grid(row=1, column=1, sticky="nsew")
        bar = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, height=38); bar.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.status = ctk.CTkLabel(bar, text="Preparando análisis local...", font=self.f_s, text_color=MUTE, anchor="w"); self.status.pack(side="left", padx=18)
        self.prog = ctk.CTkProgressBar(bar, width=210, height=7, progress_color=ACC, fg_color=CARD2); self.prog.set(0); self.prog.pack(side="right", padx=18, pady=11)
        self._scan_busy = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.splash("Escaneando tu equipo...")
        threading.Thread(target=self.boot, daemon=True).start()

    # ---------- utilidades ----------
    def clear(self):
        for w in self.content.winfo_children(): w.destroy()
        self.pending_lbl = self.banner = None
    def splash(self, text):
        self.clear()
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.pack(expand=True)
        mark = ctk.CTkFrame(wrap, fg_color=ACC, corner_radius=18, width=76, height=76)
        mark.pack(pady=(0, 18)); mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="ZT", font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"), text_color=ACC_TXT).pack(expand=True)
        ctk.CTkLabel(wrap, text="ZYROTECH", font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"), text_color=TEXT).pack()
        ctk.CTkLabel(wrap, text="OPTIMIZER SUITE", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=ACC).pack(pady=(1, 18))
        self.splash_status = ctk.CTkLabel(wrap, text=text, font=self.f_n, text_color=MUTE)
        self.splash_status.pack()
        loader = ctk.CTkProgressBar(wrap, width=220, height=5, progress_color=ACC, fg_color=CARD2)
        loader.pack(pady=(18, 0)); loader.configure(mode="indeterminate"); loader.start()
    def say(self, text, frac=None):
        def f():
            self.status.configure(text=text)
            if frac is not None: self.prog.set(frac)
        self.after(0, f)
    def card(self, parent, **kw):
        fg = kw.pop("fg", CARD)
        kw.setdefault("corner_radius", 16)
        kw.setdefault("border_width", 1)
        kw.setdefault("border_color", LINE)
        return ctk.CTkFrame(parent, fg_color=fg, **kw)

    def btn(self, parent, text, cmd, kind="acc", **kw):
        styles = {
            "acc": (ACC, ACC_TXT, ACC),
            "ghost": (CARD2, TEXT, HOVER),
            "gold": (GOLD, "#111820", "#FFD88E"),
            "red": (RED, "#FFFFFF", "#FF8295"),
        }
        fg, tc, hover = styles[kind]
        return ctk.CTkButton(parent, text=text, command=cmd, fg_color=fg, text_color=tc,
                             hover_color=kw.pop("hover", None) or hover, corner_radius=10,
                             border_width=0, height=kw.pop("height", 38), font=self.f_b, **kw)

    def badge(self, parent, text):
        color = BADGE.get(text, CARD2)
        return ctk.CTkLabel(parent, text=f"  {text}  ", fg_color=color,
                            text_color="#0A0B0E" if text in ("PRO", "Energía") else "#FFFFFF",
                            corner_radius=7, font=self.f_s, height=22)

    def heading(self, text, sub=""):
        ctk.CTkLabel(self.content, text="CONTROL CENTER  /  ZYROTECH", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=30, pady=(24, 2))
        ctk.CTkLabel(self.content, text=text, font=self.f_h1, text_color=TEXT, anchor="w").pack(fill="x", padx=30, pady=(0, 0))
        if sub:
            ctk.CTkLabel(self.content, text=sub, font=self.f_n, text_color=MUTE, anchor="w",
                         wraplength=900, justify="left").pack(fill="x", padx=30, pady=(4, 14))
    def tname(self, tid): return next((t["name"] for t in self.tweaks if t["id"] == tid), "DNS personalizado" if tid == "DNS" else tid)
    def log(self, action, name, ok):
        self.hist.append({"t": time.strftime("%d/%m %H:%M"), "a": action, "n": name, "ok": ok}); self.hist = self.hist[-200:]
        core.save_json(core.data_path("history.json"), self.hist)
    def go_buy(self):
        url = (config.BUY_URL or "").strip()
        if not url or "XXXXXXXX" in url.upper() or "XXX" in url.upper():
            messagebox.showinfo("ZyroTech Pro", "El canal de compra todavía no está configurado.\n" + config.CONTACT)
            return
        webbrowser.open(url)
    def on_close(self):
        for x in (self.booster, self.ram):
            if x: x.stop()
        try:
            if PRO:
                core.set_timer(False, "manual")
                core.set_timer(False, "gamebooster")
        except Exception: pass
        self.destroy()

    # ---------- arranque ----------
    def boot(self):
        try: self.hw = core.hw_profile(core.scan_raw())
        except Exception:
            self.hw = {"nvidia": False, "amd": False, "intel": False, "cpu_intel": False, "cpu_amd": False, "ram": 8, "ssd": False, "laptop": False, "win11": False,
                       "wifi": False, "gpu_name": "No detectada", "cpu_name": "No detectado", "os": "Windows"}
        self.tweaks = load_tweaks(); self.vis = list(self.tweaks)
        core.clear_tweak_detection_cache()
        for t in self.vis:
            if t.get("mode") == "once": self.statuses[t["id"]] = "once"
            elif not core.applicable(t, self.hw): self.statuses[t["id"]] = "incompatible"
            else:
                try: self.statuses[t["id"]] = core.tweak_status(t)
                except Exception: self.statuses[t["id"]] = "unknown"
        if PRO:
            try: self.comps = pro.fingerprint()
            except Exception: self.comps = []
            lic = pro.load_license(); self.licensed = bool(lic) and pro.verify(lic, self.comps)[0]
        self.after(0, self.ready)

    def refresh_scan(self):
        """Vuelve a leer hardware y estado real de los tweaks sin confiar solo en el historial."""
        if self._scan_busy:
            return
        self._scan_busy = True
        self.say("Actualizando detección de hardware y tweaks...", 0.15)

        def work():
            try:
                hw = core.hw_profile(core.scan_raw())
                core.clear_tweak_detection_cache()
                statuses = {}
                for t in self.vis:
                    if t.get("mode") == "once":
                        statuses[t["id"]] = "once"
                    elif not core.applicable(t, hw):
                        statuses[t["id"]] = "incompatible"
                    else:
                        try:
                            statuses[t["id"]] = core.tweak_status(t)
                        except Exception:
                            statuses[t["id"]] = "unknown"
                self.after(0, lambda: self._finish_refresh(hw, statuses))
            except Exception as e:
                message = str(e)
                self.after(0, lambda: self._fail_refresh(message))

        threading.Thread(target=work, daemon=True).start()

    def _finish_refresh(self, hw, statuses):
        self.hw, self.statuses = hw, statuses
        for t in self.vis:
            tid = t["id"]
            var = self.vars.get(tid)
            if var is None:
                continue
            state = statuses.get(tid, "unknown")
            if state == "active":
                var.set(True)
            elif state in ("inactive", "partial", "incompatible", "unknown") and tid not in self.st["applied"]:
                var.set(False)
        self._scan_busy = False
        self.say("Detección actualizada. Los contadores reflejan el estado leído de Windows.", 0)
        if self.page:
            self.show(self.page)

    def _fail_refresh(self, message):
        self._scan_busy = False
        self.say("No se pudo completar el análisis.", 0)
        messagebox.showwarning("ZyroTech", f"No se pudo actualizar la detección: {message}")

    def ready(self):
        self.vars = {t["id"]: ctk.BooleanVar(value=(self.statuses.get(t["id"]) in ("active", "partial") or (self.statuses.get(t["id"]) == "unknown" and t["id"] in self.st["applied"]))) for t in self.vis}
        for w in self.side.winfo_children(): w.destroy()
        if PRO and not self.licensed: return self.gate_view()
        ctk.CTkLabel(self.side, text="TU ESPACIO", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color=MUTE).pack(anchor="w", padx=20, pady=(24, 10))
        self.nav = {}
        nav_items = [
            ("home", "⌂", "Panel"),
            ("opt", "◈", "Optimizar"),
            ("profiles", "▦", "Perfiles"),
            ("game", "▣", "Gaming"),
            ("net", "⌁", "Red"),
            ("hist", "◷", "Historial"),
            ("pro", "✦", "Licencia" if PRO else "Free vs Pro"),
        ]
        for key, glyph, label in nav_items:
            b = ctk.CTkButton(self.side, text=f"  {glyph}     {label}", anchor="w",
                              fg_color="transparent", text_color=MUTE, hover_color=CARD2,
                              corner_radius=10, height=43, font=self.f_b,
                              command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=12, pady=3); self.nav[key] = b
        foot = ctk.CTkFrame(self.side, fg_color="transparent")
        foot.pack(side="bottom", fill="x", padx=14, pady=16)
        ctk.CTkFrame(foot, fg_color=LINE, height=1).pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(foot, text="DETECCIÓN LOCAL", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"), text_color=MUTE).pack(anchor="w", padx=5)
        ctk.CTkLabel(foot, text="Tus datos permanecen en este equipo", font=self.f_s, text_color=MUTE).pack(anchor="w", padx=5, pady=(3, 10))
        if not PRO:
            self.btn(foot, "✦   Desbloquear Pro", self.go_buy, "gold", height=42).pack(fill="x")
        if not PRO:
            self.btn(self.side, "Desbloquear Pro", self.go_buy, "gold").pack(side="bottom", fill="x", padx=16, pady=18)
        if "--revert-all" in sys.argv: pass
        self.show("home")

    def show(self, key):
        self.page = key; self.clear()
        for k, b in self.nav.items(): b.configure(fg_color=CARD2 if k == key else "transparent", text_color=TEXT if k == key else MUTE)
        getattr(self, "page_" + key)()

    # ---------- activación Pro ----------
    def gate_view(self):
        self.clear(); code = pro.machine_code(self.comps) if self.comps else ""
        ctk.CTkLabel(self.content, text="Activar ZyroTech Pro", font=self.f_h1, text_color=GOLD).pack(pady=(70, 6))
        ctk.CTkLabel(self.content, text="La licencia queda atada a este equipo. Copiá el código, mandalo para recibir tu licencia y pegala acá.\n" + config.CONTACT,
                     font=self.f_n, text_color=MUTE, justify="center").pack()
        c = self.card(self.content); c.pack(padx=120, pady=22, fill="x")
        ctk.CTkLabel(c, text="Código de este equipo", font=self.f_b, text_color=TEXT, anchor="w").pack(fill="x", padx=18, pady=(14, 4))
        tb = ctk.CTkTextbox(c, height=64, fg_color=CARD2, font=ctk.CTkFont(family="Consolas", size=12)); tb.pack(fill="x", padx=18)
        tb.insert("1.0", code or "No se pudo leer el hardware. Ejecutá como Administrador."); tb.configure(state="disabled")
        self.btn(c, "Copiar código", lambda: (self.clipboard_clear(), self.clipboard_append(code), self.say("Código copiado.")), "ghost", width=150).pack(anchor="w", padx=18, pady=(8, 4))
        ctk.CTkLabel(c, text="Tu licencia", font=self.f_b, text_color=TEXT, anchor="w").pack(fill="x", padx=18, pady=(10, 4))
        self.lic_box = ctk.CTkTextbox(c, height=90, fg_color=CARD2, font=ctk.CTkFont(family="Consolas", size=12)); self.lic_box.pack(fill="x", padx=18)
        self.gate_msg = ctk.CTkLabel(c, text="", font=self.f_n, text_color=RED); self.gate_msg.pack(pady=(8, 0))
        self.btn(c, "Activar", self.activate, "gold", width=160).pack(pady=(4, 16))

    def activate(self):
        txt = self.lic_box.get("1.0", "end").strip(); ok, why = pro.verify(txt, self.comps)
        if not ok: return self.gate_msg.configure(text=why)
        pro.save_license(txt); self.licensed = True; self.ready()

    # ---------- Panel ----------
    def coverage(self, include_locked=True):
        applied = {i for i, s in self.statuses.items() if s == "active"}
        return core.coverage([t for t in self.vis if core.applicable(t, self.hw)], applied, include_locked)
    def page_home(self):
        self.heading("Panel principal", "Una lectura clara del estado de tu PC y de las optimizaciones que realmente corresponden a tu equipo.")

        eligible = [t for t in self.vis if t.get("mode") == "track" and core.applicable(t, self.hw)]
        active = sum(1 for t in eligible if self.statuses.get(t["id"]) == "active")
        partial = sum(1 for t in eligible if self.statuses.get(t["id"]) == "partial")
        pending = sum(1 for t in eligible if self.statuses.get(t["id"]) == "inactive" and not t.get("locked"))
        unknown = sum(1 for t in eligible if self.statuses.get(t["id"]) == "unknown")
        incompatible = sum(1 for t in self.vis if self.statuses.get(t["id"]) == "incompatible")
        coverage = self.coverage()

        hero = self.card(self.content, fg="#101E2A")
        hero.pack(fill="x", padx=30, pady=(0, 14))
        hero_left = ctk.CTkFrame(hero, fg_color="transparent")
        hero_left.pack(side="left", fill="both", expand=True, padx=20, pady=17)
        ctk.CTkLabel(hero_left, text="ZYROTECH  /  SYSTEM OVERVIEW", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=ACC, anchor="w").pack(anchor="w")
        ctk.CTkLabel(hero_left, text="Tu PC. Tu rendimiento. Tu control.", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                     text_color=TEXT, anchor="w").pack(anchor="w", pady=(4, 3))
        ctk.CTkLabel(hero_left, text="Análisis local · sin telemetría de ZyroTech · cambios reversibles cuando el tweak lo permite",
                     font=self.f_s, text_color=MUTE, anchor="w").pack(anchor="w")
        self.btn(hero, "↻  Actualizar análisis", self.refresh_scan, "ghost", width=175, height=40).pack(side="right", padx=20, pady=18)

        stats = ctk.CTkFrame(self.content, fg_color="transparent")
        stats.pack(fill="x", padx=30, pady=(0, 14))
        for i in range(4): stats.grid_columnconfigure(i, weight=1, uniform="stats")

        def stat(parent, col, label, value, note, tint):
            box = self.card(parent, fg=CARD)
            box.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0 if col == 3 else 6))
            ctk.CTkLabel(box, text=label.upper(), font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                         text_color=MUTE, anchor="w").pack(fill="x", padx=15, pady=(13, 1))
            ctk.CTkLabel(box, text=str(value), font=ctk.CTkFont(family="Segoe UI", size=29, weight="bold"),
                         text_color=tint, anchor="w").pack(fill="x", padx=15, pady=(0, 0))
            ctk.CTkLabel(box, text=note, font=self.f_s, text_color=MUTE, anchor="w").pack(fill="x", padx=15, pady=(0, 13))

        stat(stats, 0, "Tweaks activos", active, "Estado verificado en Windows", GREEN)
        stat(stats, 1, "Recomendados", pending, "Compatibles y aún pendientes", ACC)
        stat(stats, 2, "Parciales / sin lectura", partial + unknown, f"{partial} parciales · {unknown} no verificables", GOLD)
        stat(stats, 3, "No compatibles", incompatible, "Se omiten automáticamente", MUTE)

        row = ctk.CTkFrame(self.content, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=30, pady=(0, 12))
        row.grid_columnconfigure(0, weight=3, uniform="home")
        row.grid_columnconfigure(1, weight=2, uniform="home")
        row.grid_rowconfigure(0, weight=1)

        hw = self.hw
        device = self.card(row)
        device.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ctk.CTkLabel(device, text="HARDWARE DETECTADO", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=19, pady=(16, 10))
        specs = [
            ("CPU", hw.get("cpu_name", "No detectado")),
            ("GPU", hw.get("gpu_name", "No detectada")),
            ("MEMORIA", f'{hw.get("ram", 0)} GB RAM'),
            ("ALMACENAMIENTO", "SSD / NVMe" if hw.get("ssd") else "HDD / no identificado como SSD"),
            ("SISTEMA", hw.get("os", "Windows")),
            ("FORMATO", "Notebook" if hw.get("laptop") else "PC de escritorio"),
        ]
        spec_grid = ctk.CTkFrame(device, fg_color="transparent")
        spec_grid.pack(fill="both", expand=True, padx=16, pady=(0, 15))
        spec_grid.grid_columnconfigure(0, weight=1, uniform="spec")
        spec_grid.grid_columnconfigure(1, weight=1, uniform="spec")
        for idx, (label, value) in enumerate(specs):
            rr, cc = divmod(idx, 2)
            cell = ctk.CTkFrame(spec_grid, fg_color=CARD2, corner_radius=10)
            cell.grid(row=rr, column=cc, sticky="nsew", padx=3, pady=3)
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                         text_color=MUTE, anchor="w").pack(fill="x", padx=11, pady=(8, 1))
            ctk.CTkLabel(cell, text=value, font=self.f_n, text_color=TEXT, anchor="w",
                         wraplength=290, justify="left").pack(fill="x", padx=11, pady=(0, 8))

        overview = self.card(row)
        overview.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(overview, text="ESTADO DE OPTIMIZACIÓN", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=18, pady=(16, 4))
        ctk.CTkLabel(overview, text=f"{coverage}%", font=ctk.CTkFont(family="Segoe UI", size=39, weight="bold"),
                     text_color=TEXT).pack(anchor="w", padx=17, pady=(0, 0))
        pb = ctk.CTkProgressBar(overview, height=9, progress_color=ACC, fg_color=CARD2, corner_radius=6)
        pb.set(coverage / 100); pb.pack(fill="x", padx=19, pady=(3, 9))
        ctk.CTkLabel(overview, text=f"{active} ajustes activos de los compatibles y verificables.",
                     font=self.f_s, text_color=MUTE, wraplength=300, justify="left").pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkFrame(overview, fg_color=LINE, height=1).pack(fill="x", padx=18, pady=(0, 10))
        ctk.CTkLabel(overview, text="LATENCIA DE TEMPORIZACIÓN", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=MUTE, anchor="w").pack(fill="x", padx=18)
        self.lat_lbl = ctk.CTkLabel(overview, text=self.lat_text(), font=self.f_n, text_color=TEXT, anchor="w", justify="left")
        self.lat_lbl.pack(fill="x", padx=18, pady=(4, 7))
        self.btn(overview, "Medir ahora", self.measure, "ghost", width=130, height=34).pack(anchor="w", padx=18, pady=(0, 12))
        ctk.CTkLabel(overview, text="La medición no equivale a FPS ni garantiza menor latencia dentro del juego.",
                     font=ctk.CTkFont(family="Segoe UI", size=9), text_color=MUTE, wraplength=300,
                     justify="left").pack(fill="x", padx=18, pady=(0, 12))

        actions = self.card(self.content)
        actions.pack(fill="x", padx=30, pady=(0, 18))
        ctk.CTkLabel(actions, text="ACCIONES RÁPIDAS", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=18, pady=(13, 8))
        action_row = ctk.CTkFrame(actions, fg_color="transparent")
        action_row.pack(fill="x", padx=18, pady=(0, 14))
        self.btn(action_row, "◈  Ver recomendaciones", self.recommended, "acc", width=195).pack(side="left")
        self.btn(action_row, "＋  Punto de restauración", self.make_restore, "ghost", width=205).pack(side="left", padx=8)
        self.btn(action_row, "↶  Revertir todo", self.revert_all, "ghost", width=150).pack(side="left")
        if not PRO:
            self.badge(action_row, "PRO").pack(side="right", padx=8)

    def lat_text(self):
        l = self.settings.get("last_latency")
        return "Sin medir todavía." if not l else f'Timer: {l["res"]:.1f} ms\nSleep(1): {l["avg"]:.1f} ms (p95 {l["p95"]:.1f} ms)'
    def measure(self):
        self.lat_lbl.configure(text="Midiendo..."); self.say("Midiendo latencia...", 0.3)
        def work():
            try:
                res = core.timer_resolution_ms(); avg, p95 = core.sleep_probe(); self.settings["last_latency"] = {"res": res, "avg": avg, "p95": p95}
                core.save_json(core.data_path("settings.json"), self.settings)
                self.after(0, lambda: self.lat_lbl.configure(text=self.lat_text()) if self.page == "home" else None); self.say("Medición lista.", 0)
            except Exception as e: self.say(f"No se pudo medir: {e}", 0)
        threading.Thread(target=work, daemon=True).start()

    def recommended(self):
        for t in self.vis:
            ok = (not t.get("locked") and t["risk"] != "extreme" and t["mode"] == "track" and
                  t.get("badge") not in BAD_FOR_AUTO and core.applicable(t, self.hw) and
                  self.statuses.get(t["id"]) == "inactive")
            self.vars[t["id"]].set(self.vars[t["id"]].get() or ok)
        self.cat = ORDER[0]; self.show("opt")

    # ---------- Optimizar ----------
    def cats(self): return [m for m in ORDER if any(t["module"] == m and core.applicable(t, self.hw) for t in self.vis)]
    def page_opt(self):
        self.heading("Optimizar", "Activá lo que querés, revisá la lista de cambios pendientes y aplicá. Todo se puede revertir.")
        cats = self.cats(); self.cat = self.cat if self.cat in cats else (cats[0] if cats else None)
        body = ctk.CTkFrame(self.content, fg_color="transparent"); body.pack(fill="both", expand=True, padx=28)
        left = ctk.CTkScrollableFrame(body, width=240, fg_color=CARD, corner_radius=14); left.pack(side="left", fill="y", padx=(0, 12))
        for m in cats:
            n = sum(1 for t in self.vis if t["module"] == m and core.applicable(t, self.hw)); locked = sum(1 for t in self.vis if t["module"] == m and t.get("locked") and core.applicable(t, self.hw))
            txt = f"{m}  ({n})" + (f"  ·  {locked} PRO" if locked else "")
            ctk.CTkButton(left, text=txt, anchor="w", fg_color=CARD2 if m == self.cat else "transparent", text_color=TEXT if m == self.cat else MUTE, hover_color=CARD2,
                          corner_radius=8, height=34, font=self.f_n, command=lambda m=m: self.set_cat(m)).pack(fill="x", pady=1)
        right = ctk.CTkFrame(body, fg_color="transparent"); right.pack(side="left", fill="both", expand=True)
        top = ctk.CTkFrame(right, fg_color="transparent"); top.pack(fill="x", pady=(0, 8))
        self.search = ctk.CTkEntry(top, placeholder_text="Buscar en todas las categorías...", fg_color=CARD, border_color=LINE, height=36); self.search.pack(side="left", fill="x", expand=True)
        self.search.bind("<KeyRelease>", lambda e: self.fill_list())
        self.btn(top, "Marcar recomendados", self.recommended, "ghost", width=170).pack(side="left", padx=(8, 0))
        self.listf = ctk.CTkScrollableFrame(right, fg_color="transparent"); self.listf.pack(fill="both", expand=True)
        self.banner = ctk.CTkLabel(self.content, text="", fg_color=RED, text_color="white", font=self.f_s, wraplength=900, justify="left", corner_radius=8)
        bar = self.card(self.content); bar.pack(fill="x", padx=28, pady=(8, 10))
        self.pending_lbl = ctk.CTkLabel(bar, text="", font=self.f_b, text_color=TEXT); self.pending_lbl.pack(side="left", padx=18, pady=12)
        self.risk_ok = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(bar, text="Entiendo los riesgos", variable=self.risk_ok, font=self.f_s, fg_color=ACC, hover_color=ACC, text_color=MUTE).pack(side="left", padx=10)
        self.btn(bar, "Aplicar" if PRO else "Aplicar uno", self.on_apply, width=120).pack(side="right", padx=14)
        self.btn(bar, "Ver pendientes", self.show_pending, "ghost", width=140).pack(side="right")
        self.fill_list(); self.update_pending()

    def set_cat(self, m): self.cat = m; self.search_clear = True; self.show("opt")
    def fill_list(self):
        for w in self.listf.winfo_children(): w.destroy()
        q = self.search.get().strip().lower() if getattr(self, "search", None) and self.search.winfo_exists() else ""
        rows = [t for t in self.vis if (q in t["name"].lower() or q in t["module"].lower())] if q else [t for t in self.vis if t["module"] == self.cat]
        for t in rows[:70]: self.tweak_row(t)
        if len(rows) > 70: ctk.CTkLabel(self.listf, text=f"Mostrando 70 de {len(rows)}. Afiná la búsqueda.", font=self.f_s, text_color=MUTE).pack(pady=8)

    def tweak_row(self, t):
        locked = bool(t.get("locked")); compatible = core.applicable(t, self.hw); status = self.statuses.get(t["id"], "unknown")
        c = ctk.CTkFrame(self.listf, fg_color=CARD, corner_radius=12); c.pack(fill="x", pady=3)
        managed = t["id"] in self.st["applied"]
        disabled = locked or not compatible or (t["mode"] == "track" and status == "unknown") or (status in ("active", "partial") and not managed)
        sw = ctk.CTkSwitch(c, text="", variable=self.vars[t["id"]], onvalue=True, offvalue=False, command=self.update_pending, progress_color=ACC, width=46, state="disabled" if disabled else "normal")
        sw.pack(side="left", padx=(14, 6), pady=12)
        ctk.CTkLabel(c, text=t["name"], font=self.f_n, text_color=GOLD if locked else (RED if t["risk"] == "extreme" else TEXT), anchor="w", wraplength=430, justify="left").pack(side="left", fill="x", expand=True, padx=4)
        tags = ([("PRO")] if locked else []) + ([t["badge"]] if t.get("badge") else []) + (["Reinicio"] if t.get("reboot") else []) + (["Una vez"] if t["mode"] == "once" else [])
        state_label = ("No compatible" if not compatible else
                       "Acción puntual" if status == "once" else
                       "Activo" if status == "active" and managed else
                       "Activo detectado" if status == "active" else
                       "Parcialmente activo" if status == "partial" else
                       "Estado no disponible" if status == "unknown" else "Disponible")
        state_color = MUTE if not compatible or status == "unknown" else GREEN if status == "active" else TEXT
        ctk.CTkLabel(c, text=state_label, font=self.f_s, text_color=state_color).pack(side="right", padx=6)
        for b in tags: self.badge(c, b).pack(side="right", padx=3)
        ctk.CTkButton(c, text="i", width=28, height=28, corner_radius=14, fg_color=CARD2, text_color=MUTE, hover_color=LINE, command=lambda: self.info(t)).pack(side="right", padx=(0, 6))

    def info(self, t):
        w = ctk.CTkToplevel(self); w.wm_title(t["name"]); w.geometry("640x420"); w.configure(fg_color=BG); w.after(120, w.lift)
        ctk.CTkLabel(w, text=t["name"], font=self.f_b, text_color=TEXT, wraplength=590, justify="left").pack(anchor="w", padx=20, pady=(18, 4))
        if t.get("warn"): ctk.CTkLabel(w, text=f'{t["badge"]}: {t["warn"]}', font=self.f_n, text_color=GOLD, wraplength=590, justify="left").pack(anchor="w", padx=20)
        tb = ctk.CTkTextbox(w, fg_color=CARD, font=ctk.CTkFont(family="Consolas", size=11)); tb.pack(fill="both", expand=True, padx=20, pady=12)
        if t.get("locked"): tb.insert("1.0", "Este cambio es parte de Pro. El detalle técnico se muestra al desbloquearlo.")
        else:
            for a in t["actions"]:
                tb.insert("end", f'{a["path"]}\\{a["name"]} = {a["value"]}  ({a["vtype"]})\n' if a["type"] == "reg" else f'PowerShell: {a["cmd"]}\n')
            tb.insert("end", "\nSe puede revertir al valor anterior." if t["mode"] == "track" else "\nSe ejecuta una vez y no se puede deshacer.")
        tb.configure(state="disabled")

    # ---------- pendientes y aplicar ----------
    def pending(self):
        want = {t["id"] for t in self.vis if self.vars[t["id"]].get() and not t.get("locked")}; done = set(self.st["applied"])
        ap = [t for t in self.vis if t["id"] in want and core.applicable(t, self.hw) and
              self.statuses.get(t["id"]) != "unknown" and self.statuses.get(t["id"]) != "active" and
              (t["id"] not in done or t["mode"] == "once" or self.statuses.get(t["id"]) == "partial")]
        rv = [t for t in self.vis if t["id"] in done and t["id"] not in want]
        return ap, rv
    def update_pending(self):
        if not self.pending_lbl or not self.pending_lbl.winfo_exists(): return
        ap, rv = self.pending(); self.pending_lbl.configure(text=f"{len(ap)} por aplicar · {len(rv)} por revertir")
        ext = any(t["risk"] == "extreme" for t in ap)
        if ext: self.banner.configure(text="  " + WARN_BANNER + "  "); self.banner.pack(fill="x", padx=28, before=self.pending_lbl.master)
        else: self.banner.pack_forget()
    def show_pending(self):
        ap, rv = self.pending(); w = ctk.CTkToplevel(self); w.wm_title("Cambios pendientes"); w.geometry("560x460"); w.configure(fg_color=BG); w.after(120, w.lift)
        tb = ctk.CTkTextbox(w, fg_color=CARD, font=self.f_n); tb.pack(fill="both", expand=True, padx=18, pady=18)
        tb.insert("1.0", "POR APLICAR\n" + ("\n".join("  + " + t["name"] for t in ap) or "  (nada)") + "\n\nPOR REVERTIR\n" + ("\n".join("  - " + t["name"] for t in rv) or "  (nada)")); tb.configure(state="disabled")

    def need_admin(self):
        if core.is_admin(): return True
        messagebox.showerror("ZyroTech", "Ejecutá ZyroTech como Administrador."); return False
    def make_restore(self):
        if not self.need_admin(): return
        def w():
            try: self.say("Creando punto de restauración...", 0.4); core.create_restore_point(); self.restore_ok = True; self.say("Punto de restauración creado.", 0)
            except Exception as e: self.say(f"No se pudo crear el punto de restauración: {e}", 0)
        threading.Thread(target=w, daemon=True).start()

    def on_apply(self):
        ap, rv = self.pending()
        if not ap and not rv: return
        if not PRO and len(ap) > 1:
            return messagebox.showinfo("ZyroTech Free", "La edición Free aplica un tweak por vez. Dejé todos seleccionados; aplicá uno y después seguí con el próximo.")
        if any(t["risk"] == "extreme" for t in ap) and not self.risk_ok.get():
            return messagebox.showwarning("ZyroTech", "Marcá 'Entiendo los riesgos' para aplicar los cambios en rojo.")
        if not self.need_admin(): return
        if ap and not self.restore_ok and not messagebox.askyesno("ZyroTech", "Antes de aplicar hay que crear un punto de restauración de Windows.\n¿Crearlo ahora?"): return
        threading.Thread(target=lambda: self.run_apply(ap, rv), daemon=True).start()

    def run_apply(self, ap, rv, done_callback=None):
        errs, total, n = [], len(ap) + len(rv), 0
        try:
            if ap and not self.restore_ok:
                self.say("Creando punto de restauración...", 0.05); core.create_restore_point(); self.restore_ok = True
            if ap: self.say("Guardando backup del registro...", 0.1); core.backup_registry()
        except Exception as e:
            self.say("No se aplicó nada: falló el punto de restauración o el backup.", 0); return self.after(0, lambda: messagebox.showerror("ZyroTech", str(e)))
        for t in rv:
            n += 1; self.say(f"Revirtiendo: {t['name']}", n / total)
            e = core.run_undo(self.st["applied"].pop(t["id"], []))
            try:
                self.statuses[t["id"]] = core.tweak_status(t) if not e else "unknown"
            except Exception:
                self.statuses[t["id"]] = "unknown"
            core.save_json(core.data_path("state.json"), self.st); self.log("Revertido", t["name"], not e); errs += e
        reboot = False
        core.clear_tweak_detection_cache()
        for t in ap:
            n += 1; self.say(f"Aplicando: {t['name']}", n / total)
            try:
                undo = core.apply_tweak(t)
                if t["mode"] == "track":
                    # Conservar la primera copia de los valores originales si se
                    # completa un tweak parcialmente aplicado.
                    if t["id"] not in self.st["applied"]:
                        self.st["applied"][t["id"]] = undo
                    try:
                        self.statuses[t["id"]] = core.tweak_status(t)
                    except Exception:
                        self.statuses[t["id"]] = "unknown"
                    core.save_json(core.data_path("state.json"), self.st)
                self.log("Aplicado", t["name"], True); reboot = reboot or t.get("reboot", False)
            except Exception as e:
                errs.append(f'{t["name"]}: {e}'); self.log("Error", t["name"], False)
        def done():
            for t in ap:
                if t["mode"] == "once": self.vars[t["id"]].set(False)
            self.update_pending()
            if self.page == "opt" and getattr(self, "listf", None) and self.listf.winfo_exists(): self.fill_list()
            self.say(f"Listo: {len(ap)} aplicados, {len(rv)} revertidos" + (" · reiniciá para completar algunos cambios" if reboot else "") + (f" · {len(errs)} con error (ver Historial)" if errs else ""), 0)
            if done_callback: done_callback()
        self.after(0, done)

    def revert_all(self):
        if not self.st["applied"]: return self.say("No hay nada para revertir.", 0)
        if not self.need_admin() or not messagebox.askyesno("ZyroTech", "¿Revertir todos los cambios aplicados por ZyroTech?"): return
        def w():
            for i, tid in enumerate(list(reversed(list(self.st["applied"]))), 1):
                self.say(f"Revirtiendo: {self.tname(tid)}", i / max(1, len(self.st["applied"])))
                e = core.run_undo(self.st["applied"].pop(tid))
                try:
                    self.statuses[tid] = core.tweak_status(next(t for t in self.vis if t["id"] == tid)) if not e else "unknown"
                except Exception:
                    self.statuses[tid] = "unknown"
                core.save_json(core.data_path("state.json"), self.st); self.log("Revertido", self.tname(tid), not e)
            def ui():
                for v in self.vars.values(): v.set(False)
                self.update_pending(); self.say("Todo revertido.", 0)
            self.after(0, ui)
        threading.Thread(target=w, daemon=True).start()

    # ---------- Perfiles ----------
    def page_profiles(self):
        self.heading("Perfiles inteligentes", "Cada perfil usa los datos detectados de tu PC y el estado actual de Windows. Revisá cada cambio antes de aplicarlo.")
        hw = self.hw
        summary = self.card(self.content); summary.pack(fill="x", padx=28, pady=(0, 10))
        ctk.CTkLabel(summary, text="EQUIPO DETECTADO", font=self.f_s, text_color=ACC, anchor="w").pack(fill="x", padx=18, pady=(13, 4))
        ctk.CTkLabel(summary, text=f'{hw["cpu_name"]}   ·   {hw["gpu_name"]}   ·   {hw["ram"]} GB RAM   ·   {"Notebook" if hw["laptop"] else "Escritorio"}   ·   {"Windows 11" if hw["win11"] else "Windows 10 / anterior"}', font=self.f_n, text_color=TEXT, anchor="w", wraplength=900).pack(fill="x", padx=18, pady=(0, 5))
        self.btn(summary, "Actualizar detección", self.refresh_scan, "ghost", width=180).pack(anchor="e", padx=18, pady=(0, 10))
        if not PRO:
            c = self.card(self.content, border_width=1, border_color=GOLD); c.pack(fill="x", padx=28, pady=8)
            ctk.CTkLabel(c, text="Tres perfiles en ZyroTech Pro", font=self.f_h1, text_color=GOLD, anchor="w").pack(fill="x", padx=20, pady=(18, 6))
            ctk.CTkLabel(c, text="Lite para cambios conservadores · Medio para una selección equilibrada · Avanzado para la mayoría de los ajustes reversibles compatibles. Free conserva los cambios manuales y muestra cuáles ya están activos.", font=self.f_n, text_color=TEXT, wraplength=830, justify="left", anchor="w").pack(fill="x", padx=20)
            self.btn(c, "Conocer ZyroTech Pro", self.go_buy, "gold", width=220).pack(anchor="w", padx=20, pady=18)
            return
        for name, desc in [("Lite", "Selección breve y conservadora para empezar."), ("Medio", "Amplía la selección con red, periféricos, inicio y ajustes del sistema."), ("Avanzado", "La selección más amplia entre cambios reversibles y compatibles. Excluye acciones irreversibles y ajustes de seguridad." )]:
            result = pro.profile_preview(name, self.vis, self.hw, self.statuses)
            c = self.card(self.content, border_width=1, border_color=ACC if name == "Avanzado" else LINE); c.pack(fill="x", padx=28, pady=5)
            row = ctk.CTkFrame(c, fg_color="transparent"); row.pack(fill="x", padx=18, pady=(13, 2))
            ctk.CTkLabel(row, text=name, font=self.f_h1, text_color=ACC).pack(side="left")
            ctk.CTkLabel(row, text=f'{len(result["apply"])} para aplicar  ·  {len(result["active"])} activos  ·  {len(result["partial"])} parciales', font=self.f_b, text_color=GREEN).pack(side="right")
            ctk.CTkLabel(c, text=desc, font=self.f_n, text_color=MUTE, anchor="w").pack(fill="x", padx=18, pady=(0, 5))
            ctk.CTkLabel(c, text=f'{len(result["incompatible"])} no compatibles o sin lectura fiable  ·  {len(result["unsafe"])} excluidos por seguridad  ·  {len(result["locked"])} Pro bloqueados en esta edición', font=self.f_s, text_color=MUTE, anchor="w", wraplength=850).pack(fill="x", padx=18, pady=(0, 8))
            self.btn(c, "Revisar cambios", lambda n=name: self.preview_profile(n), "gold" if name == "Avanzado" else "ghost", width=180).pack(anchor="e", padx=18, pady=(0, 13))
        note = self.card(self.content); note.pack(fill="x", padx=28, pady=8)
        ctk.CTkLabel(note, text="Sin promesas de FPS", font=self.f_b, text_color=TEXT, anchor="w").pack(fill="x", padx=18, pady=(12, 2))
        ctk.CTkLabel(note, text="Los perfiles agrupan ajustes existentes del catálogo. El resultado depende de tu equipo y de las aplicaciones que uses; ningún aumento de FPS está garantizado.", font=self.f_s, text_color=MUTE, anchor="w", wraplength=850, justify="left").pack(fill="x", padx=18, pady=(0, 12))

    def preview_profile(self, name):
        result = pro.profile_preview(name, self.vis, self.hw, self.statuses)
        w = ctk.CTkToplevel(self); w.wm_title(f"Vista previa · {name}"); w.geometry("760x640"); w.minsize(640, 480); w.configure(fg_color=BG); w.after(120, w.lift)
        ctk.CTkLabel(w, text=f"Perfil {name}", font=self.f_h1, text_color=ACC, anchor="w").pack(fill="x", padx=20, pady=(18, 2))
        ctk.CTkLabel(w, text=f'{len(result["apply"])} disponibles para aplicar · {len(result["active"])} ya activos · {len(result["partial"])} parcialmente activos (se completan) · {len(result["incompatible"])} incompatibles o sin lectura · {len(result["unsafe"])} excluidos por seguridad', font=self.f_s, text_color=MUTE, anchor="w", wraplength=700).pack(fill="x", padx=20, pady=(0, 10))
        box = ctk.CTkScrollableFrame(w, fg_color="transparent"); box.pack(fill="both", expand=True, padx=16)
        choices = {}
        for t in result["apply"]:
            v = ctk.BooleanVar(value=True); choices[t["id"]] = v
            row = ctk.CTkFrame(box, fg_color=CARD, corner_radius=10); row.pack(fill="x", pady=2)
            ctk.CTkCheckBox(row, text=t["name"], variable=v, font=self.f_n, text_color=TEXT, fg_color=ACC, hover_color=ACC).pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(row, text=f'{t["module"]}{" · requiere reinicio" if t.get("reboot") else ""}', font=self.f_s, text_color=MUTE, anchor="w").pack(fill="x", padx=38, pady=(0, 7))
        for key, title, color in [("active", "YA ACTIVOS · SE OMITEN", GREEN), ("partial", "PARCIALMENTE ACTIVOS · SE COMPLETAN", GOLD), ("incompatible", "INCOMPATIBLES O SIN LECTURA FIABLE · SE OMITEN", MUTE), ("unsafe", "EXCLUIDOS POR SEGURIDAD", RED), ("locked", "BLOQUEADOS EN FREE", GOLD), ("once", "ACCIONES PUNTUALES · NO INCLUIDAS EN PERFILES", MUTE)]:
            items = result[key]
            if items:
                ctk.CTkLabel(box, text=f"{title} ({len(items)})", font=self.f_b, text_color=color, anchor="w").pack(fill="x", pady=(12, 3))
                for t in items:
                    ctk.CTkLabel(box, text=f'• {t["name"]}', font=self.f_s, text_color=MUTE, anchor="w", wraplength=690, justify="left").pack(fill="x", padx=8, pady=1)
        if not result["apply"]:
            ctk.CTkLabel(box, text="No hay cambios elegibles para aplicar con este perfil en este equipo.", font=self.f_n, text_color=MUTE).pack(pady=18)
        bar = ctk.CTkFrame(w, fg_color="transparent"); bar.pack(fill="x", padx=20, pady=14)
        self.btn(bar, "Marcar todos", lambda: [v.set(True) for v in choices.values()], "ghost", width=120).pack(side="left")
        self.btn(bar, "Desmarcar todos", lambda: [v.set(False) for v in choices.values()], "ghost", width=140).pack(side="left", padx=8)
        self.btn(bar, "Aplicar seleccionados", lambda: self.execute_profile(w, result["apply"], choices, name), "ghost", width=200).pack(side="right")
        self.btn(bar, "Aplicar todo", lambda: self.apply_all_profile(w, result["apply"], choices, name), "gold", width=140).pack(side="right", padx=(0, 8))

    def apply_all_profile(self, window, candidates, choices, name):
        """Selecciona todos los cambios elegibles del perfil y abre la confirmación final."""
        for variable in choices.values():
            variable.set(True)
        self.execute_profile(window, candidates, choices, name)

    def execute_profile(self, window, candidates, choices, name):
        selected = [t for t in candidates if choices[t["id"]].get()]
        if not selected: return messagebox.showinfo("ZyroTech", "No seleccionaste cambios para aplicar.", parent=window)
        if not self.need_admin(): return
        if not messagebox.askyesno("Confirmar perfil", f"Se aplicarán {len(selected)} cambios elegibles del perfil {name}. Los tweaks ya activos e incompatibles se omiten. ZyroTech intentará crear un punto de restauración y un backup antes de continuar. ¿Seguimos?", parent=window): return
        window.destroy(); self.say(f"Aplicando perfil {name}...", 0.05)
        threading.Thread(target=lambda: self.run_apply(selected, [], lambda: self.show("profiles")), daemon=True).start()

    # ---------- Gaming ----------
    def locked_note(self, c, text):
        r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0, 14)); self.badge(r, "PRO").pack(side="left")
        ctk.CTkLabel(r, text=text, font=self.f_s, text_color=MUTE).pack(side="left", padx=8); self.btn(r, "Desbloquear", self.go_buy, "gold", width=110, height=28).pack(side="right")
    def feature(self, title, desc, var=None, cmd=None):
        c = self.card(self.content); c.pack(fill="x", padx=28, pady=5)
        h = ctk.CTkFrame(c, fg_color="transparent"); h.pack(fill="x", padx=18, pady=(14, 2))
        ctk.CTkLabel(h, text=title, font=self.f_b, text_color=TEXT).pack(side="left")
        if PRO and cmd: ctk.CTkSwitch(h, text="", variable=var, command=cmd, progress_color=GOLD, width=46).pack(side="right")
        ctk.CTkLabel(c, text=desc, font=self.f_n, text_color=MUTE, anchor="w", wraplength=860, justify="left").pack(fill="x", padx=18, pady=(0, 12 if PRO else 6))
        if not PRO: self.locked_note(c, "Incluido en ZyroTech Pro")
    def page_game(self):
        self.heading("Gaming", "Funciones que actúan mientras jugás.")
        self.v_boost, self.v_timer, self.v_ram = (ctk.BooleanVar(value=bool(self.booster)), ctk.BooleanVar(), ctk.BooleanVar(value=bool(self.ram)))
        self.feature("Game Booster automático", "Detecta los juegos compatibles, solicita temporalmente el timer de 0,5 ms y usa prioridad Above Normal solo si el proceso estaba en Normal o inferior. Restaura la prioridad al terminar el juego; no vacía automáticamente la memoria en espera.", self.v_boost, self.toggle_boost)
        self.feature("Timer de 0.5 ms", "Solicita una resolución de temporizador de 0,5 ms mientras esta opción está encendida. Puede aumentar el consumo y no garantiza mejores FPS ni menor latencia.", self.v_timer, lambda: core.set_timer(self.v_timer.get(), "manual"))
        self.feature("Mantenimiento de memoria", "Opcional y desactivado por defecto. Solo purga la lista Standby cuando supera 40% de la RAM y queda menos de 15% libre. Windows suele gestionar esta memoria; purgarla puede forzar nuevas lecturas de disco y empeorar tirones.", self.v_ram, self.toggle_ram)
        c = self.card(self.content); c.pack(fill="x", padx=28, pady=5)
        ctk.CTkLabel(c, text="Perfiles Lite, Medio y Avanzado", font=self.f_b, text_color=TEXT, anchor="w").pack(fill="x", padx=18, pady=(14, 2))
        ctk.CTkLabel(c, text="Detectan compatibilidad y cambios ya activos, muestran una vista previa y te dejan elegir qué aplicar.", font=self.f_n, text_color=MUTE, anchor="w").pack(fill="x", padx=18)
        self.btn(c, "Ver perfiles", lambda: self.show("profiles"), "gold" if PRO else "ghost", width=150).pack(anchor="w", padx=18, pady=(8, 14))
        if PRO:
            g = self.card(self.content); g.pack(fill="x", padx=28, pady=5)
            ctk.CTkLabel(g, text="Agregar un juego al Game Booster (nombre del .exe)", font=self.f_b, text_color=TEXT, anchor="w").pack(fill="x", padx=18, pady=(14, 4))
            r = ctk.CTkFrame(g, fg_color="transparent"); r.pack(fill="x", padx=18, pady=(0, 14)); self.game_e = ctk.CTkEntry(r, placeholder_text="ej: eldenring.exe", fg_color=CARD2, border_color=LINE, width=300); self.game_e.pack(side="left")
            self.btn(r, "Agregar", self.add_game, "ghost", width=110).pack(side="left", padx=8)
            ctk.CTkLabel(r, text=f'{len(pro.GAMES) + len(self.settings["games"])} juegos detectados', font=self.f_s, text_color=MUTE).pack(side="left", padx=8)
    def toggle_boost(self):
        if self.booster: self.booster.stop(); self.booster = None
        if self.v_boost.get(): self.booster = pro.GameBooster(self.settings["games"], lambda m: self.say(m)); self.booster.start()
    def toggle_ram(self):
        if self.ram: self.ram.stop(); self.ram = None
        if self.v_ram.get(): self.ram = pro.RamCleaner(lambda m: self.say(m)); self.ram.start()
    def add_game(self):
        n = self.game_e.get().strip().lower()
        if n.endswith(".exe") and n not in self.settings["games"]:
            self.settings["games"].append(n); core.save_json(core.data_path("settings.json"), self.settings); self.show("game")
    def apply_profile(self, name):
        self.preview_profile(name)

    # ---------- Red ----------
    def page_net(self):
        self.heading("Red", "Probá qué servidor DNS responde más rápido desde tu conexión.")
        c = self.card(self.content); c.pack(fill="x", padx=28, pady=4)
        r = ctk.CTkFrame(c, fg_color="transparent"); r.pack(fill="x", padx=18, pady=14)
        self.btn(r, "Probar DNS", self.dns_test, width=150).pack(side="left")
        self.best_btn = self.btn(r, "Usar el más rápido", self.dns_apply, "gold", width=180, state="disabled" if PRO else "disabled"); self.best_btn.pack(side="left", padx=10)
        if PRO: self.btn(r, "Restaurar DNS automático", self.dns_reset, "ghost", width=210).pack(side="left")
        else: self.badge(r, "PRO").pack(side="left", padx=4); ctk.CTkLabel(r, text="Aplicar el mejor DNS es de Pro", font=self.f_s, text_color=MUTE).pack(side="left")
        self.dns_f = ctk.CTkFrame(self.content, fg_color="transparent"); self.dns_f.pack(fill="x", padx=28, pady=8); self.dns_best = None
    def dns_test(self):
        for w in self.dns_f.winfo_children(): w.destroy()
        def work():
            res = []
            for i, (name, ip) in enumerate(core.DNS_SERVERS, 1):
                self.say(f"Probando {name}...", i / len(core.DNS_SERVERS)); res.append((name, ip, core.dns_rtt(ip)))
            res.sort(key=lambda x: (x[2] is None, x[2] or 0)); self.after(0, lambda: self.dns_show(res)); self.say("Prueba de DNS terminada.", 0)
        threading.Thread(target=work, daemon=True).start()
    def dns_show(self, res):
        if self.page != "net": return
        mx = max([x[2] for x in res if x[2]] or [1])
        for i, (name, ip, ms) in enumerate(res):
            c = self.card(self.dns_f); c.pack(fill="x", pady=3)
            ctk.CTkLabel(c, text=f"{name}  ·  {ip}", font=self.f_n, text_color=GREEN if i == 0 and ms else TEXT, width=250, anchor="w").pack(side="left", padx=16, pady=10)
            pb = ctk.CTkProgressBar(c, height=8, progress_color=GREEN if i == 0 and ms else ACC, fg_color=CARD2); pb.set(0 if ms is None else max(0.04, 1 - ms / (mx * 1.15))); pb.pack(side="left", fill="x", expand=True, padx=10)
            ctk.CTkLabel(c, text="sin respuesta" if ms is None else f"{ms:.0f} ms", font=self.f_b, text_color=TEXT, width=100).pack(side="right", padx=16)
        self.dns_best = next(((n, ip) for n, ip, ms in res if ms), None)
        if PRO and self.dns_best: self.best_btn.configure(state="normal")
    def dns_apply(self):
        if not self.dns_best or not self.need_admin(): return
        ip = self.dns_best[1]; alt = {"1.1.1.1": "1.0.0.1", "8.8.8.8": "8.8.4.4", "9.9.9.9": "149.112.112.112", "208.67.222.222": "208.67.220.220"}.get(ip)
        try: self.st["applied"]["DNS"] = pro.apply_dns(ip, alt); core.save_json(core.data_path("state.json"), self.st); self.log("Aplicado", f"DNS {self.dns_best[0]}", True); self.say(f"DNS {self.dns_best[0]} aplicado.", 0)
        except Exception as e: self.say(f"No se pudo cambiar el DNS: {e}", 0)
    def dns_reset(self):
        if not self.need_admin(): return
        core.run_undo(self.st["applied"].pop("DNS", [{"type": "ps", "cmd": "Get-NetAdapter -Physical | Set-DnsClientServerAddress -ResetServerAddresses"}])); core.save_json(core.data_path("state.json"), self.st); self.say("DNS restaurado.", 0)

    # ---------- Historial ----------
    def page_hist(self):
        self.heading("Historial", "Lo que está aplicado ahora y el registro de cambios. Cada uno se revierte por separado.")
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent"); box.pack(fill="both", expand=True, padx=28, pady=(0, 12))
        ctk.CTkLabel(box, text=f'Aplicados ahora ({len(self.st["applied"])})', font=self.f_b, text_color=ACC, anchor="w").pack(fill="x", pady=(4, 4))
        for tid in list(self.st["applied"]):
            r = self.card(box); r.pack(fill="x", pady=2); ctk.CTkLabel(r, text=self.tname(tid), font=self.f_n, text_color=TEXT, anchor="w").pack(side="left", padx=16, pady=8)
            self.btn(r, "Revertir", lambda i=tid: self.revert_one(i), "ghost", width=90, height=28).pack(side="right", padx=12)
        ctk.CTkLabel(box, text="Registro", font=self.f_b, text_color=ACC, anchor="w").pack(fill="x", pady=(16, 4))
        for h in reversed(self.hist[-60:]):
            ctk.CTkLabel(box, text=f'{h["t"]}   {h["a"]}   {h["n"]}' + ("" if h["ok"] else "   (con error)"), font=self.f_s, text_color=MUTE if h["ok"] else RED, anchor="w").pack(fill="x")
    def revert_one(self, tid):
        if not self.need_admin(): return
        e = core.run_undo(self.st["applied"].pop(tid, []))
        try:
            self.statuses[tid] = core.tweak_status(next(t for t in self.vis if t["id"] == tid)) if not e else "unknown"
        except Exception:
            self.statuses[tid] = "unknown"
        core.save_json(core.data_path("state.json"), self.st); self.log("Revertido", self.tname(tid), not e)
        if tid in self.vars: self.vars[tid].set(False)
        self.show("hist")

    # ---------- Pro / licencia ----------
    def page_pro(self):
        if PRO:
            self.heading("Licencia", "Tu licencia queda guardada en este equipo y no funciona en otro.")
            c = self.card(self.content); c.pack(fill="x", padx=28)
            ctk.CTkLabel(c, text="Licencia activa en este equipo", font=self.f_b, text_color=GREEN, anchor="w").pack(fill="x", padx=18, pady=(16, 4))
            ctk.CTkLabel(c, text="Código de equipo", font=self.f_s, text_color=MUTE, anchor="w").pack(fill="x", padx=18)
            tb = ctk.CTkTextbox(c, height=60, fg_color=CARD2, font=ctk.CTkFont(family="Consolas", size=12)); tb.pack(fill="x", padx=18, pady=(2, 8)); tb.insert("1.0", pro.machine_code(self.comps)); tb.configure(state="disabled")
            ctk.CTkLabel(c, text="Si cambiás la placa madre o reinstalás con otro hardware y pierde la licencia, mandá este código para recibir una nueva.", font=self.f_s, text_color=MUTE, wraplength=820, justify="left").pack(fill="x", padx=18, pady=(0, 16))
            return
        self.heading("Free vs Pro", f"Pago único de {config.PRICE_TEXT}. Sin suscripción, sin renovaciones. Una licencia por equipo.")
        nfree = sum(1 for t in self.vis if not t.get("locked")); c = self.card(self.content); c.pack(fill="x", padx=28)
        rows = [("", "Free", "Pro"), ("Optimizaciones compatibles con tu PC", f"{nfree}", f"{len(self.vis)}"), ("Cambios de rendimiento (kernel, red, GPU, energía)", "Básicos", "Todos"),
                ("Perfiles listos (Gaming, Competitivo, Notebook...)", "—", "✓"), ("Game Booster automático", "—", "✓"), ("Timer de 0.5 ms", "—", "✓"), ("Limpiador de RAM", "—", "✓"),
                ("Aplicar el DNS más rápido", "solo ver ranking", "✓"), ("Punto de restauración, historial y reversión", "✓", "✓"), ("Pago único, sin suscripción", "", "✓")]
        for i, (a, b, p) in enumerate(rows):
            f = ctk.CTkFrame(c, fg_color=CARD2 if i == 0 else "transparent", corner_radius=8); f.pack(fill="x", padx=12, pady=(12 if i == 0 else 0, 0))
            for txt, w, col, anc in ((a, 470, TEXT, "w"), (b, 150, MUTE, "center"), (p, 150, GOLD, "center")):
                ctk.CTkLabel(f, text=txt, width=w, font=self.f_b if i == 0 else self.f_n, text_color=col, anchor=anc).pack(side="left", padx=8, pady=7)
        self.btn(c, "Comprar Pro", self.go_buy, "gold", width=200, height=44).pack(pady=18)


if __name__ == "__main__":
    if "--revert-all" in sys.argv: headless_revert(); sys.exit(0)
    if not core.IS_WIN: sys.exit("ZyroTech solo corre en Windows.")
    App().mainloop()
