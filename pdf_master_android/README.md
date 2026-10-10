# PDF Master Suite — Aplicación Android Nativa v2.2.0

Versión nativa para **Android** de **PDF Master Suite**, construida en **Kotlin** con **Jetpack Compose (Material 3)**, arquitectura reactiva **MVVM**, asincronía con **Coroutines** y procesamiento local de alto rendimiento mediante **PdfBox-Android** y el **PdfRenderer nativo de Android**.

La versión **2.2.0** incorpora una **interfaz fluida**, barra de búsqueda interactiva en tiempo real, chips de categorías y un conjunto completo de **13 herramientas locales** estilo *iLovePDF*.

---

## 🚀 Cómo abrir y ejecutar el proyecto en Android Studio

### Paso 1: Abrir el proyecto
1. Abre **Android Studio** (versión Hedgehog, Iguana, Jellyfish, Koala, Ladybug o superior).
2. En la pantalla de bienvenida o en el menú superior, ve a:
   **File > Open...** (o *Open Project*).
3. Busca la carpeta donde está guardado este proyecto y selecciona:
   `PDF/pdf_master_android`
4. Haz clic en **OK**.

### Paso 2: Sincronización de Gradle
- Android Studio comenzará a sincronizar el proyecto automáticamente (*Gradle Sync*).
- Descargará las librerías necesarias (`Jetpack Compose`, `PdfBox-Android`, etc.).
- En la barra inferior verás *Gradle Build: Finished in ...*.

### Paso 3: Ejecutar en tu Celular o Emulador
1. Conecta tu celular Android por cable USB (asegúrate de tener activada la **Depuración por USB** en las *Opciones de desarrollador*) **O** inicia un Emulador desde el *Device Manager* de Android Studio.
2. En la barra superior de Android Studio, asegúrate de que esté seleccionado el módulo `app` y tu dispositivo.
3. Presiona el botón verde de **Run (▶)** o el atajo `Shift + F10`.
4. ¡La aplicación se instalará y abrirá en tu dispositivo!

---

## 📱 Catálogo de Herramientas Implementadas (13 Herramientas)

### 📂 Organizar
1. **Unir PDFs (Merge):** Combina múltiples archivos PDF en el orden exacto deseado mediante Storage Access Framework.
2. **Dividir PDF (Split):** Extrae páginas individuales o por rangos numéricos como `1-3, 5, 8-10`.
3. **Organizar Páginas (Visual Grid):** Renderizado en alta definición de miniaturas reales con `PdfRenderer`, rotación por página y descarte visual.
4. **Rotar en Bloque:** Giro rápido a +90°, -90° o 180° aplicado a todas las páginas, solo páginas pares o impares.

### ✍️ Editar
5. **Firmar PDF (Lienzo Táctil):** Lienzo fluido para firmar con dedo o stylus con tinta ejecutiva, selección de página y posición.
6. **Marca de Agua:** Estampa textos o logos de imagen con transparencia regulable (10% - 90%), ángulo diagonal o posición fija.
7. **Numerar Páginas:** Inserta folios correlativos (`Pág. X`, `X de Y`, `- X -`), posición personalizable y omisión de portada.
8. **Recortar PDF:** Ajuste y recorte de márgenes externos en milímetros (preajustes sutil, estándar o amplio).

### 🔄 Convertir
9. **Imágenes a PDF:** Convierte fotos JPG, PNG o WEBP en un documento ordenado con muestreo inteligente anti-OOM.
10. **PDF a Imágenes:** Exporta páginas a JPG o PNG en calidad estándar, alta o ultra, con empaquetado automático en archivo ZIP para documentos de varias páginas.
11. **PDF a Texto (.txt):** Extracción de texto indexable con contador de palabras y caracteres, copia al portapapeles y exportación `.txt`.

### 🔒 Seguridad & Rendimiento
12. **Comprimir PDF:** Optimización de estructuras y flujos redundantes sin alterar la legibilidad ni la calidad.
13. **Seguridad (Proteger / Desbloquear):** Cifrado seguro **AES-256** y **AES-128**, y remoción permanente de contraseñas.

---

## 🎨 Experiencia de Usuario e Interfaz Fluida

- **Búsqueda en Tiempo Real:** Barra de búsqueda integrada en la pantalla principal que filtra las 13 herramientas instantáneamente según tecleas (*"firmar"*, *"texto"*, *"rotar"*).
- **Filtro por Categorías:** Chips interactivos (`Todos`, `Organizar`, `Editar`, `Convertir`, `Seguridad`).
- **Lienzo de Firma Táctil:** Dibujo reactivo suave con trazado Bézier y exportación a mapa de bits transparente.
- **Detección Automática de Actualizaciones:** Comprobación en segundo plano contra GitHub Releases con banner emergente y botón manual de sincronización para descargar la última versión sin perder tus datos.
- **Modo Oscuro Puro:** Paleta armónica moderna (`#0E0F14`, `#16181F`, `#1C1E27`) con acentos vibrantes Indigo, Cyan, Púrpura y Esmeralda.
- **100% Local y Seguro:** Todo el procesamiento de tus PDFs se ejecuta exclusivamente en el dispositivo sin enviar información a ningún servidor.
