# ZyroTech Free

**Diagnóstico y ajustes locales de Windows.** Este repositorio público distribuye exclusivamente la edición gratuita.

<details>
<summary><strong>Descarga directa</strong></summary>

- **[Descargar la última versión desde Releases](https://github.com/bautistacasero265-maker/zyrotechc/releases/latest)**
- En cada Release vas a encontrar el EXE y el ZIP portable para Windows x64.

</details>

## Qué incluye

- Detección de CPU, GPU, RAM, unidad de almacenamiento, formato del equipo y versión de Windows.
- Catálogo Free con 93 ajustes, agrupados por módulos y con una explicación clara de qué hace cada uno.
- Lectura del estado actual para distinguir ajustes activos, pendientes, parciales, incompatibles y no verificables; incluye detección de tareas programadas, configuración de Teredo, plan de energía y telemetría de PowerShell.
- Clasificación de riesgo normal, precaución y riesgo alto, con advertencias antes de aplicar cambios delicados o acciones puntuales.
- Recomendaciones prudentes: selecciona solo ajustes compatibles, reversibles, verificables y de impacto acotado; nunca aplica cambios automáticamente.
- Aplicación de un ajuste por vez.
- Exportación de un informe de diagnóstico en texto con hardware detectado, compatibilidad y estado de cada ajuste; no incluye rutas personales ni datos del registro.
- Punto de restauración, respaldo del registro, historial y reversión cuando el cambio tiene una acción inversa.
- Diagnóstico de respuesta DNS y medición de temporización, sin prometer mejoras de FPS ni cambiar automáticamente la red.

## Interfaz

ZyroTech Free utiliza una identidad **Premium Gaming**: superficies oscuras de tono violeta, acento púrpura, detalles cian y estados semánticos de alto contraste. La navegación lateral permanece visible y cada pantalla comparte la misma jerarquía tipográfica, espaciado, tarjetas y botones.

- Dashboard con presentación del producto, estado verificado de ajustes, resumen de hardware, acciones rápidas y consejos de uso.
- Catálogo con categorías, búsqueda, recomendaciones, estados compatibles/no verificables y tarjetas de ajuste reorganizadas para mantener la lectura.
- Actividad con cambios administrados, acciones individuales de reversión e historial reciente.
- Diagnóstico DNS y pantalla Acerca de con componentes consistentes.
- Reflujo del dashboard entre cuatro y dos columnas, y redistribución de los paneles principales al estrechar la ventana.
- Las categorías actualizan el contenido sin reconstruir la pantalla ni perder búsqueda, switches o confirmaciones.

El análisis del equipo y de los ajustes corre en un hilo separado para evitar bloquear la interfaz. La cobertura informa ajustes comprobados y no representa una puntuación de rendimiento ni una promesa de FPS.

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
