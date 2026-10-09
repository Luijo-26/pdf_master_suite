# PDF Master Suite — Gestor Integral de Documentos

Aplicación de escritorio nativa para Windows con interfaz gráfica moderna, fluida y en **modo oscuro**, construida con **Python** y **PySide6 (Qt)**. Proporciona un conjunto de herramientas locales estilo *I Love PDF* completamente privadas, sin límites de tamaño de archivo y sin enviar datos a internet.

---

## Características y Rediseño

- **Arquitectura fluida con Qt (PySide6):** Renderizado acelerado, micro-animaciones suaves, sin parpadeos de lista ni bloqueos de ventana.
- **Arrastrar y soltar nativo (Drag & Drop):** Arrastra archivos PDF, imágenes o documentos Word directamente desde el Explorador de Windows a cualquier pantalla.
- **Modo oscuro premium:** Paleta seleccionada (#0E0F14 / #16181F), tarjetas con bordes suaves, iconos vectoriales dinámicos y tipografía nativa Segoe UI.
- **Miniaturas reales de páginas (QtPdf):** En *Organizar y Rotar páginas*, visualiza cada página como una miniatura nítida con rotación en tiempo real (+90°, -90°, 180°), eliminación y selección múltiple.
- **Control total de guardado (Guardar como...):** Diálogos nativos para elegir siempre la carpeta de destino y el nombre final con sugerencias inteligentes.
- **Notificaciones no bloqueantes (Toasts):** Mensajes emergentes con accesos directos a "Abrir archivo" y "Mostrar en carpeta" en el Explorador de Windows.
- **Auto-actualización directa y notificaciones (GitHub Releases):** Detección automática en segundo plano de nuevas versiones, ventana emergente modal con changelog interactivo, descarga asistida con barra de progreso y sustitución en caliente (hot-swap) para el ejecutable de Windows.
- **Dashboard de inicio:** Pantalla principal interactiva con tarjetas de acceso rápido, soltado universal que detecta el formato y lista de documentos recientes.
- **Procesamiento multihilo (QThreadPool):** Tareas pesadas ejecutadas en segundo plano con indicadores de progreso reactivos.

---

## Módulos y Herramientas

1. **Unir PDFs (Merge):**
   - Selección múltiple de archivos con Drag & Drop.
   - Lista interactiva reordenable con botones rápidos (▲, ▼, ✕), ordenamiento alfabético e inversión.
   - Exportación de un único archivo PDF unificado mediante `pypdf`.

2. **Dividir PDF (Split):**
   - Detección automática del número total de páginas.
   - **Por rangos:** Extrae páginas o intervalos específicos (ejemplo: `1-3, 5, 8-10`) con **validación en vivo** de la sintaxis y páginas existentes.
   - **Todas las páginas:** Separa cada página en archivos individuales en la carpeta seleccionada.

3. **Organizar y Rotar Páginas:**
   - Cuadrícula visual interactiva con miniaturas de alta definición renderizadas mediante `PySide6.QtPdf`.
   - Rotación precisa en ángulos de **+90°**, **-90°** y **180°** por página o en bloque.
   - Eliminación de páginas innecesarias y reordenamiento antes de exportar.

4. **Comprimir PDF (Compress):**
   - Reducción del peso del archivo eliminando metadatos redundantes, recomprimiendo flujos de contenido de cada página y removiendo objetos duplicados.
   - Panel de estadísticas visuales: tamaño original, tamaño final y porcentaje de reducción obtenido.

5. **Imágenes a PDF (JPG/PNG/WEBP/BMP):**
   - Selección múltiple de imágenes en formatos habituales.
   - Reordenamiento interactivo en lista para definir la secuencia de páginas.
   - Normalización a RGB, soporte de transparencia y corrección de orientación EXIF mediante `Pillow`.

6. **Convertir Word (.docx) a PDF (Individual y Lotes):**
   - Conversión local de alta fidelidad mediante la API COM nativa de Office en Windows con `docx2pdf`.
   - Soporte para procesar múltiples documentos Word a la vez con barra de progreso en vivo.
   - Opción para guardar junto al archivo original o consolidar en una carpeta elegida.

7. **Seguridad (Proteger / Desbloquear con Cifrado AES):**
   - **Proteger:** Cifrado con contraseña bajo algoritmos bancarios robustos: `AES-256` (máxima seguridad) o `AES-128`. Incluye medidor de fortaleza de contraseña y alternancia de visibilidad.
   - **Desbloquear:** Detección automática del estado del archivo y remoción permanente de la clave tras ingresar la contraseña correcta.

---

## Atajos de Teclado Globales

| Atajo | Acción |
|---|---|
| `Ctrl + H` | Ir a la pantalla de Inicio |
| `Ctrl + 1` | Unir PDFs |
| `Ctrl + 2` | Dividir PDF |
| `Ctrl + 3` | Organizar y Rotar páginas |
| `Ctrl + 4` | Comprimir PDF |
| `Ctrl + 5` | Imágenes a PDF |
| `Ctrl + 6` | Word a PDF |
| `Ctrl + 7` | Seguridad de PDF |
| `Ctrl + Enter` | Ejecutar acción principal ("Guardar como...") en la herramienta activa |

---

## Estructura del Proyecto

```text
├── main.py                  # Arranque de la aplicación y ciclo de vida Qt
├── pdf_tools.py             # Lógica pura de manipulación de archivos (sin GUI)
├── requirements.txt         # Dependencias (PySide6, pypdf, Pillow, docx2pdf, etc.)
├── build.bat                # Script de compilación a ejecutable (.exe)
├── core/
│   ├── version.py           # Metadatos de versión y parser semántico
│   └── updater.py           # Comprobación de API GitHub, descarga y hot-swap Windows
├── ui/
│   ├── app.py               # Ventana principal (QMainWindow, router y atajos)
│   ├── theme.py             # Sistema de diseño, paleta oscura y QSS global
│   ├── icons.py             # Iconos vectoriales SVG embebidos y logotipo
│   ├── worker.py            # Ejecución en segundo plano con QThreadPool
│   ├── recents.py           # Gestor de historial de archivos recientes
│   ├── components/
│   │   ├── sidebar.py       # Menú lateral categorizado con verificador
│   │   ├── update_dialog.py # Diálogo modal emergente de actualización
│   │   ├── drop_zone.py     # Zona de arrastrar y soltar nativa
│   │   ├── file_list.py     # Lista de archivos interactiva reordenable
│   │   ├── page_grid.py     # Cuadrícula de miniaturas reales (QtPdf)
│   │   ├── action_bar.py    # Barra de acción inferior sticky
│   │   └── toast.py         # Notificaciones flotantes animadas
│   └── views/
│       ├── base_tool.py     # Estructura base de herramientas
│       ├── home.py          # Dashboard de bienvenida
│       ├── merge.py         # Vista Unir PDFs
│       ├── split.py         # Vista Dividir PDF
│       ├── organize.py      # Vista Organizar páginas
│       ├── compress.py      # Vista Comprimir PDF
│       ├── images.py        # Vista Imágenes a PDF
│       ├── word.py          # Vista Word a PDF
│       └── security.py      # Vista Seguridad de PDF
└── README.md
```

---

## Instalación y Ejecución

### 1. Requisitos
- Python 3.10 o superior instalado en Windows.
- Microsoft Word instalado (requerido únicamente para la conversión de Word `.docx` a `.pdf`).

### 2. Instalación de dependencias
```powershell
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```powershell
python main.py
```

---

## Compilación a Ejecutable Único (.exe)

Para generar el ejecutable autónomo para Windows:

1. Ejecuta el archivo [`build.bat`](file:///c:/Users/luisj/OneDrive%20-%20uniminuto.edu/ISUM(materias-documentos-certificados)/Materias/Programacion%20Web/PDF/build.bat).
2. El archivo `.exe` se generará en la carpeta `dist\PDFMasterSuite.exe`.
