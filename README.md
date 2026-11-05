# ZyroTech Free

**Diagnóstico y ajustes locales de Windows.** Este repositorio público distribuye exclusivamente la edición gratuita.

<details>
<summary><strong>Descarga directa</strong></summary>

- **[Descargar la última versión desde Releases](https://github.com/bautistacasero265-maker/zyrotechc/releases/latest)**
- En cada Release vas a encontrar el EXE y el ZIP portable para Windows x64.

</details>

## Qué incluye

- Detección de CPU, GPU, RAM, unidad de almacenamiento, formato del equipo y versión de Windows.
- Catálogo Free con 93 ajustes, agrupados por módulos.
- Lectura del estado actual para distinguir ajustes activos, pendientes, parciales, incompatibles y no verificables.
- Recomendaciones conservadoras: evita proponer cambios ya activos, irreversibles, marcados como riesgosos o que no correspondan al equipo.
- Aplicación de un ajuste por vez.
- Punto de restauración, respaldo del registro, historial y reversión cuando el cambio tiene una acción inversa.
- Diagnóstico de respuesta DNS y medición de temporización, sin prometer mejoras de FPS ni cambiar automáticamente la red.

## Interfaz

ZyroTech Free utiliza una interfaz oscura de alto contraste con acentos cian, violeta y lima, navegación lateral persistente, dashboard de diagnóstico, categorías con contadores y tarjetas de ajustes con estados visibles. Cambiar de sección o categoría no reinicia la selección de ajustes; la búsqueda y las confirmaciones se conservan al navegar. El análisis del equipo y de los ajustes corre en un hilo separado para evitar bloquear la interfaz.

## Releases y compilación automática

Cada actualización de `main` que afecte a la aplicación o al proceso de build ejecuta las pruebas y compila en una máquina Windows de GitHub Actions. Cuando el build termina correctamente, publica una Release con el EXE y el ZIP descargables desde la pestaña **Releases**.

Los artefactos temporales de Actions caducan; las Releases permanecen disponibles hasta que se eliminen.

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
