"""ZyroTech Free · diagnóstico y ajustes locales de Windows."""
import os, sys, threading, time
import customtkinter as ctk
from tkinter import messagebox, filedialog
import core


# ---------- Identidad visual ZyroTech / nueva interfaz ----------
BG, SIDE, CARD, CARD2, LINE = "#090B13", "#101522", "#151C2B", "#1D2940", "#293750"
TEXT, MUTE, RED, GOLD, GREEN = "#F4F7FF", "#94A3B8", "#FF6685", "#FFC857", "#B8FF5C"
CYAN, BLUE, PURPLE = "#43D9FF", "#6EA8FF", "#A78BFA"
ACC = CYAN
ACC_TXT = "#07121B"
HOVER = "#293A56"
BADGE = {"Breaking": RED, "Seguridad": RED, "Irreversible": RED, "Beta": PURPLE, "Energía": GOLD, "Info": BLUE, "Reinicio": BLUE, "Una vez": "#77798E"}
WARN_BANNER = ("Algunos cambios marcados bajan la seguridad del equipo. Revisá cada acción antes de aplicarla.")
BAD_FOR_AUTO = {"Breaking", "Irreversible", "Beta", "Seguridad"}
ORDER = ["Privacidad", "Debloat", "Gaming", "Kernel", "Energía", "Red", "Periféricos", "Interfaz", "Servicios", "Tareas", "Inicio", "Mantenimiento", "Seguridad básica", "Seguridad"]





def load_tweaks():
    return core.load_json(os.path.join(core.BASE, "tweaks_free.json"), [])


def headless_revert():
    st = core.load_json(core.data_path("state.json"), {"applied": {}})
    for tid in list(reversed(list(st["applied"]))):
        core.run_undo(st["applied"].pop(tid)); core.save_json(core.data_path("state.json"), st)
    print("Todos los cambios de ZyroTech fueron revertidos.")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.wm_title("ZyroTech Free")
        self.geometry("1360x860")
        self.minsize(1040, 700)
        self.configure(fg_color=BG)

        self.f_logo = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.f_h1 = ctk.CTkFont(family="Segoe UI", size=31, weight="bold")
        self.f_h2 = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.f_b = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        self.f_n = ctk.CTkFont(family="Segoe UI", size=13)
        self.f_s = ctk.CTkFont(family="Segoe UI", size=11)
        self.f_big = ctk.CTkFont(family="Segoe UI", size=43, weight="bold")
        self.f_mono = ctk.CTkFont(family="Cascadia Code", size=11)
        ctk.set_widget_scaling(1.0)

        self.st = core.load_json(core.data_path("state.json"), {"applied": {}})
        self.hist = core.load_json(core.data_path("history.json"), [])
        self.settings = core.load_json(core.data_path("settings.json"), {"games": [], "last_latency": None})
        self.tweaks, self.vis, self.vars, self.hw, self.statuses = [], [], {}, None, {}
        self.restore_ok, self.cat, self.page = False, None, None
        self.search_query, self.risk_ack = "", False
        self.pending_lbl = self.banner = None

        # Layout principal: cabecera + navegación horizontal + espacio de trabajo + estado.
        self.grid_columnconfigure(0, weight=0, minsize=194)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.topbar = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, height=70)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.topbar.grid_propagate(False)

        brand = ctk.CTkFrame(self.topbar, fg_color="transparent")
        brand.pack(side="left", padx=25, pady=12)
        mark = ctk.CTkFrame(brand, fg_color=ACC, corner_radius=13, width=43, height=43)
        mark.pack(side="left")
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="Z", font=ctk.CTkFont(family="Segoe UI", size=26, weight="bold"),
                     text_color=ACC_TXT).pack(expand=True)
        namebox = ctk.CTkFrame(brand, fg_color="transparent")
        namebox.pack(side="left", padx=12)
        ctk.CTkLabel(namebox, text="ZYROTECH", font=self.f_logo, text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(namebox, text="PERFORMANCE LAB", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=MUTE).pack(anchor="w", pady=(0, 1))

        top_right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        top_right.pack(side="right", padx=24)
        ctk.CTkLabel(top_right, text="●  MODO LOCAL",
                     font=self.f_s, text_color=GREEN).pack(side="left", padx=(0, 16))
        self.edition_tag = ctk.CTkLabel(top_right, text="FREE",
                     fg_color=CARD2, text_color=ACC, corner_radius=8, font=self.f_s, padx=13, pady=7)
        self.edition_tag.pack(side="left")
        self.btn(top_right, "↻  ESCANEAR", self.refresh_scan, "ghost", height=34, width=125).pack(side="left", padx=(13, 0))

        self.navbar = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0,
                                   border_width=0, width=194)
        self.navbar.grid(row=1, column=0, sticky="nsew")
        self.navbar.grid_propagate(False)

        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.grid(row=1, column=1, sticky="nsew")

        footer = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, height=34)
        footer.grid(row=2, column=0, columnspan=2, sticky="ew")
        footer.grid_propagate(False)
        ctk.CTkFrame(footer, fg_color=ACC, width=3, height=14, corner_radius=2).pack(side="left", padx=(14, 0), pady=9)
        self.status = ctk.CTkLabel(footer, text="Preparando diagnóstico local...",
                                   font=self.f_s, text_color=MUTE, anchor="w")
        self.status.pack(side="left", padx=20)
        self.prog = ctk.CTkProgressBar(footer, width=170, height=6, progress_color=ACC, fg_color=CARD2)
        self.prog.set(0)
        self.prog.pack(side="right", padx=20, pady=12)

        self._scan_busy = False
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.splash("Analizando componentes y ajustes...")
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
                            text_color="#0A0B0E" if text == "Energía" else "#FFFFFF",
                            corner_radius=7, font=self.f_s, height=22)

    def heading(self, text, sub=""):
        top = ctk.CTkFrame(self.content, fg_color="transparent")
        top.pack(fill="x", padx=30, pady=(24, 15))
        eyebrow = ctk.CTkFrame(top, fg_color="transparent")
        eyebrow.pack(fill="x")
        ctk.CTkLabel(eyebrow, text="ZT  /  PERFORMANCE LAB",
                     font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(side="left")
        ctk.CTkLabel(eyebrow, text="●  LOCAL MODE", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=GREEN, anchor="e").pack(side="right")
        ctk.CTkLabel(top, text=text, font=self.f_h1, text_color=TEXT, anchor="w").pack(fill="x", pady=(7, 2))
        if sub:
            ctk.CTkLabel(top, text=sub, font=self.f_n, text_color="#9AAAC0", anchor="w",
                         wraplength=940, justify="left").pack(fill="x", pady=(3, 0))

    def tname(self, tid): return next((t["name"] for t in self.tweaks if t["id"] == tid), "DNS personalizado" if tid == "DNS" else tid)
    def log(self, action, name, ok):
        self.hist.append({"t": time.strftime("%d/%m %H:%M"), "a": action, "n": name, "ok": ok}); self.hist = self.hist[-200:]
        core.save_json(core.data_path("history.json"), self.hist)
    def on_close(self):
        self.destroy()

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
        # Esta edición funciona de forma independiente y local.

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
        self.vars = {
            t["id"]: ctk.BooleanVar(value=(
                self.statuses.get(t["id"]) in ("active", "partial")
                or (self.statuses.get(t["id"]) == "unknown" and t["id"] in self.st["applied"])
            )) for t in self.vis
        }
        for widget in self.navbar.winfo_children():
            widget.destroy()
        self.nav = {}
        nav_items = [
            ("home", "◫", "Inicio"),
            ("opt", "⌁", "Ajustes"),
            ("net", "⌘", "Red"),
            ("hist", "◷", "Actividad"),
            ("about", "⋯", "Acerca de"),
        ]
        self.nav_rails = {}
        ctk.CTkLabel(self.navbar, text="MENÚ PRINCIPAL", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color="#71849D", anchor="w").pack(fill="x", padx=19, pady=(25, 12))
        for key, glyph, label in nav_items:
            tile = ctk.CTkFrame(self.navbar, fg_color="transparent", corner_radius=11)
            tile.pack(fill="x", padx=10, pady=3)
            rail = ctk.CTkFrame(tile, fg_color="transparent", width=3, corner_radius=2)
            rail.pack(side="left", fill="y", padx=(0, 5), pady=8)
            button = ctk.CTkButton(
                tile, text=f"{glyph}     {label}", anchor="w",
                fg_color="transparent", text_color=MUTE, hover_color="#1B293B",
                corner_radius=9, height=44, font=self.f_n,
                command=lambda selected=key: self.show(selected)
            )
            button.pack(side="left", fill="x", expand=True)
            self.nav[key] = button
            self.nav_rails[key] = (tile, rail)
        ctk.CTkFrame(self.navbar, fg_color=LINE, height=1).pack(fill="x", padx=18, pady=(22, 14))
        edition = ctk.CTkFrame(self.navbar, fg_color="#141F2E", corner_radius=13,
                               border_width=1, border_color="#26384D")
        edition.pack(side="bottom", fill="x", padx=12, pady=15)
        ctk.CTkLabel(edition, text="ZYROTECH  /  FREE", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(edition, text="Optimización local para Windows.\nControlá cada cambio. Revertí cuando quieras.",
                     font=self.f_s, text_color="#9AAAC0", anchor="w", justify="left",
                     wraplength=155).pack(fill="x", padx=12, pady=(0, 12))
        self.show("home")

    def show(self, key):
        # Conservar el estado de Ajustes al navegar: búsqueda, categoría y confirmación.
        if self.page == "opt":
            try:
                if self.search.winfo_exists(): self.search_query = self.search.get()
            except Exception:
                pass
            try:
                self.risk_ack = bool(self.risk_ok.get())
            except Exception:
                pass
        self.page = key
        self.clear()
        for k, b in self.nav.items():
            active = (k == key)
            b.configure(fg_color="#1B293B" if active else "transparent",
                        text_color=TEXT if active else MUTE,
                        font=self.f_b if active else self.f_n)
            if k in getattr(self, "nav_rails", {}):
                tile, rail = self.nav_rails[k]
                tile.configure(fg_color="#142337" if active else "transparent")
                rail.configure(fg_color=ACC if active else "transparent")
        getattr(self, "page_" + key)()


    # ---------- Panel ----------
    def coverage(self):
        applied = {tid for tid, state in self.statuses.items() if state == "active"}
        applicable = [t for t in self.vis if core.applicable(t, self.hw)]
        return core.coverage(applicable, applied)

    def page_home(self):
        eligible = [t for t in self.vis if t.get("mode") == "track" and core.applicable(t, self.hw)]
        active = sum(1 for t in eligible if self.statuses.get(t["id"]) == "active")
        partial = sum(1 for t in eligible if self.statuses.get(t["id"]) == "partial")
        pending = sum(1 for t in eligible if self.statuses.get(t["id"]) == "inactive")
        unknown = sum(1 for t in eligible if self.statuses.get(t["id"]) == "unknown")
        incompatible = sum(1 for t in self.vis if self.statuses.get(t["id"]) == "incompatible")
        coverage = self.coverage()
        hw = self.hw or {}

        body = ctk.CTkScrollableFrame(self.content, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, padx=26, pady=(17, 20))

        hero = self.card(body, fg="#111B2B", border_color="#29445B", corner_radius=22)
        hero.pack(fill="x", pady=(0, 16))
        hero.grid_columnconfigure(0, weight=0, minsize=4)
        hero.grid_columnconfigure(1, weight=1)
        hero.grid_columnconfigure(2, weight=0, minsize=205)
        accent_rail = ctk.CTkFrame(hero, fg_color=ACC, width=4, corner_radius=2)
        accent_rail.grid(row=0, column=0, sticky="ns", padx=(0, 0), pady=20)
        left = ctk.CTkFrame(hero, fg_color="transparent")
        left.grid(row=0, column=1, sticky="nsew", padx=(20, 12), pady=25)
        ctk.CTkLabel(left, text="ZYROTECH  /  SYSTEM OVERVIEW",
                     font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x")
        ctk.CTkLabel(left, text="Tu PC. Tu rendimiento.\nTu control.",
                     font=ctk.CTkFont(family="Segoe UI", size=30, weight="bold"),
                     text_color=TEXT, anchor="w", justify="left").pack(fill="x", pady=(8, 8))
        ctk.CTkLabel(left, text="Un centro de control para revisar Windows, detectar ajustes compatibles y decidir qué querés cambiar. Sin promesas falsas de FPS.",
                     font=self.f_n, text_color="#B4C1D4", anchor="w", wraplength=610,
                     justify="left").pack(fill="x")
        ctk.CTkLabel(left, text="93 AJUSTES FREE   ·   DETECCIÓN LOCAL   ·   CONTROL Y REVERSIÓN",
                     font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=GREEN, anchor="w").pack(fill="x", pady=(12, 0))
        hero_actions = ctk.CTkFrame(left, fg_color="transparent")
        hero_actions.pack(fill="x", pady=(17, 0))
        self.btn(hero_actions, "Explorar ajustes  →", lambda: self.show("opt"), "acc", width=175, height=39).pack(side="left")
        self.btn(hero_actions, "Volver a analizar", self.refresh_scan, "ghost", width=150, height=39).pack(side="left", padx=9)
        right = ctk.CTkFrame(hero, fg_color="#17283A", corner_radius=18, width=205)
        right.grid(row=0, column=2, sticky="nsew", padx=(8, 18), pady=18)
        right.grid_propagate(False)
        ctk.CTkLabel(right, text="ESTADO DEL SISTEMA", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color="#9FB2C9").pack(anchor="w", padx=16, pady=(17, 4))
        ctk.CTkLabel(right, text=f"{coverage}%", font=ctk.CTkFont(family="Segoe UI", size=43, weight="bold"),
                     text_color=ACC).pack(anchor="w", padx=14)
        ctk.CTkLabel(right, text="de ajustes compatibles\nverificados como activos", font=self.f_s,
                     text_color="#B4C1D4", justify="left").pack(anchor="w", padx=16, pady=(0, 12))
        gauge = ctk.CTkProgressBar(right, height=7, progress_color=ACC, fg_color="#2A3B50", corner_radius=8)
        gauge.set(coverage / 100)
        gauge.pack(fill="x", padx=16, pady=(0, 17))

        metrics = ctk.CTkFrame(body, fg_color="transparent")
        metrics.pack(fill="x", pady=(0, 14))
        for i in range(4):
            metrics.grid_columnconfigure(i, weight=1, uniform="metric")
        def metric(i, title, value, detail, accent):
            c = self.card(metrics, corner_radius=16)
            c.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 6, 0 if i == 3 else 6))
            ctk.CTkFrame(c, fg_color=accent, height=3, corner_radius=2).pack(fill="x", padx=13, pady=(12, 9))
            ctk.CTkLabel(c, text=title.upper(), font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                         text_color=MUTE, anchor="w").pack(fill="x", padx=15, pady=(0, 2))
            ctk.CTkLabel(c, text=str(value), font=ctk.CTkFont(family="Segoe UI", size=34, weight="bold"),
                         text_color=accent, anchor="w").pack(fill="x", padx=15)
            ctk.CTkLabel(c, text=detail, font=self.f_s, text_color=MUTE,
                         anchor="w", wraplength=220, justify="left").pack(fill="x", padx=15, pady=(1, 14))
        metric(0, "Activos", active, "Leídos directamente en Windows", GREEN)
        metric(1, "Por revisar", pending, "Compatibles y pendientes", ACC)
        metric(2, "Parciales / desconocidos", partial + unknown, f"{partial} parciales · {unknown} sin lectura", GOLD)
        metric(3, "No compatibles", incompatible, "Se excluyen del análisis útil", MUTE)

        lower = ctk.CTkFrame(body, fg_color="transparent")
        lower.pack(fill="x")
        lower.grid_columnconfigure(0, weight=3, uniform="lower")
        lower.grid_columnconfigure(1, weight=2, uniform="lower")

        device = self.card(lower, corner_radius=17)
        device.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        ctk.CTkLabel(device, text="INFORMACIÓN DEL EQUIPO", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=18, pady=(16, 10))
        specs = [
            ("PROCESADOR", hw.get("cpu_name", "No detectado")),
            ("GRÁFICOS", hw.get("gpu_name", "No detectada")),
            ("MEMORIA", f'{hw.get("ram", 0)} GB RAM'),
            ("UNIDAD", "SSD / NVMe" if hw.get("ssd") else "HDD / no identificado como SSD"),
            ("WINDOWS", hw.get("os", "Windows")),
            ("FORMATO", "Notebook" if hw.get("laptop") else "Escritorio"),
        ]
        spec_grid = ctk.CTkFrame(device, fg_color="transparent")
        spec_grid.pack(fill="both", expand=True, padx=14, pady=(0, 15))
        spec_grid.grid_columnconfigure((0, 1), weight=1, uniform="spec")
        for idx, (label, value) in enumerate(specs):
            rr, cc = divmod(idx, 2)
            cell = ctk.CTkFrame(spec_grid, fg_color=CARD2, corner_radius=10)
            cell.grid(row=rr, column=cc, sticky="nsew", padx=3, pady=3)
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(family="Segoe UI", size=8, weight="bold"),
                         text_color=MUTE, anchor="w").pack(fill="x", padx=10, pady=(8, 1))
            ctk.CTkLabel(cell, text=value, font=self.f_s, text_color=TEXT, anchor="w",
                         wraplength=285, justify="left").pack(fill="x", padx=10, pady=(0, 8))

        overview = self.card(lower, corner_radius=17)
        overview.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        ctk.CTkLabel(overview, text="ESTADO GENERAL", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=18, pady=(16, 6))
        ctk.CTkLabel(overview, text=f"{active} de {max(1, len(eligible))}",
                     font=ctk.CTkFont(family="Segoe UI", size=32, weight="bold"),
                     text_color=TEXT, anchor="w").pack(fill="x", padx=18)
        ctk.CTkLabel(overview, text="ajustes compatibles y comprobables activos",
                     font=self.f_s, text_color=MUTE, anchor="w").pack(fill="x", padx=18, pady=(0, 9))
        pb = ctk.CTkProgressBar(overview, height=9, progress_color=ACC, fg_color=CARD2, corner_radius=6)
        pb.set(coverage / 100)
        pb.pack(fill="x", padx=18, pady=(0, 13))
        ctk.CTkFrame(overview, fg_color=LINE, height=1).pack(fill="x", padx=18, pady=(0, 11))
        ctk.CTkLabel(overview, text="MEDICIÓN DE TEMPORIZACIÓN", font=ctk.CTkFont(family="Segoe UI", size=8, weight="bold"),
                     text_color=MUTE, anchor="w").pack(fill="x", padx=18)
        self.lat_lbl = ctk.CTkLabel(overview, text=self.lat_text(), font=self.f_s, text_color=TEXT,
                                    anchor="w", justify="left")
        self.lat_lbl.pack(fill="x", padx=18, pady=(4, 8))
        self.btn(overview, "Medir ahora", self.measure, "ghost", width=130, height=33).pack(anchor="w", padx=18)
        ctk.CTkLabel(overview, text="La medición no equivale a FPS ni garantiza menor latencia en juegos.",
                     font=ctk.CTkFont(family="Segoe UI", size=9), text_color=MUTE,
                     wraplength=310, justify="left").pack(fill="x", padx=18, pady=(10, 14))

        actions = self.card(body, corner_radius=17)
        actions.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(actions, text="SIGUIENTE PASO", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=18, pady=(14, 5))
        ctk.CTkLabel(actions, text="Revisá los cambios antes de aplicarlos. Los que ya están activos o no corresponden a tu PC se omiten.",
                     font=self.f_n, text_color=MUTE, anchor="w", wraplength=850,
                     justify="left").pack(fill="x", padx=18, pady=(0, 11))
        row = ctk.CTkFrame(actions, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 15))
        self.btn(row, "Ver ajustes recomendados", self.recommended, "acc", width=200).pack(side="left")
        self.btn(row, "Crear punto de restauración", self.make_restore, "ghost", width=215).pack(side="left", padx=8)
        self.btn(row, "Revertir todos los cambios", self.revert_all, "ghost", width=195).pack(side="left")
        self.btn(row, "Exportar informe", self.export_report, "ghost", width=150).pack(side="left", padx=8)

    def lat_text(self):
        l = self.settings.get("last_latency")
        return "Sin medir todavía." if not l else f'Timer: {l["res"]:.1f} ms\nSleep(1): {l["avg"]:.1f} ms (p95 {l["p95"]:.1f} ms)'

    def export_report(self):
        """Exporta un resumen legible del diagnóstico sin incluir datos personales."""
        if not self.hw:
            return messagebox.showinfo("ZyroTech", "El análisis del equipo todavía no está disponible.")
        path = filedialog.asksaveasfilename(
            parent=self, title="Guardar informe de ZyroTech",
            defaultextension=".txt", initialfile="ZyroTech-informe.txt",
            filetypes=[("Informe de texto", "*.txt")]
        )
        if not path:
            return
        eligible = [t for t in self.vis if core.applicable(t, self.hw)]
        counts = {
            "Activos": sum(self.statuses.get(t["id"]) == "active" for t in eligible),
            "Parciales": sum(self.statuses.get(t["id"]) == "partial" for t in eligible),
            "Pendientes": sum(self.statuses.get(t["id"]) == "inactive" for t in eligible),
            "No verificables": sum(self.statuses.get(t["id"]) == "unknown" for t in eligible),
            "No compatibles": sum(self.statuses.get(t["id"]) == "incompatible" for t in self.vis),
        }
        hw = self.hw
        lines = [
            "ZYROTECH FREE — INFORME DE DIAGNÓSTICO",
            "=" * 46,
            f"Fecha: {time.strftime('%d/%m/%Y %H:%M:%S')}",
            "",
            "EQUIPO",
            f"Procesador: {hw.get('cpu_name', 'No detectado')}",
            f"Gráficos: {hw.get('gpu_name', 'No detectada')}",
            f"Memoria: {hw.get('ram', 0)} GB RAM",
            f"Almacenamiento: {'SSD / NVMe' if hw.get('ssd') else 'HDD / no identificado como SSD'}",
            f"Windows: {hw.get('os', 'Windows')}",
            f"Formato: {'Notebook' if hw.get('laptop') else 'Escritorio'}",
            "",
            "ESTADO DE AJUSTES",
            f"Catálogo incluido: {len(self.vis)}",
            f"Compatibles con este equipo: {len(eligible)}",
        ]
        lines.extend(f"{label}: {value}" for label, value in counts.items())
        lines.extend(["", "DETALLE"])
        for tweak in self.vis:
            state = self.statuses.get(tweak["id"], "unknown")
            label = {
                "active": "Activo", "partial": "Parcial", "inactive": "Pendiente",
                "unknown": "No verificable", "incompatible": "No compatible",
                "once": "Acción puntual"
            }.get(state, "Desconocido")
            lines.append(f"[{label}] {tweak['module']} — {tweak['name']}")
        lines.extend([
            "", "NOTA",
            "Este informe describe el estado detectado en el momento del análisis.",
            "No representa una puntuación de rendimiento ni garantiza mejoras de FPS.",
            "El informe no incluye nombres de usuario, rutas personales ni el contenido del registro."
        ])
        try:
            with open(path, "w", encoding="utf-8") as report:
                report.write("\\n".join(lines))
            self.say("Informe exportado correctamente.", 0)
            messagebox.showinfo("ZyroTech", "El informe se guardó correctamente.")
        except OSError as error:
            messagebox.showerror("ZyroTech", f"No se pudo guardar el informe: {error}")

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
        for tweak in self.vis:
            suitable = (
                tweak["risk"] != "extreme"
                and tweak["mode"] == "track"
                and tweak.get("badge") not in BAD_FOR_AUTO
                and core.applicable(tweak, self.hw)
                and self.statuses.get(tweak["id"]) == "inactive"
            )
            self.vars[tweak["id"]].set(self.vars[tweak["id"]].get() or suitable)
        self.cat = ORDER[0]
        self.search_query = ""
        self.show("opt")

    def cats(self): return [m for m in ORDER if any(t["module"] == m and core.applicable(t, self.hw) for t in self.vis)]
    def page_opt(self):
        self.heading("Biblioteca de ajustes", "Explorá los ajustes Free por categoría. ZyroTech detecta cuáles ya están activos y conserva tus selecciones mientras navegás.")
        cats = self.cats(); self.cat = self.cat if self.cat in cats else (cats[0] if cats else None)
        body = ctk.CTkFrame(self.content, fg_color="transparent"); body.pack(fill="both", expand=True, padx=28)
        left = ctk.CTkScrollableFrame(body, width=218, fg_color=SIDE, corner_radius=16, border_width=1, border_color=LINE); left.pack(side="left", fill="y", padx=(0, 14))
        self.cat_buttons = {}
        ctk.CTkLabel(left, text="CATEGORÍAS", font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                     text_color="#71849D", anchor="w").pack(fill="x", padx=13, pady=(13, 8))
        for m in cats:
            n = sum(1 for t in self.vis if t["module"] == m and core.applicable(t, self.hw))
            icon = {"Privacidad":"◈","Debloat":"✦","Gaming":"▣","Kernel":"⌘","Energía":"ϟ","Red":"⌁","Periféricos":"⌖","Interfaz":"▤","Servicios":"⚙","Tareas":"◷","Inicio":"➜","Mantenimiento":"⌁","Seguridad básica":"◇","Seguridad":"⬡"}.get(m, "•")
            selected = m == self.cat
            tile = ctk.CTkFrame(left, fg_color="#1B2C40" if selected else "transparent", corner_radius=11)
            tile.pack(fill="x", pady=3)
            rail = ctk.CTkFrame(tile, fg_color=ACC if selected else "transparent", width=3, corner_radius=2)
            rail.pack(side="left", fill="y", padx=(0, 5), pady=7)
            button = ctk.CTkButton(tile, text=f"{icon}   {m}", anchor="w", fg_color="transparent",
                          text_color=TEXT if selected else MUTE, hover_color=CARD2,
                          corner_radius=9, height=42, font=self.f_b if selected else self.f_n,
                          command=lambda m=m: self.set_cat(m))
            button.pack(side="left", fill="x", expand=True)
            self.cat_buttons[m] = (tile, rail, button)
            ctk.CTkLabel(tile, text=str(n), fg_color="#26384D" if selected else CARD2, text_color=ACC if selected else MUTE, corner_radius=7,
                         font=self.f_s, width=28, height=22).pack(side="right", padx=8)
        right = ctk.CTkFrame(body, fg_color="transparent"); right.pack(side="left", fill="both", expand=True)
        top = ctk.CTkFrame(right, fg_color="transparent"); top.pack(fill="x", pady=(0, 10))
        self.category_title = ctk.CTkLabel(top, text=self.cat or "Ajustes", font=self.f_h2, text_color=TEXT, anchor="w")
        self.category_title.pack(side="left", padx=(2, 12))
        self.result_count = ctk.CTkLabel(top, text="", font=self.f_s, text_color=MUTE)
        self.result_count.pack(side="left")
        self.search = ctk.CTkEntry(top, placeholder_text="Buscar ajustes...", fg_color=CARD, border_color=LINE, height=43, corner_radius=12, border_width=1)
        self.search.pack(side="right", fill="x", expand=True, padx=(14, 0))
        if self.search_query: self.search.insert(0, self.search_query)
        self.search.bind("<KeyRelease>", lambda e: self.fill_list())
        self.btn(top, "✦  Recomendarme", self.recommended, "ghost", width=170, height=40).pack(side="left", padx=(8, 0))
        self.listf = ctk.CTkScrollableFrame(right, fg_color="transparent"); self.listf.pack(fill="both", expand=True)
        self.banner = ctk.CTkLabel(self.content, text="", fg_color=RED, text_color="white", font=self.f_s, wraplength=900, justify="left", corner_radius=8)
        bar = self.card(self.content); bar.pack(fill="x", padx=28, pady=(8, 10))
        self.pending_lbl = ctk.CTkLabel(bar, text="", font=self.f_b, text_color=TEXT); self.pending_lbl.pack(side="left", padx=18, pady=12)
        self.risk_ok = ctk.BooleanVar(value=self.risk_ack)
        ctk.CTkCheckBox(bar, text="Entiendo los riesgos", variable=self.risk_ok, font=self.f_s, fg_color=ACC, hover_color=ACC, text_color=MUTE).pack(side="left", padx=10)
        self.btn(bar, "Aplicar uno", self.on_apply, width=145, height=40).pack(side="right", padx=14)
        self.btn(bar, "Ver pendientes", self.show_pending, "ghost", width=140).pack(side="right")
        self.fill_list(); self.update_pending()

    def set_cat(self, m):
        # Actualiza solo el panel de resultados; no reconstruye la ventana ni los controles.
        self.cat = m
        for name, (tile, rail, button) in getattr(self, "cat_buttons", {}).items():
            active = name == m
            tile.configure(fg_color="#1B2C40" if active else "transparent")
            rail.configure(fg_color=ACC if active else "transparent")
            button.configure(text_color=TEXT if active else MUTE,
                             font=self.f_b if active else self.f_n)
        if getattr(self, "category_title", None) and self.category_title.winfo_exists():
            self.category_title.configure(text=m)
        self.fill_list()
    def fill_list(self):
        for w in self.listf.winfo_children(): w.destroy()
        q = self.search.get().strip().lower() if getattr(self, "search", None) and self.search.winfo_exists() else ""
        rows = [t for t in self.vis if t["module"] == self.cat]
        if q:
            rows = [t for t in self.vis if q in t["name"].lower() or q in t["module"].lower()]
        if getattr(self, "category_title", None) and self.category_title.winfo_exists():
            self.category_title.configure(text="Resultados de búsqueda" if q else (self.cat or "Ajustes"))
        if getattr(self, "result_count", None) and self.result_count.winfo_exists():
            self.result_count.configure(text=f"{len(rows)} ajustes")
        if not rows:
            empty = self.card(self.listf, fg=SIDE, corner_radius=16)
            empty.pack(fill="x", pady=8)
            ctk.CTkLabel(empty, text="No encontramos ajustes", font=self.f_h2, text_color=TEXT).pack(anchor="w", padx=20, pady=(20, 4))
            ctk.CTkLabel(empty, text="Probá con otro término o elegí otra categoría.", font=self.f_n, text_color=MUTE).pack(anchor="w", padx=20, pady=(0, 20))
        for t in rows[:70]: self.tweak_row(t)
        if len(rows) > 70: ctk.CTkLabel(self.listf, text=f"Mostrando 70 de {len(rows)}. Afiná la búsqueda.", font=self.f_s, text_color=MUTE).pack(pady=8)

    def tweak_row(self, tweak):
        compatible = core.applicable(tweak, self.hw)
        status = self.statuses.get(tweak["id"], "unknown")
        card = self.card(self.listf, fg="#121A28", corner_radius=15, border_color="#29384C")
        card.pack(fill="x", pady=5)
        card.grid_columnconfigure(1, weight=1)
        accent = GREEN if status == "active" else GOLD if status == "partial" else RED if tweak.get("risk") == "extreme" else ACC
        ctk.CTkFrame(card, fg_color=accent, width=3, corner_radius=2).pack(side="left", fill="y", padx=(0, 12), pady=10)
        managed = tweak["id"] in self.st["applied"]
        disabled = (
            not compatible
            or (tweak["mode"] == "track" and status == "unknown")
            or (status == "active" and not managed)
        )
        switch = ctk.CTkSwitch(
            card, text="", variable=self.vars[tweak["id"]], onvalue=True, offvalue=False,
            command=self.update_pending, progress_color=ACC, width=42,
            state="disabled" if disabled else "normal"
        )
        switch.pack(side="left", padx=(13, 5), pady=11)
        title_color = RED if tweak["risk"] == "extreme" else TEXT
        titlebox = ctk.CTkFrame(card, fg_color="transparent")
        titlebox.pack(side="left", fill="x", expand=True, padx=5, pady=11)
        ctk.CTkLabel(
            titlebox, text=tweak["name"], font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"), text_color=title_color,
            anchor="w", wraplength=470, justify="left"
        ).pack(fill="x", anchor="w")
        hint = tweak.get("warn") or ("Requiere reinicio para completar el cambio" if tweak.get("reboot") else "Reversible desde Actividad" if tweak.get("mode") == "track" else "Herramienta puntual de mantenimiento")
        ctk.CTkLabel(titlebox, text=hint, font=self.f_s, text_color="#9AAAC0",
                     anchor="w", wraplength=470, justify="left").pack(fill="x", anchor="w", pady=(4, 0))
        tags = ([tweak["badge"]] if tweak.get("badge") else [])
        if tweak.get("reboot"):
            tags.append("Reinicio")
        if tweak["mode"] == "once":
            tags.append("Una vez")
        status_label = (
            "No compatible" if not compatible else
            "Acción puntual" if status == "once" else
            "Activo" if status == "active" and managed else
            "Activo detectado" if status == "active" else
            "Parcialmente activo" if status == "partial" else
            "Estado no disponible" if status == "unknown" else "Disponible"
        )
        status_color = MUTE if not compatible or status == "unknown" else GREEN if status == "active" else GOLD if status == "partial" else CYAN
        status_bg = "#193A31" if status == "active" else "#3C3422" if status == "partial" else "#26384D" if status == "inactive" else "#2A2E3B"
        ctk.CTkLabel(card, text=f"  {status_label}  ", fg_color=status_bg, corner_radius=8,
                     font=self.f_s, text_color=status_color, height=25).pack(side="right", padx=9)
        for tag in tags:
            self.badge(card, tag).pack(side="right", padx=3)
        ctk.CTkButton(
            card, text="···", width=32, height=30, corner_radius=9,
            fg_color="#202D40", text_color="#B7C8DC", hover_color=HOVER,
            command=lambda item=tweak: self.info(item)
        ).pack(side="right", padx=(0, 9))

    def info(self, tweak):
        window = ctk.CTkToplevel(self)
        window.wm_title(tweak["name"])
        window.geometry("640x420")
        window.configure(fg_color=BG)
        window.after(120, window.lift)
        ctk.CTkLabel(
            window, text=tweak["name"], font=self.f_b, text_color=TEXT,
            wraplength=590, justify="left"
        ).pack(anchor="w", padx=20, pady=(18, 4))
        if tweak.get("warn"):
            ctk.CTkLabel(
                window, text=f'{tweak.get("badge", "Aviso")}: {tweak["warn"]}',
                font=self.f_n, text_color=GOLD, wraplength=590, justify="left"
            ).pack(anchor="w", padx=20)
        textbox = ctk.CTkTextbox(window, fg_color=CARD, font=ctk.CTkFont(family="Consolas", size=11))
        textbox.pack(fill="both", expand=True, padx=20, pady=12)
        for action in tweak["actions"]:
            if action["type"] == "reg":
                textbox.insert("end", f'{action["path"]}\\{action["name"]} = {action["value"]} ({action.get("vtype", "REG_DWORD")})\n')
            elif action["type"] == "ps":
                textbox.insert("end", f'PowerShell: {action["cmd"]}\n')
            elif action["type"] == "scheduled_task":
                textbox.insert("end", f'Tarea: {action["path"]}\\{action["name"]}\n')
        ending = "Se puede revertir al valor anterior." if tweak["mode"] == "track" else "Acción puntual: no tiene reversión automática."
        textbox.insert("end", "\n" + ending)
        textbox.configure(state="disabled")

    def pending(self):
        selected_ids = {t["id"] for t in self.vis if self.vars[t["id"]].get()}
        applied_ids = set(self.st["applied"])
        apply_items = [
            t for t in self.vis
            if t["id"] in selected_ids
            and core.applicable(t, self.hw)
            and self.statuses.get(t["id"]) not in ("unknown", "active")
            and (t["id"] not in applied_ids or t["mode"] == "once" or self.statuses.get(t["id"]) == "partial")
        ]
        revert_items = [
            t for t in self.vis
            if t["id"] in applied_ids and t["id"] not in selected_ids
        ]
        return apply_items, revert_items

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
        if len(ap) > 1:
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
                    self.statuses[t["id"]] = "active"  # estado provisional hasta verificar al final
                    core.save_json(core.data_path("state.json"), self.st)
                self.log("Aplicado", t["name"], True); reboot = reboot or t.get("reboot", False)
            except Exception as e:
                errs.append(f'{t["name"]}: {e}'); self.log("Error", t["name"], False)
        # Verificar todos los cambios después de que el lote terminó, no durante
        # el lote: así la caché de tareas programadas no queda desactualizada.
        core.clear_tweak_detection_cache()
        for t in ap:
            if t["mode"] == "track":
                try:
                    self.statuses[t["id"]] = core.tweak_status(t)
                except Exception:
                    self.statuses[t["id"]] = "unknown"
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
    def page_net(self):
        self.heading(
            "Diagnóstico de red",
            "Compará la respuesta de servidores DNS desde tu conexión. No equivale al ping de un servidor de juego."
        )
        body = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 14))
        card = self.card(body, corner_radius=16)
        card.pack(fill="x", pady=4)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=15)
        self.btn(row, "Iniciar prueba DNS", self.dns_test, width=180).pack(side="left")
        ctk.CTkLabel(
            row, text="Mide consultas DNS reales; no cambia la configuración de Windows.",
            font=self.f_s, text_color=MUTE
        ).pack(side="left", padx=12)
        self.dns_f = ctk.CTkFrame(body, fg_color="transparent")
        self.dns_f.pack(fill="x", pady=8)
        self.dns_best = None

    def dns_test(self):
        for widget in self.dns_f.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.dns_f, text="Consultando servidores DNS...",
            font=self.f_n, text_color=MUTE
        ).pack(anchor="w", pady=10)
        def work():
            results = []
            for index, (name, address) in enumerate(core.DNS_SERVERS, 1):
                self.say(f"Probando {name}...", index / len(core.DNS_SERVERS))
                results.append((name, address, core.dns_rtt(address)))
            results.sort(key=lambda item: (item[2] is None, item[2] or 0))
            self.after(0, lambda: self.dns_show(results))
            self.say("Prueba de DNS terminada.", 0)
        threading.Thread(target=work, daemon=True).start()

    def dns_show(self, results):
        if self.page != "net":
            return
        for widget in self.dns_f.winfo_children():
            widget.destroy()
        card = self.card(self.dns_f, corner_radius=15)
        card.pack(fill="x", pady=4)
        ctk.CTkLabel(
            card, text="RESULTADOS DNS",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=ACC, anchor="w"
        ).pack(fill="x", padx=16, pady=(13, 5))
        for index, (name, address, latency) in enumerate(results):
            row = ctk.CTkFrame(card, fg_color=CARD2, corner_radius=10)
            row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                row, text=f"{name} · {address}", font=self.f_n,
                text_color=GREEN if index == 0 and latency is not None else TEXT,
                width=260, anchor="w"
            ).pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(
                row, text="sin respuesta" if latency is None else f"{latency:.1f} ms",
                font=self.f_b, text_color=TEXT, width=110, anchor="e"
            ).pack(side="right", padx=12)
        ctk.CTkLabel(
            card, text="El DNS más rápido en estas consultas no garantiza una mejora en juegos.",
            font=self.f_s, text_color=MUTE
        ).pack(anchor="w", padx=15, pady=(6, 12))

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
        core.clear_tweak_detection_cache()
        try:
            self.statuses[tid] = core.tweak_status(next(t for t in self.vis if t["id"] == tid)) if not e else "unknown"
        except Exception:
            self.statuses[tid] = "unknown"
        core.save_json(core.data_path("state.json"), self.st); self.log("Revertido", self.tname(tid), not e)
        if tid in self.vars: self.vars[tid].set(False)
        self.show("hist")

    # ---------- Acerca de / versión ----------
    def page_about(self):
        self.heading(
            "Acerca de ZyroTech Free",
            "Herramientas locales para entender y ajustar Windows con control."
        )
        body = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 16))
        hero = self.card(body, fg="#1B1B2A", corner_radius=18, border_color="#39354F")
        hero.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(
            hero, text="ZYROTECH FREE",
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            text_color=ACC, anchor="w"
        ).pack(fill="x", padx=22, pady=(20, 4))
        ctk.CTkLabel(
            hero, text="Diagnóstico y ajustes locales para Windows. Sin cuentas ni servidores externos.",
            font=self.f_n, text_color=TEXT, anchor="w"
        ).pack(fill="x", padx=22, pady=(0, 16))
        cards = ctk.CTkFrame(body, fg_color="transparent")
        cards.pack(fill="x")
        cards.grid_columnconfigure((0, 1), weight=1, uniform="about")
        items = [
            ("PRIVACIDAD", "El análisis se ejecuta localmente."),
            ("CONTROL", "Cada ajuste muestra su estado y puede revertirse cuando existe una acción inversa."),
            ("COMPATIBILIDAD", "La detección filtra ajustes según hardware y versión de Windows."),
            ("TRANSPARENCIA", "La cobertura representa ajustes comprobados, no una promesa de FPS."),
        ]
        for index, (title, description) in enumerate(items):
            tile = ctk.CTkFrame(cards, fg_color=CARD, corner_radius=14, border_width=1, border_color=LINE)
            tile.grid(row=index // 2, column=index % 2, sticky="nsew", padx=4, pady=4)
            ctk.CTkLabel(
                tile, text=title, font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                text_color=ACC, anchor="w"
            ).pack(fill="x", padx=16, pady=(14, 5))
            ctk.CTkLabel(
                tile, text=description, font=self.f_s, text_color=MUTE, anchor="w",
                wraplength=410, justify="left"
            ).pack(fill="x", padx=16, pady=(0, 15))

if __name__ == "__main__":
    if "--revert-all" in sys.argv: headless_revert(); sys.exit(0)
    if not core.IS_WIN: sys.exit("ZyroTech solo corre en Windows.")
    App().mainloop()
