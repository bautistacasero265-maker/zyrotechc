"""ZyroTech Free · diagnóstico y ajustes locales de Windows."""
import os, sys, threading, time
import customtkinter as ctk
from tkinter import messagebox, filedialog
import core


# ---------- Identidad visual ZyroTech / nueva interfaz ----------
BG, SIDE, CARD, CARD2, LINE = "#0A0811", "#100D19", "#181322", "#211A2D", "#352A47"
TEXT, MUTE, RED, GOLD, GREEN = "#F8F5FF", "#BDB4CC", "#FF647C", "#FFC66D", "#65E6B7"
CYAN, BLUE, PURPLE = "#69DCEB", "#9AA2FF", "#B99AFF"
ACC = "#9B72FF"
ACC_TXT = "#130D20"
HOVER = "#3A2D50"
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
        self.geometry("1280x760")
        self.minsize(980, 660)
        try:
            self.state("zoomed")
        except Exception:
            pass
        self.configure(fg_color=BG)

        self.f_logo = ctk.CTkFont(family="Segoe UI", size=20, weight="bold")
        self.f_h1 = ctk.CTkFont(family="Segoe UI", size=31, weight="bold")
        self.f_h2 = ctk.CTkFont(family="Segoe UI", size=19, weight="bold")
        self.f_b = ctk.CTkFont(family="Segoe UI", size=14, weight="bold")
        self.f_n = ctk.CTkFont(family="Segoe UI", size=14)
        self.f_s = ctk.CTkFont(family="Segoe UI", size=12)
        self.f_big = ctk.CTkFont(family="Segoe UI", size=43, weight="bold")
        self.f_mono = ctk.CTkFont(family="Cascadia Code", size=12)

        self.st = core.load_json(core.data_path("state.json"), {"applied": {}})
        self.hist = core.load_json(core.data_path("history.json"), [])
        self.settings = core.load_json(core.data_path("settings.json"), {"games": [], "last_latency": None})
        self.tweaks, self.vis, self.vars, self.hw, self.statuses = [], [], {}, None, {}
        self.restore_ok, self.cat, self.page = False, None, None
        self.search_query, self.risk_ack = "", False
        self.pending_lbl = self.banner = None

        # Layout principal: cabecera + navegación horizontal + espacio de trabajo + estado.
        self.grid_columnconfigure(0, weight=0, minsize=228)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.topbar = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0, height=72)
        self.topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.topbar.grid_propagate(False)

        brand = ctk.CTkFrame(self.topbar, fg_color="transparent")
        brand.pack(side="left", padx=25, pady=12)
        mark = ctk.CTkFrame(brand, fg_color=ACC, corner_radius=13, width=43, height=43)
        mark.pack(side="left")
        mark.pack_propagate(False)
        ctk.CTkLabel(mark, text="ZT", font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
                     text_color=ACC_TXT).pack(expand=True)
        namebox = ctk.CTkFrame(brand, fg_color="transparent")
        namebox.pack(side="left", padx=12)
        ctk.CTkLabel(namebox, text="ZYROTECH", font=self.f_logo, text_color=TEXT).pack(anchor="w")
        ctk.CTkLabel(namebox, text="PERFORMANCE LAB", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=MUTE).pack(anchor="w", pady=(0, 1))

        top_right = ctk.CTkFrame(self.topbar, fg_color="transparent")
        top_right.pack(side="right", padx=24)
        ctk.CTkLabel(top_right, text="●  ANÁLISIS LOCAL",
                     font=self.f_s, text_color=GREEN).pack(side="left", padx=(0, 16))
        self.edition_tag = ctk.CTkLabel(top_right, text="FREE",
                     fg_color=CARD2, text_color=ACC, corner_radius=8, font=self.f_s, padx=13, pady=7)
        self.edition_tag.pack(side="left")
        self.btn(top_right, "↻  ESCANEAR", self.refresh_scan, "ghost", height=34, width=125).pack(side="left", padx=(13, 0))

        self.navbar = ctk.CTkFrame(self, fg_color=SIDE, corner_radius=0,
                                   border_width=0, width=228)
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
        self._compact = False
        self.bind("<Configure>", self._on_window_resize)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.splash("Analizando componentes y ajustes...")
        threading.Thread(target=self.boot, daemon=True).start()


    # ---------- utilidades ----------
    def _on_window_resize(self, event):
        if event.widget is not self:
            return
        compact = event.width < 1180
        if compact != self._compact:
            self._compact = compact
            current = self.page
            if current and hasattr(self, "nav"):
                self.after_idle(lambda page=current: self.show(page) if self.page == page else None)

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
        ctk.CTkLabel(wrap, text="OPTIMIZER SUITE", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=ACC).pack(pady=(1, 18))
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
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color=ACC, anchor="w").pack(side="left")
        ctk.CTkLabel(eyebrow, text="●  LOCAL MODE", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=GREEN, anchor="e").pack(side="right")
        ctk.CTkLabel(top, text=text, font=self.f_h1, text_color=TEXT, anchor="w").pack(fill="x", pady=(7, 2))
        if sub:
            ctk.CTkLabel(top, text=sub, font=self.f_n, text_color="#C3B9D1", anchor="w",
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
            ("home", "⌂", "Inicio"),
            ("opt", "◈", "Ajustes"),
            ("net", "⌁", "Red"),
            ("hist", "◷", "Actividad"),
            ("about", "ⓘ", "Acerca de"),
        ]
        self.nav_rails = {}
        ctk.CTkLabel(self.navbar, text="MENÚ PRINCIPAL", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color="#A99DB8", anchor="w").pack(fill="x", padx=19, pady=(25, 12))
        for key, glyph, label in nav_items:
            tile = ctk.CTkFrame(self.navbar, fg_color="transparent", corner_radius=11)
            tile.pack(fill="x", padx=10, pady=3)
            rail = ctk.CTkFrame(tile, fg_color="transparent", width=3, corner_radius=2)
            rail.pack(side="left", fill="y", padx=(0, 5), pady=8)
            button = ctk.CTkButton(
                tile, text=f"{glyph}     {label}", anchor="w",
                fg_color="transparent", text_color=MUTE, hover_color="#2C2340",
                corner_radius=9, height=44, font=self.f_n,
                command=lambda selected=key: self.show(selected)
            )
            button.pack(side="left", fill="x", expand=True)
            self.nav[key] = button
            self.nav_rails[key] = (tile, rail)
        ctk.CTkFrame(self.navbar, fg_color=LINE, height=1).pack(fill="x", padx=18, pady=(22, 14))
        edition = ctk.CTkFrame(self.navbar, fg_color="#181322", corner_radius=13,
                               border_width=1, border_color="#3A2D50")
        edition.pack(side="bottom", fill="x", padx=12, pady=15)
        ctk.CTkLabel(edition, text="ZYROTECH  /  FREE", font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color=ACC, anchor="w").pack(fill="x", padx=12, pady=(12, 4))
        ctk.CTkLabel(edition, text="Optimización local para Windows.\nControlá cada cambio. Revertí cuando quieras.",
                     font=self.f_s, text_color="#C3B9D1", anchor="w", justify="left",
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
            b.configure(fg_color="#2C2340" if active else "transparent",
                        text_color=TEXT if active else MUTE,
                        font=self.f_b if active else self.f_n)
            if k in getattr(self, "nav_rails", {}):
                tile, rail = self.nav_rails[k]
                tile.configure(fg_color="#21182F" if active else "transparent")
                rail.configure(fg_color=ACC if active else "transparent")
        getattr(self, "page_" + key)()


    # ---------- Panel ----------
    def coverage(self):
        applied = {tid for tid, state in self.statuses.items() if state == "active"}
        applicable = [t for t in self.vis if core.applicable(t, self.hw)]
        return core.coverage(applicable, applied, include_locked=False)

    def page_home(self):
        eligible = [t for t in self.vis if t.get("mode") == "track" and not t.get("locked") and core.applicable(t, self.hw)]
        active = sum(1 for t in eligible if self.statuses.get(t["id"]) == "active")
        partial = sum(1 for t in eligible if self.statuses.get(t["id"]) == "partial")
        pending = sum(1 for t in eligible if self.statuses.get(t["id"]) == "inactive")
        unknown = sum(1 for t in eligible if self.statuses.get(t["id"]) == "unknown")
        incompatible = sum(1 for t in self.vis if self.statuses.get(t["id"]) == "incompatible")
        coverage = self.coverage()
        hw = self.hw or {}

        body = ctk.CTkScrollableFrame(self.content, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True, padx=24, pady=(18, 22))

        # Hero de bienvenida con identidad violeta/magenta y acciones claras.
        hero = ctk.CTkFrame(body, fg_color="#21182F", corner_radius=22,
                            border_width=1, border_color="#554078")
        hero.pack(fill="x", pady=(0, 17))
        compact = getattr(self, "_compact", False)
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_columnconfigure(1, weight=0, minsize=238 if not compact else 0)
        hero_left = ctk.CTkFrame(hero, fg_color="transparent")
        hero_left.grid(row=0, column=0, sticky="nsew", padx=(25, 15), pady=24)
        ctk.CTkLabel(hero_left, text="ZYROTECH  /  TU CENTRO DE CONTROL",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#CEB9FF", anchor="w").pack(fill="x")
        ctk.CTkLabel(hero_left, text="Hacé que Windows\ntrabaje a tu manera.",
                     font=ctk.CTkFont(family="Segoe UI", size=31, weight="bold"),
                     text_color=TEXT, anchor="w", justify="left").pack(fill="x", pady=(9, 8))
        ctk.CTkLabel(hero_left,
                     text="Explorá ajustes, revisá qué está activo en tu PC y elegí cada cambio con información clara. Todo desde un solo lugar.",
                     font=ctk.CTkFont(family="Segoe UI", size=13),
                     text_color="#D1C6DC", anchor="w", wraplength=680,
                     justify="left").pack(fill="x")
        ctk.CTkLabel(hero_left, text="91 AJUSTES DISPONIBLES   •   2 PROTEGIDOS   •   DETECCIÓN LOCAL",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#80F0D0", anchor="w").pack(fill="x", pady=(13, 0))
        hero_actions = ctk.CTkFrame(hero_left, fg_color="transparent")
        hero_actions.pack(fill="x", pady=(17, 0))
        self.btn(hero_actions, "Explorar ajustes  →", lambda: self.show("opt"), "acc",
                 width=184, height=42).pack(side="left")
        self.btn(hero_actions, "Volver a analizar", self.refresh_scan, "ghost",
                 width=158, height=42).pack(side="left", padx=10)

        score = ctk.CTkFrame(hero, fg_color="#2C2340", corner_radius=17,
                             border_width=1, border_color="#594477", width=220)
        score.grid(row=0 if not compact else 1, column=1 if not compact else 0,
                    sticky="nsew" if not compact else "ew",
                    padx=(5, 19) if not compact else (18, 18), pady=18 if not compact else (0, 16))
        score.configure(width=220 if not compact else 0)
        score.grid_propagate(not not compact)
        ctk.CTkLabel(score, text="ESTADO DE TU EQUIPO",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#D9C5E9").pack(anchor="w", padx=17, pady=(17, 5))
        ctk.CTkLabel(score, text=f"{coverage}%",
                     font=ctk.CTkFont(family="Segoe UI", size=48, weight="bold"),
                     text_color="#C6AFFF").pack(anchor="w", padx=15)
        ctk.CTkLabel(score, text="de los ajustes compatibles\nfiguran activos y verificados",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color="#E0D5E9", justify="left").pack(anchor="w", padx=17, pady=(0, 12))
        gauge = ctk.CTkProgressBar(score, height=8, progress_color="#9B72FF",
                                   fg_color="#403050", corner_radius=8)
        gauge.set(coverage / 100)
        gauge.pack(fill="x", padx=17, pady=(0, 16))

        section = ctk.CTkFrame(body, fg_color="transparent")
        section.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(section, text="RESUMEN DE OPTIMIZACIÓN",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#D7C9E4", anchor="w").pack(fill="x", pady=(0, 9))
        metrics = ctk.CTkFrame(section, fg_color="transparent")
        metrics.pack(fill="x")
        metric_columns = 2 if compact else 4
        for i in range(metric_columns):
            metrics.grid_columnconfigure(i, weight=1, uniform="metric")
        def metric(i, title, value, detail, accent):
            c = ctk.CTkFrame(metrics, fg_color="#191525", corner_radius=16,
                             border_width=1, border_color="#3A2D4D")
            c.grid(row=i // metric_columns, column=i % metric_columns, sticky="nsew",
                   padx=(0 if i % metric_columns == 0 else 6, 0 if i % metric_columns == metric_columns - 1 else 6),
                   pady=(0, 8) if compact else 0)
            ctk.CTkFrame(c, fg_color=accent, height=4, corner_radius=2).pack(fill="x", padx=14, pady=(13, 11))
            ctk.CTkLabel(c, text=title.upper(),
                         font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                         text_color="#BEB2CB", anchor="w").pack(fill="x", padx=15, pady=(0, 2))
            ctk.CTkLabel(c, text=str(value),
                         font=ctk.CTkFont(family="Segoe UI", size=35, weight="bold"),
                         text_color=accent, anchor="w").pack(fill="x", padx=15)
            ctk.CTkLabel(c, text=detail,
                         font=ctk.CTkFont(family="Segoe UI", size=11),
                         text_color="#B7AFC6", anchor="w", wraplength=220,
                         justify="left").pack(fill="x", padx=15, pady=(2, 14))
        metric(0, "Activos", active, "Detectados directamente en Windows", "#80F0D0")
        metric(1, "Por revisar", pending, "Compatibles que todavía no están activos", "#C6AFFF")
        metric(2, "Parciales / sin lectura", partial + unknown,
               f"{partial} parciales  •  {unknown} sin lectura", "#FFD166")
        metric(3, "No compatibles", incompatible, "Se excluyen de las recomendaciones", "#A99CB8")

        ctk.CTkLabel(body, text="TU EQUIPO",
                     font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                     text_color="#D7C9E4", anchor="w").pack(fill="x", pady=(8, 9))
        lower = ctk.CTkFrame(body, fg_color="transparent")
        lower.pack(fill="x")
        lower.grid_columnconfigure(0, weight=1 if compact else 3, uniform="lower")
        if not compact:
            lower.grid_columnconfigure(1, weight=2, uniform="lower")

        device = ctk.CTkFrame(lower, fg_color="#191525", corner_radius=17,
                              border_width=1, border_color="#3A2D4D")
        device.grid(row=0, column=0, sticky="nsew", padx=(0, 0 if compact else 7), pady=(0, 10) if compact else 0)
        ctk.CTkLabel(device, text="INFORMACIÓN DEL HARDWARE",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#C6AFFF", anchor="w").pack(fill="x", padx=18, pady=(16, 10))
        specs = [
            ("PROCESADOR", hw.get("cpu_name", "No detectado")),
            ("GRÁFICOS", hw.get("gpu_name", "No detectada")),
            ("MEMORIA", f'{hw.get("ram", 0)} GB RAM'),
            ("ALMACENAMIENTO", "SSD / NVMe" if hw.get("ssd") else "HDD / no identificado como SSD"),
            ("WINDOWS", hw.get("os", "Windows")),
            ("FORMATO", "Notebook" if hw.get("laptop") else "Escritorio"),
        ]
        spec_grid = ctk.CTkFrame(device, fg_color="transparent")
        spec_grid.pack(fill="both", expand=True, padx=13, pady=(0, 14))
        spec_grid.grid_columnconfigure((0, 1), weight=1, uniform="spec")
        for idx, (label, value) in enumerate(specs):
            rr, cc = divmod(idx, 2)
            cell = ctk.CTkFrame(spec_grid, fg_color="#292137", corner_radius=11)
            cell.grid(row=rr, column=cc, sticky="nsew", padx=4, pady=4)
            ctk.CTkLabel(cell, text=label,
                         font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                         text_color="#BEB2CB", anchor="w").pack(fill="x", padx=11, pady=(9, 2))
            ctk.CTkLabel(cell, text=value,
                         font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                         text_color="#F7F1FF", anchor="w",
                         wraplength=290, justify="left").pack(fill="x", padx=11, pady=(0, 10))

        overview = ctk.CTkFrame(lower, fg_color="#191525", corner_radius=17,
                                border_width=1, border_color="#3A2D4D")
        overview.grid(row=1 if compact else 0, column=0 if compact else 1, sticky="nsew",
                       padx=(0, 0 if compact else 7), pady=(0, 0) if not compact else (2, 0))
        ctk.CTkLabel(overview, text="ESTADO Y HERRAMIENTAS",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#C6AFFF", anchor="w").pack(fill="x", padx=18, pady=(16, 7))
        ctk.CTkLabel(overview, text=f"{active} / {max(1, len(eligible))}",
                     font=ctk.CTkFont(family="Segoe UI", size=34, weight="bold"),
                     text_color=TEXT, anchor="w").pack(fill="x", padx=18)
        ctk.CTkLabel(overview, text="ajustes compatibles activos",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color="#B7AFC6", anchor="w").pack(fill="x", padx=18, pady=(0, 10))
        pb = ctk.CTkProgressBar(overview, height=9, progress_color="#9B72FF",
                                fg_color="#362A46", corner_radius=6)
        pb.set(coverage / 100)
        pb.pack(fill="x", padx=18, pady=(0, 14))
        ctk.CTkFrame(overview, fg_color="#3A2D4D", height=1).pack(fill="x", padx=18, pady=(0, 12))
        ctk.CTkLabel(overview, text="MEDICIÓN DE TEMPORIZACIÓN",
                     font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
                     text_color="#BEB2CB", anchor="w").pack(fill="x", padx=18)
        self.lat_lbl = ctk.CTkLabel(overview, text=self.lat_text(),
                                    font=ctk.CTkFont(family="Segoe UI", size=12),
                                    text_color=TEXT, anchor="w", justify="left")
        self.lat_lbl.pack(fill="x", padx=18, pady=(5, 10))
        self.btn(overview, "Medir ahora", self.measure, "ghost", width=135, height=35).pack(anchor="w", padx=18)
        ctk.CTkLabel(overview,
                     text="Esta medición no equivale a FPS ni garantiza menor latencia en juegos.",
                     font=ctk.CTkFont(family="Segoe UI", size=11), text_color="#A99CB8",
                     wraplength=320, justify="left").pack(fill="x", padx=18, pady=(10, 15))

        actions = ctk.CTkFrame(body, fg_color="#21182F", corner_radius=17,
                               border_width=1, border_color="#49365F")
        actions.pack(fill="x", pady=(15, 0))
        ctk.CTkLabel(actions, text="¿QUÉ QUERÉS HACER AHORA?",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#C6AFFF", anchor="w").pack(fill="x", padx=18, pady=(15, 5))
        ctk.CTkLabel(actions,
                     text="Revisá los cambios antes de aplicarlos. Los que ya están activos o no corresponden a tu PC se omiten.",
                     font=ctk.CTkFont(family="Segoe UI", size=12), text_color="#D1C6DC",
                     anchor="w", wraplength=900, justify="left").pack(fill="x", padx=18, pady=(0, 12))
        row = ctk.CTkFrame(actions, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=(0, 16))
        dashboard_actions = [
            ("Ver ajustes recomendados", self.recommended, "acc", 210),
            ("Crear punto de restauración", self.make_restore, "ghost", 225),
            ("Revertir todos los cambios", self.revert_all, "ghost", 205),
            ("Exportar informe", self.export_report, "ghost", 155),
        ]
        if compact:
            for col in range(2):
                row.grid_columnconfigure(col, weight=1)
            for index, (label, command, kind, width) in enumerate(dashboard_actions):
                self.btn(row, label, command, kind, height=40).grid(
                    row=index // 2, column=index % 2, sticky="ew", padx=4, pady=4)
        else:
            for label, command, kind, width in dashboard_actions:
                self.btn(row, label, command, kind, width=width, height=40).pack(
                    side="left", padx=(0, 9) if label != "Ver ajustes recomendados" else (0, 0))

        # Consejos útiles y una presentación honesta de la futura edición Pro.
        tips = [
            ("Empezá por lo reversible", "Probá un ajuste por vez y comprobá si cambia algo en tu uso diario antes de continuar."),
            ("No confundas cobertura con rendimiento", "El porcentaje indica ajustes detectados como activos; no mide FPS, fluidez ni latencia."),
            ("Reiniciá cuando el ajuste lo indique", "Algunos cambios de Windows no se reflejan por completo hasta reiniciar el equipo."),
            ("Conservá lo que necesitás", "No desactives búsqueda, servicios o funciones de Windows si realmente las usás."),
            ("Compará antes y después", "Usá el mismo juego, mapa y límite de FPS para comparar resultados en condiciones parecidas."),
        ]
        tip_title, tip_body = tips[time.localtime().tm_yday % len(tips)]
        tip_card = ctk.CTkFrame(body, fg_color="#171220", corner_radius=17,
                                border_width=1, border_color="#49365F")
        tip_card.pack(fill="x", pady=(14, 0))
        ctk.CTkLabel(tip_card, text="TIPS PARA EMPEZAR  /  CONSEJO DEL DÍA",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#C6AFFF", anchor="w").pack(fill="x", padx=18, pady=(14, 5))
        ctk.CTkLabel(tip_card, text=tip_title,
                     font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                     text_color=TEXT, anchor="w").pack(fill="x", padx=18, pady=(0, 3))
        ctk.CTkLabel(tip_card, text=tip_body,
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color="#C8BED2", anchor="w", wraplength=920,
                     justify="left").pack(fill="x", padx=18, pady=(0, 14))

        pro_card = ctk.CTkFrame(body, fg_color="#21182F", corner_radius=17,
                                border_width=1, border_color="#554078")
        pro_card.pack(fill="x", pady=(12, 0))
        pro_row = ctk.CTkFrame(pro_card, fg_color="transparent")
        pro_row.pack(fill="x", padx=18, pady=15)
        pro_copy = ctk.CTkFrame(pro_row, fg_color="transparent")
        pro_copy.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(pro_copy, text="ZYROTECH PRO  /  EN DESARROLLO",
                     font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     text_color="#C6AFFF", anchor="w").pack(fill="x")
        ctk.CTkLabel(pro_copy,
                     text="Más herramientas. Más control. Una suite avanzada.",
                     font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                     text_color=TEXT, anchor="w").pack(fill="x", pady=(4, 2))
        ctk.CTkLabel(pro_copy,
                     text="La edición gratuita seguirá siendo útil por sí sola. Pro sumará funciones avanzadas cuando esté lista.",
                     font=ctk.CTkFont(family="Segoe UI", size=12),
                     text_color="#C8BED2", anchor="w", wraplength=680,
                     justify="left").pack(fill="x")
        ctk.CTkLabel(pro_row, text="PRÓXIMAMENTE",
                     fg_color="#3A2344", text_color="#D2BCFF",
                     corner_radius=9, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                     padx=13, pady=9).pack(side="right", padx=(12, 0))

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
                report.write("\n".join(lines))
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
        # Recomendaciones prudentes: evita acciones puntuales, preferencias personales,
        # servicios críticos, cambios de energía/red y cualquier elemento con precaución.
        safe_modules = {"Privacidad", "Debloat", "Gaming", "Tareas", "Seguridad básica"}
        selected = 0
        for tweak in self.vis:
            actions_reversible = all(
                action.get("type") in ("reg", "scheduled_task") or bool(action.get("undo"))
                for action in tweak.get("actions", [])
            )
            suitable = (
                tweak.get("risk") == "normal"
                and tweak["mode"] == "track"
                and tweak.get("badge") not in BAD_FOR_AUTO
                and tweak.get("module") in safe_modules
                and actions_reversible
                and core.applicable(tweak, self.hw)
                and self.statuses.get(tweak["id"]) == "inactive"
            )
            if suitable:
                if not self.vars[tweak["id"]].get():
                    self.vars[tweak["id"]].set(True)
                selected += 1
        self.cat = "Gaming" if "Gaming" in self.cats() else ORDER[0]
        self.search_query = ""
        self.show("opt")
        self.say(
            f"{selected} sugerencias prudentes seleccionadas. No se aplicó ningún cambio.",
            0
        )

    def cats(self): return [m for m in ORDER if any(t["module"] == m and core.applicable(t, self.hw) for t in self.vis)]
    def page_opt(self):
        self.heading(
            "Biblioteca de ajustes",
            "93 ajustes Free con explicación, compatibilidad y estado detectado. Las recomendaciones evitan cambios delicados y preferencias personales."
        )
        compact = getattr(self, "_compact", False)
        cats = self.cats()
        self.cat = self.cat if self.cat in cats else (cats[0] if cats else None)

        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18 if compact else 28)
        left_width = 176 if compact else 218
        left = ctk.CTkScrollableFrame(
            body, width=left_width, fg_color=SIDE, corner_radius=16,
            border_width=1, border_color=LINE
        )
        left.pack(side="left", fill="y", padx=(0, 10 if compact else 14))
        left.pack_propagate(False)
        self.cat_buttons = {}
        ctk.CTkLabel(
            left, text="CATEGORÍAS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#A99DB8", anchor="w"
        ).pack(fill="x", padx=12, pady=(13, 8))

        icons = {
            "Privacidad": "◈", "Debloat": "✦", "Gaming": "▣", "Kernel": "⌘",
            "Energía": "ϟ", "Red": "⌁", "Periféricos": "⌖", "Interfaz": "▤",
            "Servicios": "⚙", "Tareas": "◷", "Inicio": "➜",
            "Mantenimiento": "⌁", "Seguridad básica": "◇", "Seguridad": "⬡"
        }
        for module in cats:
            count = sum(
                1 for item in self.vis
                if item["module"] == module and core.applicable(item, self.hw)
            )
            selected = module == self.cat
            tile = ctk.CTkFrame(
                left, fg_color="#2C2340" if selected else "transparent",
                corner_radius=11
            )
            tile.pack(fill="x", pady=3)
            rail = ctk.CTkFrame(
                tile, fg_color=ACC if selected else "transparent",
                width=3, corner_radius=2
            )
            rail.pack(side="left", fill="y", padx=(0, 4), pady=7)
            label = "Seg. básica" if compact and module == "Seguridad básica" else module
            button = ctk.CTkButton(
                tile, text=f'{icons.get(module, "•")}  {label}', anchor="w",
                fg_color="transparent", text_color=TEXT if selected else MUTE,
                hover_color=CARD2, corner_radius=9,
                height=39 if compact else 42,
                font=self.f_b if selected else self.f_n,
                command=lambda selected_module=module: self.set_cat(selected_module)
            )
            button.pack(side="left", fill="x", expand=True)
            self.cat_buttons[module] = (tile, rail, button)
            ctk.CTkLabel(
                tile, text=str(count),
                fg_color="#3A2D50" if selected else CARD2,
                text_color=ACC if selected else MUTE,
                corner_radius=7, font=self.f_s, width=26, height=21
            ).pack(side="right", padx=5)

        right = ctk.CTkFrame(body, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True)
        top = ctk.CTkFrame(right, fg_color="transparent")
        top.pack(fill="x", pady=(0, 10))

        if compact:
            title_row = ctk.CTkFrame(top, fg_color="transparent")
            title_row.pack(fill="x")
            self.category_title = ctk.CTkLabel(
                title_row, text=self.cat or "Ajustes", font=self.f_h2,
                text_color=TEXT, anchor="w"
            )
            self.category_title.pack(side="left", padx=(2, 10))
            self.result_count = ctk.CTkLabel(
                title_row, text="", font=self.f_s, text_color=MUTE
            )
            self.result_count.pack(side="right")
            tools_row = ctk.CTkFrame(top, fg_color="transparent")
            tools_row.pack(fill="x", pady=(8, 0))
            self.search = ctk.CTkEntry(
                tools_row, placeholder_text="Buscar ajustes...",
                fg_color=CARD, border_color=LINE, height=41,
                corner_radius=12, border_width=1
            )
            self.search.pack(side="left", fill="x", expand=True, padx=(0, 8))
            self.btn(
                tools_row, "Recomendarme", self.recommended, "ghost",
                width=132, height=39
            ).pack(side="right")
        else:
            self.category_title = ctk.CTkLabel(
                top, text=self.cat or "Ajustes", font=self.f_h2,
                text_color=TEXT, anchor="w"
            )
            self.category_title.pack(side="left", padx=(2, 12))
            self.result_count = ctk.CTkLabel(
                top, text="", font=self.f_s, text_color=MUTE
            )
            self.result_count.pack(side="left")
            self.search = ctk.CTkEntry(
                top, placeholder_text="Buscar ajustes...",
                fg_color=CARD, border_color=LINE, height=43,
                corner_radius=12, border_width=1
            )
            self.search.pack(side="right", fill="x", expand=True, padx=(14, 0))
            self.btn(
                top, "✦  Recomendarme", self.recommended, "ghost",
                width=170, height=40
            ).pack(side="left", padx=(8, 0))

        if self.search_query:
            self.search.insert(0, self.search_query)
        self.search.bind("<KeyRelease>", lambda event: self.fill_list())

        self.listf = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.listf.pack(fill="both", expand=True)

        self.banner = ctk.CTkLabel(
            self.content, text="", fg_color=RED, text_color="white",
            font=self.f_s, wraplength=900, justify="left", corner_radius=8
        )
        bar = self.card(self.content, fg=SIDE, corner_radius=14)
        bar.pack(fill="x", padx=18 if compact else 28, pady=(8, 10))

        self.risk_ok = ctk.BooleanVar(value=self.risk_ack)
        if compact:
            summary_row = ctk.CTkFrame(bar, fg_color="transparent")
            summary_row.pack(fill="x", padx=12, pady=(8, 0))
            self.pending_lbl = ctk.CTkLabel(
                summary_row, text="", font=self.f_b, text_color=TEXT
            )
            self.pending_lbl.pack(side="left")
            ctk.CTkCheckBox(
                summary_row, text="Entiendo los riesgos", variable=self.risk_ok,
                font=self.f_s, fg_color=ACC, hover_color=ACC, text_color=MUTE
            ).pack(side="right")
            action_row = ctk.CTkFrame(bar, fg_color="transparent")
            action_row.pack(fill="x", padx=10, pady=(6, 10))
            self.btn(
                action_row, "Aplicar uno", self.on_apply, width=145, height=38
            ).pack(side="right", padx=(6, 0))
            self.btn(
                action_row, "Ver pendientes", self.show_pending, "ghost",
                width=140, height=38
            ).pack(side="right")
        else:
            self.pending_lbl = ctk.CTkLabel(
                bar, text="", font=self.f_b, text_color=TEXT
            )
            self.pending_lbl.pack(side="left", padx=18, pady=12)
            ctk.CTkCheckBox(
                bar, text="Entiendo los riesgos", variable=self.risk_ok,
                font=self.f_s, fg_color=ACC, hover_color=ACC, text_color=MUTE
            ).pack(side="left", padx=10)
            self.btn(
                bar, "Aplicar uno", self.on_apply, width=145, height=40
            ).pack(side="right", padx=14)
            self.btn(
                bar, "Ver pendientes", self.show_pending, "ghost", width=140
            ).pack(side="right")

        self.fill_list()
        self.update_pending()

    def set_cat(self, m):
        # Actualiza solo el panel de resultados; no reconstruye la ventana ni los controles.
        self.cat = m
        for name, (tile, rail, button) in getattr(self, "cat_buttons", {}).items():
            active = name == m
            tile.configure(fg_color="#2C2340" if active else "transparent")
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
            rows = [
                t for t in self.vis
                if q in t["name"].lower()
                or q in t["module"].lower()
                or q in t.get("summary", "").lower()
                or q in t.get("warn", "").lower()
            ]
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
        card = self.card(self.listf, fg="#181322", corner_radius=15, border_color="#403050")
        card.pack(fill="x", pady=6, padx=2)
        card.grid_columnconfigure(2, weight=1)

        accent = GREEN if status == "active" else GOLD if status == "partial" else RED if tweak.get("risk") == "extreme" else ACC
        ctk.CTkFrame(card, fg_color=accent, width=4, corner_radius=3).grid(
            row=0, column=0, rowspan=4, sticky="ns", padx=(0, 12), pady=10)

        managed = tweak["id"] in self.st["applied"]
        disabled = (
            not compatible
            or (bool(tweak.get("locked")) and not managed)
            or (tweak["mode"] == "track" and status == "unknown")
            or (status == "active" and not managed)
        )
        switch = ctk.CTkSwitch(
            card, text="", variable=self.vars[tweak["id"]], onvalue=True, offvalue=False,
            command=self.update_pending, progress_color=ACC, width=42,
            state="disabled" if disabled else "normal"
        )
        switch.grid(row=0, column=1, rowspan=4, sticky="w", padx=(12, 9), pady=12)

        wrap = max(260, min(620, self.content.winfo_width() - (420 if self._compact else 430)))
        titlebox = ctk.CTkFrame(card, fg_color="transparent")
        titlebox.grid(row=0, column=2, sticky="ew", padx=(4, 13), pady=(11, 2))
        title_color = RED if tweak["risk"] == "extreme" else TEXT
        ctk.CTkLabel(
            titlebox, text=tweak["name"],
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=title_color, anchor="w", wraplength=wrap, justify="left"
        ).pack(fill="x", anchor="w")

        ctk.CTkLabel(
            card, text=tweak.get("summary", "Ajuste local de Windows."),
            font=self.f_s, text_color="#D0C7DD", anchor="w",
            wraplength=wrap, justify="left"
        ).grid(row=1, column=2, sticky="ew", padx=(4, 13), pady=(2, 5))

        if tweak.get("warn"):
            warning_color = RED if tweak.get("risk") == "extreme" else GOLD
            ctk.CTkLabel(
                card, text="⚠  " + tweak["warn"],
                font=self.f_s, text_color=warning_color, anchor="w",
                wraplength=wrap, justify="left"
            ).grid(row=2, column=2, sticky="ew", padx=(4, 13), pady=(0, 5))

        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.grid(row=3, column=2, sticky="ew", padx=(4, 12), pady=(2, 10))
        status_label = (
            "No compatible" if not compatible else
            "Protegido por seguridad" if tweak.get("locked") and not managed else
            "Acción puntual" if status == "once" else
            "Activo y gestionado" if status == "active" and managed else
            "Activo detectado" if status == "active" else
            "Parcialmente activo" if status == "partial" else
            "Estado no disponible" if status == "unknown" else "Disponible"
        )
        status_color = MUTE if not compatible or status == "unknown" else GREEN if status == "active" else GOLD if status == "partial" else CYAN
        status_bg = "#193A31" if status == "active" else "#3C3422" if status == "partial" else "#352A47" if status == "inactive" else "#2A2638"
        ctk.CTkLabel(
            meta, text=f"  {status_label}  ", fg_color=status_bg,
            corner_radius=8, font=self.f_s, text_color=status_color, height=25
        ).pack(side="left", padx=(0, 6))

        if tweak.get("risk") in ("caution", "extreme"):
            risk_text = "Precaución" if tweak["risk"] == "caution" else "Riesgo alto"
            risk_color = GOLD if tweak["risk"] == "caution" else RED
            ctk.CTkLabel(
                meta, text=f"  {risk_text}  ",
                fg_color="#382E20" if tweak["risk"] == "caution" else "#48232B",
                text_color=risk_color, corner_radius=7, font=self.f_s, height=23
            ).pack(side="left", padx=3)

        tags = ([tweak["badge"]] if tweak.get("badge") else [])
        if tweak.get("reboot"):
            tags.append("Reinicio")
        if tweak["mode"] == "once":
            tags.append("Una vez")
        for tag in tags:
            self.badge(meta, tag).pack(side="left", padx=3)

        ctk.CTkButton(
            meta, text="ⓘ", width=34, height=29, corner_radius=9,
            fg_color="#30263D", text_color="#E5D9F5", hover_color=HOVER,
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            command=lambda item=tweak: self.info(item)
        ).pack(side="right", padx=(8, 0))

    def info(self, tweak):
        window = ctk.CTkToplevel(self)
        window.wm_title(tweak["name"])
        window.geometry("740x600")
        window.minsize(600, 480)
        window.configure(fg_color=BG)
        window.after(120, window.lift)

        body = ctk.CTkScrollableFrame(window, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=18, pady=16)

        ctk.CTkLabel(
            body, text=f'ZYROTECH  /  {tweak["module"].upper()}',
            font=self.f_s, text_color=ACC, anchor="w"
        ).pack(fill="x", padx=4, pady=(0, 7))
        ctk.CTkLabel(
            body, text=tweak["name"],
            font=ctk.CTkFont(family="Segoe UI", size=21, weight="bold"),
            text_color=TEXT, anchor="w", wraplength=650, justify="left"
        ).pack(fill="x", padx=4, pady=(0, 10))

        summary = self.card(body, fg="#21182F", border_color="#554078", corner_radius=16)
        summary.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            summary, text="QUÉ HACE",
            font=self.f_s, text_color="#C6AFFF", anchor="w"
        ).pack(fill="x", padx=15, pady=(14, 5))
        ctk.CTkLabel(
            summary, text=tweak.get("summary", "Ajuste local de Windows."),
            font=self.f_n, text_color=TEXT, anchor="w",
            wraplength=640, justify="left"
        ).pack(fill="x", padx=15, pady=(0, 14))

        if tweak.get("warn"):
            warning = self.card(
                body, fg="#382E20" if tweak.get("risk") != "extreme" else "#48232B",
                border_color="#6B5430" if tweak.get("risk") != "extreme" else "#75404B",
                corner_radius=14
            )
            warning.pack(fill="x", pady=(0, 10))
            ctk.CTkLabel(
                warning, text="ANTES DE APLICAR",
                font=self.f_s,
                text_color=GOLD if tweak.get("risk") != "extreme" else RED,
                anchor="w"
            ).pack(fill="x", padx=14, pady=(12, 4))
            ctk.CTkLabel(
                warning, text=tweak["warn"], font=self.f_n, text_color=TEXT,
                anchor="w", wraplength=640, justify="left"
            ).pack(fill="x", padx=14, pady=(0, 12))

        risk_text = {
            "normal": "Riesgo normal · ajuste reversible o de impacto acotado.",
            "caution": "Precaución · puede cambiar funciones o preferencias.",
            "extreme": "Riesgo alto · puede ser difícil recuperar la función eliminada."
        }.get(tweak.get("risk"), "Revisá el efecto antes de aplicar.")
        ctk.CTkLabel(
            body, text=risk_text, font=self.f_s,
            text_color=RED if tweak.get("risk") == "extreme" else GOLD if tweak.get("risk") == "caution" else GREEN,
            anchor="w", wraplength=650, justify="left"
        ).pack(fill="x", padx=4, pady=(0, 10))

        ctk.CTkLabel(
            body, text="DETALLE TÉCNICO",
            font=self.f_s, text_color=MUTE, anchor="w"
        ).pack(fill="x", padx=4, pady=(4, 5))
        textbox = ctk.CTkTextbox(
            body, fg_color=CARD, font=ctk.CTkFont(family="Cascadia Code", size=11),
            height=150, wrap="word"
        )
        textbox.pack(fill="x", expand=False, padx=2, pady=(0, 10))
        for action in tweak["actions"]:
            if action["type"] == "reg":
                textbox.insert("end", f'{action["path"]}\\{action["name"]} = {action["value"]} ({action.get("vtype", "REG_DWORD")})\\n')
            elif action["type"] == "ps":
                textbox.insert("end", f'PowerShell: {action["cmd"]}\\n')
            elif action["type"] == "scheduled_task":
                textbox.insert("end", f'Tarea: {action["path"]}\\{action["name"]}\\n')
        ending = (
            "Se guarda el valor anterior para revertir este cambio desde Actividad."
            if tweak["mode"] == "track" else
            "Acción puntual: no tiene reversión automática."
        )
        textbox.insert("end", "\\n" + ending)
        textbox.configure(state="disabled")

    def pending(self):
        selected_ids = {t["id"] for t in self.vis if self.vars[t["id"]].get()}
        applied_ids = set(self.st["applied"])
        apply_items = [
            t for t in self.vis
            if t["id"] in selected_ids
            and not t.get("locked")
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
        ap, rv = self.pending()
        self.pending_lbl.configure(text=f"{len(ap)} por aplicar · {len(rv)} por revertir")
        required_ack = tuple(sorted(
            t["id"] for t in ap if t.get("risk") in ("caution", "extreme")
        ))
        previous_ack = getattr(self, "_risk_ack_items", ())
        if required_ack != previous_ack:
            self._risk_ack_items = required_ack
            self.risk_ack = False
            if getattr(self, "risk_ok", None) is not None:
                self.risk_ok.set(False)
        ext = any(t.get("risk") == "extreme" for t in ap)
        caution = any(t.get("risk") == "caution" for t in ap)
        if ext or caution:
            warning_text = (
                "Hay cambios de riesgo alto seleccionados. Revisá sus efectos y la posibilidad de recuperación."
                if ext else
                "Hay ajustes con precauciones seleccionados. Verificá qué funciones o preferencias pueden cambiar."
            )
            self.banner.configure(
                text="  " + warning_text + "  ",
                fg_color=RED if ext else "#6B5430"
            )
            anchor = self.pending_lbl.master
            while getattr(anchor, "master", None) is not self.content:
                anchor = anchor.master
            self.banner.pack(fill="x", padx=28, pady=(0, 6), before=anchor)
        else:
            self.banner.pack_forget()
    def show_pending(self):
        ap, rv = self.pending(); w = ctk.CTkToplevel(self); w.wm_title("Cambios pendientes"); w.geometry("560x460"); w.configure(fg_color=BG); w.after(120, w.lift)
        tb = ctk.CTkTextbox(w, fg_color=CARD, font=self.f_n); tb.pack(fill="both", expand=True, padx=18, pady=18)
        lines = ["POR APLICAR"]
        for item in ap:
            lines.append("  + " + item["name"])
            if item.get("warn"):
                lines.append("      Precaución: " + item["warn"])
        if not ap:
            lines.append("  (nada)")
        lines.extend(["", "POR REVERTIR"])
        lines.extend("  - " + item["name"] for item in rv)
        if not rv:
            lines.append("  (nada)")
        tb.insert("1.0", "\\n".join(lines))
        tb.configure(state="disabled")

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
        if any(t.get("risk") in ("caution", "extreme") for t in ap) and not self.risk_ok.get():
            return messagebox.showwarning(
                "ZyroTech",
                "Revisá las advertencias y marcá 'Entiendo los riesgos' para aplicar ajustes con precaución o riesgo alto."
            )
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
        card = self.card(body, fg="#181322", corner_radius=18)
        card.pack(fill="x", pady=4)
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=18, pady=15)
        self.btn(row, "Iniciar prueba DNS", self.dns_test, width=180).pack(side="left")
        ctk.CTkLabel(
            row, text="Mide consultas DNS reales; no cambia la configuración de Windows.",
            font=self.f_s, text_color=MUTE
        ).pack(side="left", padx=12)
        self.dns_f = ctk.CTkFrame(body, fg_color="transparent")
        self.dns_f.pack(fill="x", pady=12)
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
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
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
        self.heading(
            "Actividad y restauración",
            "Revisá qué cambios administra ZyroTech y revertí cada uno por separado."
        )
        box = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        box.pack(fill="both", expand=True, padx=28, pady=(0, 14))

        current = self.card(box, fg="#181322", corner_radius=18)
        current.pack(fill="x", pady=(2, 14))
        top = ctk.CTkFrame(current, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(
            top, text="CAMBIOS ACTIVOS", font=self.f_b, text_color=ACC, anchor="w"
        ).pack(side="left")
        ctk.CTkLabel(
            top, text=f'{len(self.st["applied"])} administrados',
            font=self.f_s, text_color=MUTE, anchor="e"
        ).pack(side="right")

        if not self.st["applied"]:
            ctk.CTkLabel(
                current, text="Todavía no hay cambios administrados por ZyroTech.",
                font=self.f_n, text_color=TEXT, anchor="w"
            ).pack(fill="x", padx=18, pady=(4, 18))
        else:
            for tid in list(self.st["applied"]):
                row = ctk.CTkFrame(current, fg_color=CARD2, corner_radius=11)
                row.pack(fill="x", padx=14, pady=4)
                ctk.CTkLabel(
                    row, text=self.tname(tid), font=self.f_n, text_color=TEXT,
                    anchor="w", wraplength=620, justify="left"
                ).pack(side="left", fill="x", expand=True, padx=13, pady=11)
                self.btn(
                    row, "Revertir", lambda i=tid: self.revert_one(i),
                    "ghost", width=92, height=32
                ).pack(side="right", padx=10, pady=6)
            ctk.CTkFrame(current, fg_color=LINE, height=1).pack(fill="x", padx=16, pady=(10, 8))
            self.btn(
                current, "Revertir todos los cambios", self.revert_all,
                "red", width=220, height=38
            ).pack(anchor="e", padx=16, pady=(0, 14))

        log_card = self.card(box, fg="#181322", corner_radius=18)
        log_card.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(
            log_card, text="REGISTRO RECIENTE", font=self.f_b,
            text_color=ACC, anchor="w"
        ).pack(fill="x", padx=18, pady=(16, 10))
        if not self.hist:
            ctk.CTkLabel(
                log_card, text="Las aplicaciones y reversiones aparecerán acá.",
                font=self.f_n, text_color=MUTE, anchor="w"
            ).pack(fill="x", padx=18, pady=(0, 18))
        for h in reversed(self.hist[-60:]):
            entry = ctk.CTkFrame(log_card, fg_color=CARD2, corner_radius=10)
            entry.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(
                entry, text=h.get("t", "--/-- --:--"), font=self.f_s,
                text_color=MUTE, width=118, anchor="w"
            ).pack(side="left", padx=(12, 5), pady=10)
            ctk.CTkLabel(
                entry, text=h.get("a", "Cambio"), font=self.f_b,
                text_color=GREEN if h.get("ok") else RED, width=100, anchor="w"
            ).pack(side="left", padx=5, pady=10)
            ctk.CTkLabel(
                entry, text=h.get("n", "Ajuste"), font=self.f_n,
                text_color=TEXT, anchor="w", wraplength=620, justify="left"
            ).pack(side="left", fill="x", expand=True, padx=8, pady=10)

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
            "Conocé ZyroTech",
            "Una herramienta local para revisar, entender y administrar ajustes de Windows."
        )
        body = ctk.CTkScrollableFrame(self.content, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=28, pady=(0, 16))

        hero = self.card(body, fg="#21182F", corner_radius=22, border_color="#554078")
        hero.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(
            hero, text="ZT  /  ZYROTECH FREE",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color="#C6AFFF", anchor="w"
        ).pack(fill="x", padx=22, pady=(20, 7))
        ctk.CTkLabel(
            hero, text="Más control sobre tu PC.\nSin cajas negras.",
            font=ctk.CTkFont(family="Segoe UI", size=29, weight="bold"),
            text_color=TEXT, anchor="w", justify="left"
        ).pack(fill="x", padx=22, pady=(0, 8))
        ctk.CTkLabel(
            hero, text="El análisis se realiza en tu equipo. Podés inspeccionar la compatibilidad y el estado de cada ajuste antes de decidir qué cambiar.",
            font=self.f_n, text_color="#D4CADF", anchor="w",
            wraplength=850, justify="left"
        ).pack(fill="x", padx=22, pady=(0, 20))

        cards = ctk.CTkFrame(body, fg_color="transparent")
        cards.pack(fill="x")
        cards.grid_columnconfigure((0, 1), weight=1, uniform="about")
        items = [
            ("01  PRIVACIDAD", "El diagnóstico y la aplicación de ajustes se ejecutan localmente."),
            ("02  CONTROL", "Cada cambio muestra su estado y puede revertirse cuando existe una acción inversa."),
            ("03  COMPATIBILIDAD", "La detección filtra ajustes según el hardware y la versión de Windows."),
            ("04  TRANSPARENCIA", "La cobertura representa ajustes comprobados; no es una puntuación de FPS."),
        ]
        for index, (title, description) in enumerate(items):
            tile = ctk.CTkFrame(
                cards, fg_color="#181322", corner_radius=16,
                border_width=1, border_color=LINE
            )
            tile.grid(
                row=index // 2, column=index % 2, sticky="nsew",
                padx=5, pady=5
            )
            ctk.CTkLabel(
                tile, text=title,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=ACC, anchor="w"
            ).pack(fill="x", padx=17, pady=(16, 7))
            ctk.CTkLabel(
                tile, text=description, font=self.f_n, text_color=MUTE,
                anchor="w", wraplength=420, justify="left"
            ).pack(fill="x", padx=17, pady=(0, 17))

        pro = self.card(body, fg="#21182F", corner_radius=18, border_color="#554078")
        pro.pack(fill="x", pady=(14, 4))
        pro_row = ctk.CTkFrame(pro, fg_color="transparent")
        pro_row.pack(fill="x", padx=18, pady=16)
        copy = ctk.CTkFrame(pro_row, fg_color="transparent")
        copy.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            copy, text="ZYROTECH PRO  /  EN DESARROLLO",
            font=self.f_b, text_color="#C6AFFF", anchor="w"
        ).pack(fill="x")
        ctk.CTkLabel(
            copy, text="Una suite avanzada, en desarrollo.",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color=TEXT, anchor="w"
        ).pack(fill="x", pady=(5, 3))
        ctk.CTkLabel(
            copy, text="La edición Free seguirá siendo útil por sí sola. Pro sumará herramientas adicionales cuando estén terminadas y probadas.",
            font=self.f_n, text_color="#D4CADF", anchor="w",
            wraplength=650, justify="left"
        ).pack(fill="x")
        ctk.CTkLabel(
            pro_row, text="PRÓXIMAMENTE", fg_color="#3B2D53",
            text_color="#D6C7FF", corner_radius=9, font=self.f_s,
            padx=13, pady=10
        ).pack(side="right", padx=(12, 0))

if __name__ == "__main__":
    if "--revert-all" in sys.argv: headless_revert(); sys.exit(0)
    if not core.IS_WIN: sys.exit("ZyroTech solo corre en Windows.")
    App().mainloop()
