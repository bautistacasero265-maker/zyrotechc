# ZyroTech Free

**Diagnóstico y ajustes locales de Windows.** Esta rama pública contiene exclusivamente la edición gratuita.

## Qué incluye

- Detección de CPU, GPU, RAM, unidad de almacenamiento, formato del equipo y versión de Windows.
- Catálogo Free con 93 ajustes, agrupados por módulos.
- Lectura del estado actual para distinguir ajustes activos, pendientes, parciales, incompatibles y no verificables.
- Recomendaciones conservadoras: evita proponer cambios ya activos, irreversibles, marcados como riesgosos o que no correspondan al equipo.
- Aplicación de un ajuste por vez.
- Punto de restauración, respaldo del registro, historial y reversión cuando el cambio tiene una acción inversa.
- Diagnóstico de respuesta DNS y medición de temporización, sin prometer mejoras de FPS ni cambiar automáticamente la red.

## Interfaz

ZyroTech Free utiliza una ventana ligera con navegación horizontal, panel de diagnóstico, métricas verificables y vistas desplazables. El análisis del equipo y de los ajustes corre en un hilo separado para evitar bloquear la interfaz.

## Compilar sin instalar Python en tu PC

El repositorio incluye un workflow de GitHub Actions:

1. Abrí la pestaña **Actions** del repositorio.
2. Entrá a **Build ZyroTech Free**.
3. Descargá el artefacto **ZyroTech-Free-Windows-x64** del último build exitoso.
4. Extraé el ZIP y ejecutá `ZyroTech-Free.exe` como administrador para aplicar cambios del sistema.

GitHub compila el ejecutable en una máquina Windows hospedada. El artefacto de Actions tiene retención limitada; guardá una copia del ZIP que descargues.

## Compilación local opcional

En Windows con Python 3.12:

```bat
python -m pip install -r requirements-build.txt
python tools/build.py
```

El ejecutable se genera en `dist/ZyroTech-Free.exe`.

## Seguridad y límites

- Revisá cada cambio antes de aplicarlo. Un ajuste de registro no garantiza más FPS.
- Los cambios irreversibles o sin una reversión definida no se incluyen en recomendaciones automáticas.
- Un estado no verificable se muestra como desconocido y no se recomienda para aplicar.
- Los cambios que lo requieran pueden necesitar reiniciar Windows.
- ZyroTech no sustituye un respaldo personal ni una prueba en un equipo de laboratorio.

## Privacidad

El diagnóstico y la aplicación de ajustes se realizan localmente. Esta edición no contiene activación, sistema de licencias ni comprobación de compras.
