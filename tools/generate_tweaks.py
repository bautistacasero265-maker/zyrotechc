#!/usr/bin/env python3
"""Genera tweaks.json. Editar acá y correr: python tools/generate_tweaks.py"""
import json, os, collections, re
T = []
SYS = "HKLM\\SYSTEM\\CurrentControlSet"
POL = "HKLM\\SOFTWARE\\Policies\\Microsoft"
HCV = "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion"
CV = "HKCU\\Software\\Microsoft\\Windows\\CurrentVersion"
EXP = CV + "\\Explorer"; ADV = EXP + "\\Advanced"
CDM = CV + "\\ContentDeliveryManager"
KRN = SYS + "\\Control\\Session Manager\\kernel"
MM = SYS + "\\Control\\Session Manager\\Memory Management"
MMCSS = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Multimedia\\SystemProfile"
TCP = SYS + "\\Services\\Tcpip\\Parameters"
MOU = "HKCU\\Control Panel\\Mouse"; DESK = "HKCU\\Control Panel\\Desktop"
EDGE = POL + "\\Edge"

def R(path, name, val, vt=None):
    if vt is None:
        vt = "REG_DWORD" if isinstance(val, int) else "REG_BINARY" if isinstance(val, bytes) else "REG_SZ"
    if isinstance(val, bytes): val = val.hex()
    return {"type": "reg", "path": path, "name": name, "value": val, "vtype": vt}
def P(cmd, undo=None, capture=None):
    d = {"type": "ps", "cmd": cmd}
    if undo is not None: d["undo"] = undo
    if capture: d["capture"] = capture
    return d
def A(mod, name, *acts, risk="normal", req=None, reboot=False, mode="track"):
    T.append({"module": mod, "name": name, "risk": risk, "req": req or {}, "reboot": reboot, "mode": mode, "actions": list(acts)})
def one(mod, name, path, rn, val, **kw): A(mod, name, R(path, rn, val), **kw)
def many(mod, name, path, pairs, **kw): A(mod, name, *[R(path, k, v) for k, v in pairs], **kw)
def svc(name, label, start=4, **kw): one("Servicios", f"Servicio {label} desactivado", f"{SYS}\\Services\\{name}", "Start", start, **kw)
def task(path, tn, label):
    A("Tareas", f"Tarea programada: {label}",
      P(f"Disable-ScheduledTask -TaskPath '{path}' -TaskName '{tn}' -ErrorAction SilentlyContinue | Out-Null; exit 0",
        f"Enable-ScheduledTask -TaskPath '{path}' -TaskName '{tn}' -ErrorAction SilentlyContinue | Out-Null; exit 0"))
def clean(name, cmd, req=None): A("Mantenimiento", name, P(cmd + "; exit 0"), mode="once", req=req)
def rm(expr): return f"Remove-Item -Path ({expr}) -Recurse -Force -ErrorAction SilentlyContinue"

# ---------- Privacidad ----------
DC = POL + "\\Windows\\DataCollection"
one("Privacidad", "Telemetría al mínimo (política)", DC, "AllowTelemetry", 0)
one("Privacidad", "Telemetría al mínimo (Policies del sistema)", HCV + "\\Policies\\DataCollection", "AllowTelemetry", 0)
one("Privacidad", "Sin notificaciones de feedback", DC, "DoNotShowFeedbackNotifications", 1)
one("Privacidad", "Limitar logs de diagnóstico", DC, "LimitDiagnosticLogCollection", 1)
one("Privacidad", "Sin descargas OneSettings", DC, "DisableOneSettingsDownloads", 1)
one("Privacidad", "Limitar volcados de diagnóstico", DC, "LimitDumpCollection", 1)
one("Privacidad", "ID de publicidad desactivado", CV + "\\AdvertisingInfo", "Enabled", 0)
one("Privacidad", "ID de publicidad desactivado (política)", POL + "\\Windows\\AdvertisingInfo", "DisabledByGroupPolicy", 1)
one("Privacidad", "No compartir idioma con sitios web", "HKCU\\Control Panel\\International\\User Profile", "HttpAcceptLanguageOptOut", 1)
one("Privacidad", "Experiencias personalizadas con diagnóstico OFF", CV + "\\Privacy", "TailoredExperiencesWithDiagnosticDataEnabled", 0)
one("Privacidad", "No rastrear apps lanzadas", ADV, "Start_TrackProgs", 0)
many("Privacidad", "Historial de actividad desactivado", POL + "\\Windows\\System", [("EnableActivityFeed", 0), ("PublishUserActivities", 0), ("UploadUserActivities", 0)])
many("Privacidad", "Ubicación desactivada (política)", POL + "\\Windows\\LocationAndSensors", [("DisableLocation", 1), ("DisableLocationScripting", 1)])
A("Privacidad", "Reporte de errores desactivado", R(POL + "\\Windows\\Windows Error Reporting", "Disabled", 1), R("HKLM\\SOFTWARE\\Microsoft\\Windows\\Windows Error Reporting", "Disabled", 1))
one("Privacidad", "Programa de mejora de experiencia (CEIP) OFF", POL + "\\SQMClient\\Windows", "CEIPEnable", 0)
many("Privacidad", "Telemetría de compatibilidad OFF", POL + "\\Windows\\AppCompat", [("AITEnable", 0), ("DisableInventory", 1), ("DisableUAR", 1), ("DisablePCA", 1)])
A("Privacidad", "Personalización de entrada/escritura OFF",
  R("HKCU\\Software\\Microsoft\\InputPersonalization", "RestrictImplicitInkCollection", 1),
  R("HKCU\\Software\\Microsoft\\InputPersonalization", "RestrictImplicitTextCollection", 1),
  R("HKCU\\Software\\Microsoft\\InputPersonalization\\TrainedDataStore", "HarvestContacts", 0),
  R("HKCU\\Software\\Microsoft\\Personalization\\Settings", "AcceptedPrivacyPolicy", 0))
one("Privacidad", "Reconocimiento de voz online OFF", "HKCU\\Software\\Microsoft\\Speech_OneCore\\Settings\\OnlineSpeechPrivacy", "HasAccepted", 0)
many("Privacidad", "Sincronización de configuración OFF", POL + "\\Windows\\SettingSync", [("DisableSettingSync", 2), ("DisableSettingSyncUserOverride", 1)])
one("Privacidad", "Portapapeles entre dispositivos OFF", POL + "\\Windows\\System", "AllowCrossDeviceClipboard", 0)
one("Privacidad", "Cortana desactivada", POL + "\\Windows\\Windows Search", "AllowCortana", 0)
A("Privacidad", "Búsqueda web en Inicio desactivada", R(POL + "\\Windows\\Windows Search", "DisableWebSearch", 1), R(POL + "\\Windows\\Windows Search", "ConnectedSearchUseWeb", 0), R(CV + "\\Search", "BingSearchEnabled", 0))
many("Privacidad", "Búsqueda sin ubicación ni nube", POL + "\\Windows\\Windows Search", [("AllowSearchToUseLocation", 0), ("AllowCloudSearch", 0)])
one("Privacidad", "Sugerencias del cuadro de búsqueda OFF", "HKCU\\Software\\Policies\\Microsoft\\Windows\\Explorer", "DisableSearchBoxSuggestions", 1)
one("Privacidad", "Resaltados de búsqueda OFF", CV + "\\SearchSettings", "IsDynamicSearchBoxEnabled", 0)
A("Privacidad", "Copilot desactivado", R("HKCU\\Software\\Policies\\Microsoft\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", 1), R(POL + "\\Windows\\WindowsCopilot", "TurnOffWindowsCopilot", 1))
one("Privacidad", "Botón de Copilot oculto", ADV, "ShowCopilotButton", 0, req={"win11": True})
one("Privacidad", "Análisis de datos con IA (Recall) OFF", POL + "\\Windows\\WindowsAI", "DisableAIDataAnalysis", 1, req={"win11": True})
one("Privacidad", "Windows Ink Workspace OFF", POL + "\\WindowsInkWorkspace", "AllowWindowsInkWorkspace", 0)
A("Privacidad", "Telemetría de Office OFF", R("HKCU\\Software\\Policies\\Microsoft\\office\\16.0\\osm", "Enablelogging", 0), R("HKCU\\Software\\Policies\\Microsoft\\office\\16.0\\osm", "EnableUpload", 0), R("HKCU\\Software\\Microsoft\\Office\\Common\\ClientTelemetry", "DisableTelemetry", 1))
one("Privacidad", "Telemetría de Visual Studio OFF", "HKCU\\Software\\Microsoft\\VisualStudio\\Telemetry", "TurnOffSwitch", 1)
A("Privacidad", "Chrome: sin métricas ni modo segundo plano", R("HKLM\\SOFTWARE\\Policies\\Google\\Chrome", "MetricsReportingEnabled", 0), R("HKLM\\SOFTWARE\\Policies\\Google\\Chrome", "BackgroundModeEnabled", 0))
A("Privacidad", "Firefox: sin telemetría ni estudios", R("HKLM\\SOFTWARE\\Policies\\Mozilla\\Firefox", "DisableTelemetry", 1), R("HKLM\\SOFTWARE\\Policies\\Mozilla\\Firefox", "DisableFirefoxStudies", 1))
one("Privacidad", "Asistencia remota desactivada", SYS + "\\Control\\Remote Assistance", "fAllowToGetHelp", 0)
one("Privacidad", "LLMNR desactivado", POL + "\\Windows NT\\DNSClient", "EnableMulticast", 0)
one("Privacidad", "mDNS desactivado", SYS + "\\Services\\Dnscache\\Parameters", "EnableMDNS", 0)
one("Privacidad", "Sin archivos recientes en Acceso rápido", EXP, "ShowRecent", 0)
one("Privacidad", "Sin carpetas frecuentes en Acceso rápido", EXP, "ShowFrequent", 0)

# ---------- Debloat ----------
cdm = [("Apps sugeridas e instalación silenciosa OFF", ["SilentInstalledAppsEnabled", "PreInstalledAppsEnabled", "PreInstalledAppsEverEnabled", "OemPreInstalledAppsEnabled", "ContentDeliveryAllowed", "FeatureManagementEnabled"]),
       ("Sugerencias en Inicio OFF", ["SystemPaneSuggestionsEnabled", "SubscribedContent-338388Enabled"]),
       ("Consejos y trucos OFF", ["SubscribedContent-338389Enabled", "SoftLandingEnabled"]),
       ("Sugerencias en Configuración OFF", ["SubscribedContent-338393Enabled", "SubscribedContent-353694Enabled", "SubscribedContent-353696Enabled"]),
       ("Spotlight en pantalla de bloqueo OFF", ["RotatingLockScreenEnabled", "RotatingLockScreenOverlayEnabled", "SubscribedContent-338387Enabled"]),
       ("Contenido sugerido extra OFF", ["SubscribedContent-310093Enabled"])]
for n, keys in cdm: many("Debloat", n, CDM, [(k, 0) for k in keys])
one("Debloat", "Pantalla de bienvenida post-actualización OFF", CV + "\\UserProfileEngagement", "ScoobeSystemSettingEnabled", 0)
one("Debloat", "Recomendaciones del menú Inicio OFF", ADV, "Start_IrisRecommendations", 0, req={"win11": True})
one("Debloat", "Notificaciones de cuenta en Inicio OFF", ADV, "Start_AccountNotifications", 0)
one("Debloat", "Anuncios del explorador (OneDrive) OFF", ADV, "ShowSyncProviderNotifications", 0)
CC = POL + "\\Windows\\CloudContent"
one("Debloat", "Funciones de consumidor OFF", CC, "DisableWindowsConsumerFeatures", 1)
one("Debloat", "Sugerencias de terceros OFF", CC, "DisableThirdPartySuggestions", 1)
one("Debloat", "Contenido optimizado en la nube OFF", CC, "DisableCloudOptimizedContent", 1)
one("Debloat", "Spotlight de Windows OFF (política)", "HKCU\\Software\\Policies\\Microsoft\\Windows\\CloudContent", "DisableWindowsSpotlightFeatures", 1)
one("Debloat", "Widgets desactivados", POL + "\\Dsh", "AllowNewsAndInterests", 0, req={"win11": True})
one("Debloat", "Botón de Widgets oculto", ADV, "TaskbarDa", 0, req={"win11": True})
one("Debloat", "Icono de Chat/Teams oculto", ADV, "TaskbarMn", 0, req={"win11": True})
one("Debloat", "Noticias e intereses OFF", POL + "\\Windows\\Windows Feeds", "EnableFeeds", 0)
one("Debloat", "OneDrive: sincronización desactivada", POL + "\\Windows\\OneDrive", "DisableFileSyncNGSC", 1)
RUN = CV + "\\Run"
for v, n in [("OneDrive", "OneDrive"), ("Steam", "Steam"), ("Discord", "Discord"), ("Spotify", "Spotify"), ("com.squirrel.Teams.Teams", "Teams"), ("EpicGamesLauncher", "Epic Games Launcher")]:
    one("Inicio", f"{n} no arranca con Windows", RUN, v, None)
for k, n in [("StartupBoostEnabled", "Edge: sin Startup Boost"), ("BackgroundModeEnabled", "Edge: sin modo segundo plano"), ("MetricsReportingEnabled", "Edge: sin métricas"), ("PersonalizationReportingEnabled", "Edge: sin personalización"), ("EdgeShoppingAssistantEnabled", "Edge: sin asistente de compras"), ("HubsSidebarEnabled", "Edge: sin barra lateral"), ("SpotlightExperiencesAndRecommendationsEnabled", "Edge: sin recomendaciones"), ("ShowRecommendationsEnabled", "Edge: sin sugerencias"), ("EdgeFollowEnabled", "Edge: sin Follow"), ("UserFeedbackAllowed", "Edge: sin feedback"), ("EdgeCollectionsEnabled", "Edge: sin Colecciones")]:
    one("Debloat", n, EDGE, k, 0)
one("Debloat", "Edge: Do Not Track activado", EDGE, "ConfigureDoNotTrack", 1)
one("Debloat", "Edge: datos de diagnóstico mínimos", EDGE, "DiagnosticData", 0)
apps = [("Microsoft.BingNews", "Noticias"), ("Microsoft.BingWeather", "Clima"), ("Microsoft.GetHelp", "Obtener ayuda"), ("Microsoft.Getstarted", "Consejos"), ("Microsoft.Microsoft3DViewer", "Visor 3D"), ("Microsoft.MicrosoftOfficeHub", "Office Hub"), ("Microsoft.MicrosoftSolitaireCollection", "Solitario"), ("Microsoft.MixedReality.Portal", "Realidad mixta"), ("Microsoft.People", "Contactos"), ("Microsoft.SkypeApp", "Skype"), ("Microsoft.WindowsFeedbackHub", "Centro de opiniones"), ("Microsoft.YourPhone", "Vínculo con el móvil"), ("Microsoft.ZuneMusic", "Groove/Media Player viejo"), ("Microsoft.ZuneVideo", "Películas y TV"), ("Clipchamp.Clipchamp", "Clipchamp"), ("Microsoft.PowerAutomateDesktop", "Power Automate"), ("MicrosoftTeams", "Teams (personal)"), ("Microsoft.549981C3F5F10", "Cortana app"), ("Microsoft.WindowsMaps", "Mapas"), ("Microsoft.BingSearch", "Bing Search"), ("Microsoft.OutlookForWindows", "Outlook nuevo")]
for pk, n in apps:
    A("Debloat", f"Quitar app: {n} (irreversible)", P(f"Get-AppxPackage -AllUsers -Name '{pk}' | Remove-AppxPackage -AllUsers -ErrorAction SilentlyContinue; Get-AppxProvisionedPackage -Online | ? DisplayName -eq '{pk}' | Remove-AppxProvisionedPackage -Online -ErrorAction SilentlyContinue | Out-Null; exit 0"), mode="once")
A("Debloat", "Menú contextual clásico de Windows 10", R("HKCU\\Software\\Classes\\CLSID\\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}\\InprocServer32", "", ""), req={"win11": True})

# ---------- Servicios ----------
for n, l in [("DiagTrack", "Telemetría (DiagTrack)"), ("dmwappushservice", "WAP Push"), ("MapsBroker", "Mapas descargados"), ("lfsvc", "Geolocalización"), ("RetailDemo", "Demo de tienda"), ("Fax", "Fax"), ("WMPNetworkSvc", "Uso compartido de Media Player"), ("SEMgrSvc", "Pagos NFC"), ("WpcMonSvc", "Control parental"), ("PhoneSvc", "Teléfono"), ("icssvc", "Zona móvil"), ("wisvc", "Windows Insider"), ("WerSvc", "Reporte de errores"), ("diagnosticshub.standardcollector.service", "Recolector de diagnóstico"), ("XblAuthManager", "Xbox Live Auth"), ("XblGameSave", "Xbox Game Save"), ("XboxNetApiSvc", "Xbox Networking"), ("RemoteRegistry", "Registro remoto"), ("AJRouter", "AllJoyn"), ("ALG", "Puerta de enlace capa app"), ("lltdsvc", "Link-Layer Topology"), ("WalletService", "Wallet"), ("CscService", "Archivos sin conexión"), ("WebClient", "WebDAV"), ("PcaSvc", "Asistente de compatibilidad")]:
    svc(n, l)
svc("SysMain", "SysMain/Superfetch (SSD)", req={"ssd": True})
svc("WSearch", "Windows Search (pierde la búsqueda indexada)")
svc("NvTelemetryContainer", "NVIDIA Telemetry", req={"gpu": "nvidia"})

# ---------- Tareas ----------
AE = "\\Microsoft\\Windows\\Application Experience\\"; CE = "\\Microsoft\\Windows\\Customer Experience Improvement Program\\"
for p, t, l in [(AE, "Microsoft Compatibility Appraiser", "Compatibility Appraiser"), (AE, "ProgramDataUpdater", "ProgramDataUpdater"), (AE, "StartupAppTask", "StartupAppTask"), (CE, "Consolidator", "CEIP Consolidator"), (CE, "UsbCeip", "CEIP USB"), (CE, "KernelCeipTask", "CEIP Kernel"), ("\\Microsoft\\Windows\\Feedback\\Siuf\\", "DmClient", "Feedback DmClient"), ("\\Microsoft\\Windows\\Feedback\\Siuf\\", "DmClientOnScenarioDownload", "Feedback Scenario"), ("\\Microsoft\\Windows\\Windows Error Reporting\\", "QueueReporting", "WER QueueReporting"), ("\\Microsoft\\Windows\\DiskDiagnostic\\", "Microsoft-Windows-DiskDiagnosticDataCollector", "Disk Diagnostic"), ("\\Microsoft\\Windows\\Autochk\\", "Proxy", "Autochk Proxy"), ("\\Microsoft\\Windows\\Maps\\", "MapsUpdateTask", "Maps Update"), ("\\Microsoft\\Windows\\Maps\\", "MapsToastTask", "Maps Toast"), ("\\Microsoft\\Windows\\NetTrace\\", "GatherNetworkInfo", "NetTrace"), ("\\Microsoft\\Windows\\PI\\", "Sqm-Tasks", "SQM Tasks"), ("\\Microsoft\\Windows\\Power Efficiency Diagnostics\\", "AnalyzeSystem", "Power Efficiency Diagnostics"), ("\\Microsoft\\Windows\\Shell\\", "FamilySafetyMonitor", "Family Safety Monitor"), ("\\Microsoft\\Windows\\Shell\\", "FamilySafetyRefreshTask", "Family Safety Refresh")]:
    task(p, t, l)
A("Tareas", "Tareas de telemetría NVIDIA", P("Get-ScheduledTask -TaskName 'NvTmRep*','NvTmMon*' -ErrorAction SilentlyContinue | Disable-ScheduledTask | Out-Null; exit 0", "Get-ScheduledTask -TaskName 'NvTmRep*','NvTmMon*' -ErrorAction SilentlyContinue | Enable-ScheduledTask | Out-Null; exit 0"), req={"gpu": "nvidia"})

# ---------- Gaming / GPU ----------
GCS = "HKCU\\System\\GameConfigStore"
one("Gaming", "Game DVR desactivado", GCS, "GameDVR_Enabled", 0)
one("Gaming", "Captura en segundo plano OFF", CV + "\\GameDVR", "AppCaptureEnabled", 0)
one("Gaming", "Historial de captura OFF", CV + "\\GameDVR", "HistoricalCaptureEnabled", 0)
one("Gaming", "Game DVR desactivado (política)", POL + "\\Windows\\GameDVR", "AllowGameDVR", 0)
many("Gaming", "Game Bar: sin panel ni atajos de mando", "HKCU\\Software\\Microsoft\\GameBar", [("UseNexusForGameBarEnabled", 0), ("ShowStartupPanel", 0)])
many("Gaming", "Optimizaciones de pantalla completa OFF", GCS, [("GameDVR_FSEBehaviorMode", 2), ("GameDVR_HonorUserFSEBehaviorMode", 1), ("GameDVR_DXGIHonorFSEWindowsCompatible", 1), ("GameDVR_EFSEFeatureFlags", 0)])
many("Gaming", "Modo Juego activado", "HKCU\\Software\\Microsoft\\GameBar", [("AutoGameModeEnabled", 1), ("AllowAutoGameMode", 1)])
A("Gaming", "Optimizaciones para juegos en ventana + VRR", R("HKCU\\Software\\Microsoft\\DirectX\\UserGpuPreferences", "DirectXUserGlobalSettings", "SwapEffectUpgradeEnable=1;VRROptimizeEnable=1;"))
one("Gaming", "Programación de GPU acelerada por hardware (HAGS)", SYS + "\\Control\\GraphicsDrivers", "HwSchMode", 2, reboot=True, req={"win11": True})
one("Gaming", "Multiplane Overlay desactivado (si hay stutter)", "HKLM\\SOFTWARE\\Microsoft\\Windows\\Dwm", "OverlayTestMode", 5, reboot=True)
many("Gaming", "Prioridad MMCSS para juegos", MMCSS + "\\Tasks\\Games", [("GPU Priority", 8), ("Priority", 6), ("Scheduling Category", "High"), ("SFIO Priority", "High")])
A("Gaming", "MSI mode en la GPU", P("Get-PnpDevice -Class Display -Status OK | % { $p='HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\'+$_.InstanceId+'\\Device Parameters\\Interrupt Management\\MessageSignaledInterruptProperties'; New-Item -Path $p -Force | Out-Null; Set-ItemProperty -Path $p -Name MSISupported -Value 1 -Type DWord }",
  "Get-PnpDevice -Class Display -Status OK | % { $p='HKLM:\\SYSTEM\\CurrentControlSet\\Enum\\'+$_.InstanceId+'\\Device Parameters\\Interrupt Management\\MessageSignaledInterruptProperties'; Remove-ItemProperty -Path $p -Name MSISupported -ErrorAction SilentlyContinue }"), reboot=True)
A("Gaming", "AMD: ULPS desactivado (ahorro de energía de GPU)", P("Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}' -ErrorAction SilentlyContinue | ? { $_.PSChildName -match '^\\d{4}$' -and (Get-ItemProperty $_.PSPath).DriverDesc -match 'AMD|Radeon' } | % { Set-ItemProperty $_.PSPath -Name EnableUlps -Value 0 -Type DWord }",
  "Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Control\\Class\\{4d36e968-e325-11ce-bfc1-08002be10318}' -ErrorAction SilentlyContinue | ? { $_.PSChildName -match '^\\d{4}$' -and (Get-ItemProperty $_.PSPath).DriverDesc -match 'AMD|Radeon' } | % { Remove-ItemProperty $_.PSPath -Name EnableUlps -ErrorAction SilentlyContinue }"), req={"gpu": "amd"}, reboot=True)
many("Gaming", "NVIDIA: flags de telemetría OFF", "HKLM\\SOFTWARE\\NVIDIA Corporation\\Global\\FTS", [("EnableRID44231", 0), ("EnableRID64640", 0), ("EnableRID66610", 0)], req={"gpu": "nvidia"})
one("Gaming", "NVIDIA: no participar en programa de mejora", "HKLM\\SOFTWARE\\NVIDIA Corporation\\NvControlPanel2\\Client", "OptInOrOutPreference", 0, req={"gpu": "nvidia"})

# ---------- Kernel y latencia ----------
one("Kernel", "Separación de prioridad de procesos 0x26", SYS + "\\Control\\PriorityControl", "Win32PrioritySeparation", 38)
one("Kernel", "Resolución de timer global", KRN, "GlobalTimerResolutionRequests", 1, reboot=True)
one("Kernel", "Distribuir timers entre núcleos", KRN, "DistributeTimers", 1, reboot=True)
A("Kernel", "Sin tick dinámico", P("bcdedit /set disabledynamictick yes", "bcdedit /deletevalue disabledynamictick; exit 0"), reboot=True)
A("Kernel", "Reloj de plataforma por defecto (quita useplatformclock)", P("bcdedit /deletevalue useplatformclock; exit 0"), mode="once", reboot=True)
one("Kernel", "MMCSS: SystemResponsiveness 0", MMCSS, "SystemResponsiveness", 0)
one("Kernel", "Sin límite de red de multimedia", MMCSS, "NetworkThrottlingIndex", 4294967295)
one("Kernel", "Power Throttling desactivado", SYS + "\\Control\\Power\\PowerThrottling", "PowerThrottlingOff", 1)
one("Kernel", "Inicio rápido desactivado", SYS + "\\Control\\Session Manager\\Power", "HiberbootEnabled", 0)
A("Kernel", "Hibernación desactivada", P("powercfg /h off", "powercfg /h on"))
A("Kernel", "NTFS: sin último acceso", P("fsutil behavior set disablelastaccess 1", "fsutil behavior set disablelastaccess 2"))
A("Kernel", "NTFS: sin nombres 8.3", P("fsutil behavior set disable8dot3 1", "fsutil behavior set disable8dot3 2"))
many("Kernel", "Prefetch desactivado (SSD)", MM + "\\PrefetchParameters", [("EnablePrefetcher", 0), ("EnableSuperfetch", 0)], req={"ssd": True})
A("Kernel", "Almacenamiento reservado desactivado", P("DISM /Online /Set-ReservedStorageState /State:Disabled", "DISM /Online /Set-ReservedStorageState /State:Enabled"), reboot=True)
one("Kernel", "Cierre rápido de servicios", SYS + "\\Control", "WaitToKillServiceTimeout", "2000")
one("Kernel", "Cierre rápido de apps", DESK, "WaitToKillAppTimeout", "2000")
one("Kernel", "Cerrar apps colgadas rápido", DESK, "HungAppTimeout", "2000")
one("Kernel", "Cerrar tareas automáticamente al apagar", DESK, "AutoEndTasks", "1")
one("Kernel", "Kernel en RAM (DisablePagingExecutive)", MM, "DisablePagingExecutive", 1, req={"ram_min": 16}, reboot=True)
A("Kernel", "svchost: servicios compartidos según RAM", P("$kb=[math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory/1KB); Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control' -Name SvcHostSplitThresholdInKB -Value $kb -Type DWord", "Set-ItemProperty -Path 'HKLM:\\SYSTEM\\CurrentControlSet\\Control' -Name SvcHostSplitThresholdInKB -Value 3670016 -Type DWord"), req={"ram_min": 8}, reboot=True)
A("Kernel", "Compresión de memoria desactivada", P("Disable-MMAgent -MemoryCompression", "Enable-MMAgent -MemoryCompression"), req={"ram_min": 16}, reboot=True)
one("Kernel", "Volcado de memoria mínimo", SYS + "\\Control\\CrashControl", "CrashDumpEnabled", 3)
A("Kernel", "Apps en segundo plano denegadas", R(POL + "\\Windows\\AppPrivacy", "LetAppsRunInBackground", 2), R(CV + "\\BackgroundAccessApplications", "GlobalUserDisabled", 1))
one("Kernel", "Retraso de inicio de apps = 0", EXP + "\\Serialize", "StartupDelayInMSec", 0)

# ---------- Energía y CPU ----------
GZ = ("$l=(powercfg -list | Out-String); $m=[regex]::Match(($l -split '\\r?\\n' | ? {$_ -match 'ZyroTech'} | Select -First 1),'[0-9a-f-]{36}'); "
      "if($m.Success){$g=$m.Value}else{$o=(powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61 | Out-String); "
      "if($o -notmatch '[0-9a-f-]{36}'){$o=(powercfg -duplicatescheme 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c | Out-String)}; "
      "$g=[regex]::Match($o,'[0-9a-f-]{36}').Value; powercfg -changename $g 'ZyroTech Ultimate Performance' | Out-Null}; ")
REAPPLY = "$a=[regex]::Match((powercfg /getactivescheme | Out-String),'[0-9a-f-]{36}').Value; powercfg -setactive $a"
A("Energía", "Plan de energía ZyroTech Ultimate Performance",
  P(GZ + "powercfg -setactive $g", "powercfg -setactive {captured}; $l=(powercfg -list | Out-String); $m=[regex]::Match(($l -split '\\r?\\n' | ? {$_ -match 'ZyroTech'} | Select -First 1),'[0-9a-f-]{36}'); if($m.Success){powercfg -delete $m.Value}",
    capture="[regex]::Match((powercfg /getactivescheme | Out-String),'[0-9a-f-]{36}').Value"))
def pw(name, sub, setting, val): A("Energía", name + " (plan ZyroTech)", P(GZ + f"powercfg -setacvalueindex $g {sub} {setting} {val}; " + REAPPLY, ""))
pw("Núcleos mínimos sin aparcar 100%", "SUB_PROCESSOR", "CPMINCORES", 100)
pw("Estado mínimo del procesador 100%", "SUB_PROCESSOR", "PROCTHROTTLEMIN", 100)
pw("Estado máximo del procesador 100%", "SUB_PROCESSOR", "PROCTHROTTLEMAX", 100)
pw("Boost agresivo de CPU", "SUB_PROCESSOR", "PERFBOOSTMODE", 2)
pw("EPP en 0 (máximo rendimiento)", "SUB_PROCESSOR", "PERFEPP", 0)
pw("Política de enfriamiento activa", "SUB_PROCESSOR", "SYSCOOLPOL", 1)
pw("Suspensión selectiva de USB OFF", "2a737441-1930-4402-8d77-b2bebba308a3", "48e6b7a6-50f5-4782-a5d4-53bb8f07e226", 0)
pw("PCIe ASPM desactivado", "SUB_PCIEXPRESS", "ASPM", 0)
pw("Disco nunca se apaga", "SUB_DISK", "DISKIDLE", 0)
pw("Wi-Fi en máximo rendimiento", "19cbb8fa-5279-450e-9fac-8a3d5fedd0c1", "12bbebe6-58d6-4636-95bb-3217ef867c1a", 0)
A("Energía", "Defender: limitar CPU de escaneo al 10%", P("Set-MpPreference -ScanAvgCPULoadFactor 10", "Set-MpPreference -ScanAvgCPULoadFactor 50"))

# ---------- Red ----------
IFS = "HKLM:\\SYSTEM\\CurrentControlSet\\Services\\Tcpip\\Parameters\\Interfaces"
for k, n in [("TcpAckFrequency", "Nagle: TcpAckFrequency=1"), ("TCPNoDelay", "Nagle: TCPNoDelay=1"), ("TcpDelAckTicks", "Nagle: TcpDelAckTicks=0")]:
    v = 0 if k == "TcpDelAckTicks" else 1
    A("Red", n + " en todas las interfaces", P(f"Get-ChildItem '{IFS}' | % {{ New-ItemProperty -Path $_.PSPath -Name {k} -Value {v} -PropertyType DWord -Force | Out-Null }}", f"Get-ChildItem '{IFS}' | % {{ Remove-ItemProperty -Path $_.PSPath -Name {k} -ErrorAction SilentlyContinue }}"))
A("Red", "TCP: RSC desactivado", P("netsh int tcp set global rsc=disabled", "netsh int tcp set global rsc=enabled"))
A("Red", "TCP: RTO inicial 2000 ms", P("netsh int tcp set global initialRto=2000", "netsh int tcp set global initialRto=3000"))
A("Red", "TCP: heurísticas de ventana desactivadas", P("netsh int tcp set heuristics disabled", "netsh int tcp set heuristics enabled"))
A("Red", "TCP: autotuning en normal", P("netsh int tcp set global autotuninglevel=normal", "netsh int tcp set global autotuninglevel=normal"))
for k, v, n in [("DefaultTTL", 64, "TTL por defecto 64"), ("Tcp1323Opts", 1, "Escalado de ventana TCP"), ("TcpTimedWaitDelay", 30, "TIME_WAIT 30 s"), ("MaxUserPort", 65534, "Puertos efímeros hasta 65534"), ("EnablePMTUDiscovery", 1, "Descubrimiento de MTU"), ("EnablePMTUBHDetect", 0, "Sin detección de agujeros negros MTU"), ("SackOpts", 1, "SACK activado"), ("TcpMaxDataRetransmissions", 5, "Retransmisiones máximas 5"), ("EnableICMPRedirect", 0, "ICMP redirect OFF")]:
    one("Red", "TCP/IP: " + n, TCP, k, v)
one("Red", "Sin reserva de ancho de banda QoS (20%)", POL + "\\Windows\\Psched", "NonBestEffortLimit", 0)
one("Red", "QoS: no depender de NLA", SYS + "\\Services\\Tcpip\\QoS", "Do not use NLA", "1")
for exe, g in [("VALORANT-Win64-Shipping.exe", "Valorant"), ("cs2.exe", "CS2"), ("FortniteClient-Win64-Shipping.exe", "Fortnite"), ("cod.exe", "Call of Duty"), ("r5apex.exe", "Apex Legends"), ("RocketLeague.exe", "Rocket League"), ("League of Legends.exe", "League of Legends"), ("Overwatch.exe", "Overwatch"), ("dota2.exe", "Dota 2"), ("RainbowSix.exe", "Rainbow Six Siege"), ("TslGame.exe", "PUBG"), ("GTA5.exe", "GTA V")]:
    nm = "ZyroTech-" + g.replace(" ", "")
    A("Red", f"DSCP 46 para {g} (solo sirve si el router lo respeta)", P(f"if(-not (Get-NetQosPolicy -Name '{nm}' -ErrorAction SilentlyContinue)){{ New-NetQosPolicy -Name '{nm}' -AppPathNameMatchCondition '{exe}' -DSCPAction 46 -NetworkProfile All | Out-Null }}", f"Remove-NetQosPolicy -Name '{nm}' -Confirm:$false -ErrorAction SilentlyContinue"))
A("Red", "DNS Cloudflare (1.1.1.1)", P("Get-NetAdapter -Physical | ? Status -eq Up | Set-DnsClientServerAddress -ServerAddresses ('1.1.1.1','1.0.0.1')", "Get-NetAdapter -Physical | Set-DnsClientServerAddress -ResetServerAddresses"))
A("Red", "DNS Google (8.8.8.8)", P("Get-NetAdapter -Physical | ? Status -eq Up | Set-DnsClientServerAddress -ServerAddresses ('8.8.8.8','8.8.4.4')", "Get-NetAdapter -Physical | Set-DnsClientServerAddress -ResetServerAddresses"))
def nic(kw, val, name):
    cap = "(Get-NetAdapter -Physical | % { $a=Get-NetAdapterAdvancedProperty -Name $_.Name -RegistryKeyword '@KW@' -ErrorAction SilentlyContinue; if($a){ $_.Name+'='+$a.RegistryValue[0] } }) -join ';'"
    app = "Get-NetAdapter -Physical | % { if(Get-NetAdapterAdvancedProperty -Name $_.Name -RegistryKeyword '@KW@' -ErrorAction SilentlyContinue){ Set-NetAdapterAdvancedProperty -Name $_.Name -RegistryKeyword '@KW@' -RegistryValue @V@ } }"
    und = "'{captured}' -split ';' | ? {$_} | % { $n,$v=$_ -split '=',2; Set-NetAdapterAdvancedProperty -Name $n -RegistryKeyword '@KW@' -RegistryValue $v }"
    f = lambda s: s.replace("@KW@", kw).replace("@V@", str(val))
    A("Red", name, P(f(app), f(und), f(cap)))
for kw, n in [("*EEE", "NIC: Energy-Efficient Ethernet OFF"), ("*FlowControl", "NIC: Flow Control OFF"), ("*InterruptModeration", "NIC: Interrupt Moderation OFF"), ("*LsoV2IPv4", "NIC: Large Send Offload v4 OFF"), ("*LsoV2IPv6", "NIC: Large Send Offload v6 OFF"), ("*WakeOnMagicPacket", "NIC: Wake on Magic Packet OFF"), ("*WakeOnPattern", "NIC: Wake on Pattern OFF")]:
    nic(kw, 0, n)
A("Red", "NIC: ahorro de energía del adaptador OFF", P("Get-NetAdapter -Physical | % { Disable-NetAdapterPowerManagement -Name $_.Name -NoRestart -ErrorAction SilentlyContinue }; exit 0", "Get-NetAdapter -Physical | % { Enable-NetAdapterPowerManagement -Name $_.Name -NoRestart -ErrorAction SilentlyContinue }; exit 0"))
A("Red", "Teredo desactivado", P("netsh interface teredo set state disabled", "netsh interface teredo set state default"))
A("Red", "ISATAP desactivado", P("netsh interface isatap set state disabled", "netsh interface isatap set state default"))
A("Red", "6to4 desactivado", P("netsh interface 6to4 set state disabled", "netsh interface 6to4 set state default"))
one("Red", "Optimización de entrega (P2P) desactivada", POL + "\\Windows\\DeliveryOptimization", "DODownloadMode", 0)
one("Red", "Optimización de entrega: sin P2P (usuario)", HCV + "\\DeliveryOptimization\\Config", "DODownloadMode", 0)

# ---------- Periféricos ----------
A("Periféricos", "Mouse: sin aceleración", R(MOU, "MouseSpeed", "0"), R(MOU, "MouseThreshold1", "0"), R(MOU, "MouseThreshold2", "0"))
one("Periféricos", "Mouse: sensibilidad 6/11 (1:1)", MOU, "MouseSensitivity", "10")
A("Periféricos", "Mouse: curvas planas 100% (solo escala 100%)",
  R(MOU, "SmoothMouseXCurve", bytes.fromhex("0000000000000000" "C0CC0C0000000000" "8099190000000000" "4066260000000000" "0033330000000000")),
  R(MOU, "SmoothMouseYCurve", bytes.fromhex("0000000000000000" "0000380000000000" "0000700000000000" "0000A80000000000" "0000E00000000000")))
many("Periféricos", "Teclado: delay mínimo y velocidad máxima", "HKCU\\Control Panel\\Keyboard", [("KeyboardDelay", "0"), ("KeyboardSpeed", "31")])
one("Periféricos", "Sin aviso de Sticky Keys", "HKCU\\Control Panel\\Accessibility\\StickyKeys", "Flags", "506")
one("Periféricos", "Sin aviso de Filter Keys", "HKCU\\Control Panel\\Accessibility\\Keyboard Response", "Flags", "122")
one("Periféricos", "Sin aviso de Toggle Keys", "HKCU\\Control Panel\\Accessibility\\ToggleKeys", "Flags", "58")
many("Periféricos", "Sin feedback visual táctil", "HKCU\\Control Panel\\Cursors", [("ContactVisualization", 0), ("GestureVisualization", 0)])
one("Periféricos", "Audio: sin atenuación en llamadas", "HKCU\\Software\\Microsoft\\Multimedia\\Audio", "UserDuckingPreference", 3)
one("Periféricos", "Sin sonido de inicio", HCV + "\\Authentication\\LogonUI\\BootAnimation", "DisableStartupSound", 1)
one("Periféricos", "USB: suspensión selectiva desactivada (registro)", SYS + "\\Services\\USB", "DisableSelectiveSuspend", 1)
one("Periféricos", "Aero Shake desactivado", ADV, "DisallowShaking", 1)

# ---------- Interfaz ----------
one("Interfaz", "Menús sin retardo", DESK, "MenuShowDelay", "0")
one("Interfaz", "Efectos visuales: mejor rendimiento", EXP + "\\VisualEffects", "VisualFXSetting", 2)
one("Interfaz", "Máscara de efectos visuales mínima", DESK, "UserPreferencesMask", bytes.fromhex("9012038010000000"))
one("Interfaz", "Sin animación al minimizar", DESK + "\\WindowMetrics", "MinAnimate", "0")
one("Interfaz", "Sin animaciones de la barra de tareas", ADV, "TaskbarAnimations", 0)
one("Interfaz", "Transparencia desactivada", CV + "\\Themes\\Personalize", "EnableTransparency", 0)
one("Interfaz", "Aero Peek desactivado", "HKCU\\Software\\Microsoft\\Windows\\DWM", "EnableAeroPeek", 0)
one("Interfaz", "Sin sombras en listas", ADV, "ListviewShadow", 0)

# ---------- Seguridad reducida (RIESGO) ----------
X = dict(risk="extreme")
A("Seguridad", "Defender: protección en tiempo real OFF", P("Set-MpPreference -DisableRealtimeMonitoring $true", "Set-MpPreference -DisableRealtimeMonitoring $false"), **X)
A("Seguridad", "Defender: monitoreo de comportamiento OFF", P("Set-MpPreference -DisableBehaviorMonitoring $true", "Set-MpPreference -DisableBehaviorMonitoring $false"), **X)
A("Seguridad", "Defender: análisis de descargas OFF", P("Set-MpPreference -DisableIOAVProtection $true", "Set-MpPreference -DisableIOAVProtection $false"), **X)
A("Seguridad", "Defender: análisis de scripts OFF", P("Set-MpPreference -DisableScriptScanning $true", "Set-MpPreference -DisableScriptScanning $false"), **X)
A("Seguridad", "Defender: protección en la nube OFF", P("Set-MpPreference -MAPSReporting 0", "Set-MpPreference -MAPSReporting 2"), **X)
A("Seguridad", "Defender: envío de muestras OFF", P("Set-MpPreference -SubmitSamplesConsent 2", "Set-MpPreference -SubmitSamplesConsent 1"), **X)
one("Seguridad", "Defender desactivado por política", POL + "\\Windows Defender", "DisableAntiSpyware", 1, reboot=True, **X)
one("Seguridad", "SmartScreen de Windows OFF", POL + "\\Windows\\System", "EnableSmartScreen", 0, **X)
one("Seguridad", "SmartScreen de Edge OFF", EDGE, "SmartScreenEnabled", 0, **X)
one("Seguridad", "Notificaciones de Seguridad de Windows OFF", "HKLM\\SOFTWARE\\Microsoft\\Windows Defender Security Center\\Notifications", "DisableNotifications", 1, **X)
one("Seguridad", "Windows Update automático OFF", POL + "\\Windows\\WindowsUpdate\\AU", "NoAutoUpdate", 1, **X)
svc("wuauserv", "Windows Update", risk="extreme")
A("Seguridad", "Virtualización (hypervisor) OFF", P("bcdedit /set hypervisorlaunchtype off", "bcdedit /set hypervisorlaunchtype auto"), reboot=True, **X)
one("Seguridad", "Aislamiento de núcleo / VBS OFF", SYS + "\\Control\\DeviceGuard", "EnableVirtualizationBasedSecurity", 0, reboot=True, **X)
one("Seguridad", "Integridad de memoria (HVCI) OFF", SYS + "\\Control\\DeviceGuard\\Scenarios\\HypervisorEnforcedCodeIntegrity", "Enabled", 0, reboot=True, **X)
many("Seguridad", "Mitigaciones Spectre/Meltdown OFF", MM, [("FeatureSettingsOverride", 3), ("FeatureSettingsOverrideMask", 3)], reboot=True, **X)

# ---------- Mantenimiento ----------
clean("Limpiar temporales del usuario", rm("$env:TEMP+'\\*'"))
clean("Limpiar temporales de Windows", rm("$env:WINDIR+'\\Temp\\*'"))
clean("Limpiar caché de shaders DirectX", rm("$env:LOCALAPPDATA+'\\D3DSCache\\*'"))
clean("Limpiar caché de shaders NVIDIA", rm("$env:LOCALAPPDATA+'\\NVIDIA\\DXCache\\*'") + "; " + rm("$env:LOCALAPPDATA+'\\NVIDIA\\GLCache\\*'"), req={"gpu": "nvidia"})
clean("Limpiar caché de shaders AMD", rm("$env:LOCALAPPDATA+'\\AMD\\DxCache\\*'") + "; " + rm("$env:LOCALAPPDATA+'\\AMD\\GLCache\\*'"), req={"gpu": "amd"})
clean("Limpiar caché de Chrome (cerrarlo antes)", rm("$env:LOCALAPPDATA+'\\Google\\Chrome\\User Data\\Default\\Cache\\*'") + "; " + rm("$env:LOCALAPPDATA+'\\Google\\Chrome\\User Data\\Default\\Code Cache\\*'"))
clean("Limpiar caché de Edge (cerrarlo antes)", rm("$env:LOCALAPPDATA+'\\Microsoft\\Edge\\User Data\\Default\\Cache\\*'") + "; " + rm("$env:LOCALAPPDATA+'\\Microsoft\\Edge\\User Data\\Default\\Code Cache\\*'"))
clean("Limpiar caché de Firefox (cerrarlo antes)", rm("$env:LOCALAPPDATA+'\\Mozilla\\Firefox\\Profiles\\*\\cache2'"))
clean("Limpiar caché de Discord", rm("$env:APPDATA+'\\discord\\Cache\\*'") + "; " + rm("$env:APPDATA+'\\discord\\Code Cache\\*'") + "; " + rm("$env:APPDATA+'\\discord\\GPUCache\\*'"))
clean("Limpiar caché web de Steam", rm("$env:LOCALAPPDATA+'\\Steam\\htmlcache\\*'"))
clean("Limpiar caché web de Epic Games", rm("$env:LOCALAPPDATA+'\\EpicGamesLauncher\\Saved\\webcache*'"))
clean("Limpiar reportes de errores (WER)", rm("$env:ProgramData+'\\Microsoft\\Windows\\WER\\ReportQueue\\*'") + "; " + rm("$env:ProgramData+'\\Microsoft\\Windows\\WER\\ReportArchive\\*'"))
clean("Limpiar caché de miniaturas", rm("$env:LOCALAPPDATA+'\\Microsoft\\Windows\\Explorer\\thumbcache_*.db'"))
clean("Limpiar logs de CBS", rm("$env:WINDIR+'\\Logs\\CBS\\*.log'"))
clean("Limpiar minidumps y MEMORY.DMP", rm("$env:WINDIR+'\\Minidump\\*'") + "; " + rm("$env:WINDIR+'\\MEMORY.DMP'"))
clean("Vaciar papelera", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue")
clean("Vaciar caché DNS", "ipconfig /flushdns")
clean("Limpiar caché de Optimización de entrega", "Delete-DeliveryOptimizationCache -Force")
clean("Limpiar descargas de Windows Update", "Stop-Service wuauserv,bits -Force -ErrorAction SilentlyContinue; " + rm("$env:WINDIR+'\\SoftwareDistribution\\Download\\*'") + "; Start-Service wuauserv,bits -ErrorAction SilentlyContinue")
clean("Limpiar componentes de Windows (DISM, tarda)", "DISM /Online /Cleanup-Image /StartComponentCleanup")
clean("Borrar residuos del instalador NVIDIA", rm("'C:\\NVIDIA'"), req={"gpu": "nvidia"})
clean("Borrar residuos del instalador AMD", rm("'C:\\AMD'"), req={"gpu": "amd"})

# ---------- Extras (UX, seguridad básica, telemetría de herramientas) ----------
one("Interfaz", "Mostrar extensiones de archivo", ADV, "HideFileExt", 0)
one("Interfaz", "Mostrar archivos ocultos", ADV, "Hidden", 1)
one("Interfaz", "El Explorador abre en Este equipo", ADV, "LaunchTo", 1)
one("Interfaz", "Ocultar botón Vista de tareas", ADV, "ShowTaskViewButton", 0)
one("Interfaz", "Ocultar cuadro de búsqueda de la barra", CV + "\\Search", "SearchboxTaskbarMode", 0)
one("Gaming", "Game Bar: sin consejo de inicio", "HKCU\\Software\\Microsoft\\GameBar", "GamePanelStartupTipIndex", 3)
one("Debloat", "Storage Sense desactivado", CV + "\\StorageSense\\Parameters\\StoragePolicy", "01", 0)
one("Seguridad básica", "Autoplay desactivado", EXP + "\\AutoplayHandlers", "DisableAutoplay", 1)
one("Seguridad básica", "Autorun desactivado en todas las unidades", HCV + "\\Policies\\Explorer", "NoDriveTypeAutoRun", 255)
for var, n in [("POWERSHELL_TELEMETRY_OPTOUT", "Telemetría de PowerShell 7 OFF"), ("DOTNET_CLI_TELEMETRY_OPTOUT", "Telemetría de .NET CLI OFF")]:
    A("Privacidad", n, P(f"[Environment]::SetEnvironmentVariable('{var}','1','Machine')", f"[Environment]::SetEnvironmentVariable('{var}',$null,'Machine')"))

# ---------- IDs, tiers, pesos, validación ----------
FREE_PICK = ["Game DVR desactivado", "Modo Juego activado", "Telemetría al mínimo (política)", "Mouse: sin aceleración", "Plan de energía ZyroTech Ultimate",
             "Optimizaciones de pantalla completa OFF", "Servicio Telemetría (DiagTrack)", "Cortana desactivada", "Limpiar temporales", "Limpiar caché de shaders DirectX",
             "Vaciar caché DNS", "Vaciar papelera", "Menús sin retardo", "Efectos visuales: mejor rendimiento", "Steam no arranca", "Discord no arranca", "Spotify no arranca",
             "Edge: sin Startup Boost", "Copilot desactivado", "Widgets desactivados", "Mostrar extensiones", "Inicio rápido desactivado", "Teredo desactivado", "Autoplay"]
PRO_PICK = ["Prioridad MMCSS", "MSI mode", "Resolución de timer", "Distribuir timers", "Separación de prioridad", "Nagle", "NIC:", "(plan ZyroTech)", "SystemResponsiveness",
            "Sin límite de red", "HAGS", "Multiplane", "Power Throttling", "DSCP", "Sin tick dinámico", "Compresión de memoria", "Kernel en RAM", "svchost", "TCP", "Sin reserva de ancho",
            "Prefetch", "NTFS", "ULPS", "NVIDIA", "DNS", "Mouse: curvas", "Teclado", "USB", "Wi-Fi", "Defender: limitar"]
WEIGHT = {"Gaming": 3, "Kernel": 3, "Energía": 3, "Red": 2, "Periféricos": 2, "Servicios": 2, "Inicio": 2}
for i, t in enumerate(T, 1):
    t["id"] = f"ZT-{i:04d}"
    t["w"] = 3 if any(k in t["name"] for k in PRO_PICK) else WEIGHT.get(t["module"], 1)
    if t["risk"] == "extreme" or any(k in t["name"] for k in PRO_PICK): t["tier"] = "pro"
    elif any(k in t["name"] for k in FREE_PICK): t["tier"] = "free"
    else: t["tier"] = "free" if (i % 8) in (0, 3, 5) else "pro"

WARNS = [("Xbox", "Breaking", "Xbox, Game Pass y juegos de Microsoft Store pueden dejar de funcionar"),
         ("Windows Search", "Breaking", "Se pierde la búsqueda indexada de Windows"),
         ("Servicio Windows Update", "Breaking", "Impide actualizar Windows, Edge y Microsoft Store"),
         ("Windows Update automático", "Breaking", "Windows, Edge y Microsoft Store dejan de actualizarse solos"),
         ("hypervisor", "Breaking", "WSL, Docker, máquinas virtuales y Windows Sandbox dejan de funcionar"),
         ("VBS", "Seguridad", "Baja la protección del kernel contra malware"),
         ("HVCI", "Seguridad", "Baja la protección del kernel contra malware"),
         ("Defender", "Seguridad", "Menos protección contra virus y descargas peligrosas"),
         ("SmartScreen", "Seguridad", "Sin aviso ante programas y sitios peligrosos"),
         ("Spectre", "Seguridad", "Vulnerable a ataques de ejecución especulativa"),
         ("Quitar app", "Irreversible", "Para recuperarla hay que reinstalarla desde Microsoft Store"),
         ("curvas planas", "Beta", "Solo para escala de pantalla del 100%"),
         ("DSCP", "Beta", "Solo sirve si tu router respeta QoS"),
         ("Multiplane", "Beta", "Usalo solo si tenés stutter; en algunas GPU empeora"),
         ("Compresión de memoria", "Beta", "Pensado para 16 GB o más"),
         ("Kernel en RAM", "Beta", "Pensado para 16 GB o más"),
         ("NIC:", "Beta", "Puede afectar Wake-on-LAN y el ahorro de energía del adaptador"),
         ("Hibernación", "Info", "Quita la hibernación y el inicio rápido"),
         ("Plan de energía", "Energía", "Más consumo; en notebooks reduce la autonomía"),
         ("(plan ZyroTech)", "Energía", "Más consumo; en notebooks reduce la autonomía"),
         ("SysMain", "Beta", "Recomendado solo con SSD"),
         ("Sin tick dinámico", "Beta", "Puede subir consumo y temperatura"),
         ("MSI mode", "Beta", "Si aparecen fallas de video, revertir y reiniciar"),
         ("DNS ", "Info", "Cambia los servidores DNS de tus adaptadores")]
for t in T:
    t["badge"], t["warn"] = "", ""
    for k, b, w in WARNS:
        if k in t["name"]: t["badge"], t["warn"] = b, w; break
# Metadatos de solo lectura: permiten que Free detecte también el estado de
# los tweaks Pro sin incluir sus comandos de modificación en el ejecutable Free.
for t in T:
    checks = []
    for a in t["actions"]:
        if a["type"] == "reg":
            checks.append({"type": "reg", "path": a["path"], "name": a["name"],
                           "value": a["value"], "vtype": a["vtype"]})
            continue
        match = re.search(r"Disable-ScheduledTask\s+-TaskPath\s+'([^']+)'\s+-TaskName\s+'([^']+)'", a.get("cmd", ""), re.I)
        if match:
            checks.append({"type": "scheduled_task", "path": match.group(1),
                           "name": match.group(2), "state": "Disabled"})
        else:
            checks.append({"type": "unknown"})
    t["detect"] = checks

seen = collections.Counter()
for t in T:
    assert t["actions"], t["id"]
    for a in t["actions"]:
        if a["type"] == "reg":
            assert a["path"].startswith(("HKLM\\", "HKCU\\")), (t["id"], a["path"])
            seen[(a["path"].lower(), a["name"].lower())] += 1
        else:
            assert a["cmd"], t["id"]
            if t["mode"] == "track": assert "undo" in a, (t["id"], "ps sin undo")
            if "{captured}" in a.get("undo", ""): assert a.get("capture"), t["id"]
dups = [k for k, v in seen.items() if v > 1]
assert not dups, dups
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tweaks.json")
json.dump(T, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
mods = collections.Counter(t["module"] for t in T)
free = sum(t["tier"] == "free" for t in T)
wf=sum(t["w"] for t in T if t["tier"]=="free")*100//sum(t["w"] for t in T)
print(f"peso free={wf}%")
print(f"total={len(T)} free={free} ({free*100//len(T)}%) extreme={sum(t['risk']=='extreme' for t in T)} once={sum(t['mode']=='once' for t in T)}")
print(dict(mods))
