# ZyroTech: dos apps, Free y Pro (sin cuentas, sin web, sin servidor)

- `ZyroTech-Free.exe`: gratis. 93 optimizaciones desbloqueadas de 310, punto de restauración, historial, reversión, prueba de DNS, medidor de latencia. Lo de Pro se ve con candado.
- `ZyroTech-Pro.exe`: las optimizaciones del catálogo, perfiles Lite, Medio y Avanzado, Game Booster automático, timer 0.5 ms, limpiador de RAM, aplicar el DNS más rápido. Licencia atada a la PC.

## Interfaz y rendimiento
- Identidad visual tipográfica ZyroTech con monograma ZT, paleta grafito/verde para Free y grafito/cian para Pro.
- Barra superior, navegación lateral compacta, panel con contadores en vivo, hardware detectado y tarjetas de perfiles comparables.
- Interfaz sin fondos animados, vídeos, servicios web ni telemetría propia.
- El análisis corre en segundo plano para no congelar la ventana. La lectura de tareas programadas se agrupa en una única consulta por análisis.
- El Game Booster no purga automáticamente la memoria en espera y usa prioridad Above Normal temporal y reversible cuando corresponde.

## Perfiles y detección
- La aplicación detecta Windows, CPU, GPU, RAM, tipo de equipo, disco y conectividad para filtrar los cambios que no correspondan al hardware o versión del sistema.
- Free y Pro consultan el estado actual de los ajustes reversibles incluidos en la aplicación. Registro y tareas programadas se leen directamente; un estado que no se puede verificar queda como desconocido y no se incluye en los perfiles.
- Pro ofrece vista previa, selección individual y aplicación por lote. Lite es conservador; Medio amplía la selección; Avanzado propone los cambios reversibles compatibles del catálogo. Los cambios ya activos, incompatibles, no verificables, irreversibles o marcados como riesgosos se omiten.
- Ningún perfil garantiza una mejora de FPS. Los resultados dependen del equipo, Windows y las aplicaciones instaladas.

## Antes de distribuir
Editá `app/config.py` y completá `BUY_URL`, `CONTACT` y `PRICE_TEXT`. Hasta que lo hagas, el botón de compra informa que el canal comercial no está configurado y no abre enlaces de ejemplo.

## Compilación automática (sin instalar herramientas en tu PC)
1. El workflow `.github/workflows/build.yml` compila en una máquina Windows de GitHub Actions cuando se actualiza la rama `zyrotech-profiles-auto-detection`.
2. Abre la pestaña **Actions**, entra en el último workflow **Build ZyroTech** y descarga el artefacto `ZyroTech-Windows-x64`.
3. El ZIP del artefacto contiene `ZyroTech-Free.exe`. Pro se agrega automáticamente solo cuando `app/public_key.py` tiene la clave pública correspondiente a la clave privada del vendedor.
4. Para compilar localmente como alternativa, usá `build.bat` en Windows con Python 3.12 y las dependencias de `requirements-build.txt`.

**La compilación Free ya funciona en Actions.** El archivo público `app/public_key.py` está vacío en la fuente inspeccionada, por eso el workflow no fabrica una clave nueva ni compila Pro todavía. No corras `keygen.py init` si ya existe una clave privada usada para licencias: eso cambiaría el par de claves y puede invalidar las licencias anteriores.

La clave privada `tools/zyrotech_private.pem` debe quedarse solamente en tu equipo o en un almacén privado seguro; nunca subirla al repo, a un Release ni al ejecutable. La clave pública sí puede estar en GitHub.

Para habilitar Pro sin instalar Python ni cambiar las licencias anteriores, descargá el artefacto **ZyroTech-Developer-Tools** desde Actions y ejecutá `ZyroTech-KeyExport.exe`. Seleccioná tu archivo privado existente `tools/zyrotech_private.pem` y guardá el resultado como `app/public_key.py`. La utilidad deriva solo la clave pública; no modifica ni copia la privada. Subí únicamente `app/public_key.py`; nunca subas el PEM. El siguiente push compilará Free y Pro. No ejecutes `init` si ya emitiste licencias.
## Cómo vendés una licencia Pro
1. El cliente abre `ZyroTech-Pro.exe`: ve su **código de equipo** y lo copia. Se genera solo.
2. Te lo manda. Vos corrés: `python tools\keygen.py sign CODIGO-DEL-CLIENTE`. Te imprime la licencia (y anota el código en `tools/licencias_emitidas.csv`).
3. Se la mandás. La pega en la app, toca Activar y **queda guardada sola** (archivo + registro). No vuelve a pedirla.

## Cómo funciona el bloqueo por PC
- El código de equipo mezcla seis datos del hardware (CPU, placa, UUID, BIOS, disco, ID de Windows) e ignora valores genéricos de fábrica.
- La licencia está firmada (Ed25519) con tu clave privada: sin ella nadie puede fabricar licencias, ni siquiera con el .exe.
- Copiar el .exe y el archivo de licencia a otra PC no sirve: el equipo no coincide.
- Tolera cambiar 1 o 2 componentes (por ejemplo un disco nuevo). Si cambian la placa madre, te piden otro código y emitís otra licencia.
- Límite real: un usuario experto puede parchear el .exe (pasa con cualquier programa sin servidor). Frena el pasarse la app entre amigos, no a un cracker.

El modelo actual es una activación sin servidor con licencia firmada vinculada al equipo. Un ejecutable offline que no pide licencia no puede comprobar que la compra ocurrió ni bloquear una copia en otra PC. Para quitar el código de activación y seguir haciendo cumplir compras y dispositivos registrados, hace falta un servicio de licencias online. Por eso este proyecto conserva la activación firmada existente.

## Qué se arregló respecto de lo que molesta a los usuarios
Ver `replica/feedback.md` (con fuentes). Resumen: compatibilidad por hardware, etiquetas Breaking/Beta/Seguridad, punto de restauración obligatorio, reversión por tweak, historial, modo rescate, pago único.

## Si Windows queda mal
Modo seguro → ejecutá `ZyroTech-Free.exe --revert-all` como administrador, o usá Restaurar sistema (queda un punto "ZyroTech - antes de optimizar").

## Límites que tenés que saber
- **La compilación y los cambios de registro/PowerShell deben verificarse en Windows.** GitHub Actions compila Free; Pro requiere que `app/public_key.py` contenga la clave pública del vendedor que corresponda a su clave privada.
- La "cobertura" del Panel mide cuántos cambios compatibles aplicaste; no promete FPS. Varios tweaks son marginales y dependen del equipo.
- No vi la interfaz de EXM Tweaks ni de voltX. Usé el patrón común de estas apps (menú lateral, categorías, interruptores, avisos) con diseño, nombre, colores y textos propios; no copié su código, logos ni textos.
- El .exe sin firmar muestra SmartScreen y puede dar falso positivo en antivirus (PyInstaller + cambios de registro).
- `ZyroTech-Pro.exe` necesita administrador, igual que Free.
- Opción GitHub Actions (`.github/workflows/build.yml`): corré `python tools\keygen.py init` en tu PC, subí `app/public_key.py` (es pública) y ejecutá el workflow desde la pestaña Actions.
