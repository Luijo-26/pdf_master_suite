# PDF Master Suite - Gestor Integral de Documentos

Aplicación de escritorio nativa para Windows con interfaz gráfica moderna en modo oscuro, construida con **Python** y **CustomTkinter**. Proporciona un conjunto de herramientas locales estilo *I Love PDF* completamente privadas, sin límites de tamaño de archivo y sin enviar datos a la nube.

---

## Módulos y Funcionalidades

1. **Unir PDFs (Merge):**
   - Selección múltiple de archivos PDF.
   - Lista interactiva para visualizar y reordenar con botones (Subir, Bajar, Eliminar, Limpiar).
   - Exportación de un único archivo PDF unificado mediante `pypdf`.

2. **Dividir PDF (Split):**
   - Detección automática del número total de páginas.
   - **Por rangos:** Extrae páginas o intervalos específicos (ejemplo: `1-3, 5, 8-10`) en un solo PDF.
   - **Todas las páginas:** Extrae cada página en archivos individuales (`documento_pagina_001.pdf`, etc.) en una carpeta destino.

3. **Organizar y Rotar Páginas:**
   - Visualización secuencial de las páginas de un documento.
   - Rotación precisa en ángulos de **+90°**, **-90°** y **180°**.
   - Reordenamiento del orden de las páginas y eliminación de páginas no deseadas antes de exportar.

4. **Comprimir PDF (Compress):**
   - Reducción del peso del archivo eliminando metadatos redundantes, removiendo objetos duplicados/huérfanos (`compress_identical_objects`) y recomprimiendo los flujos de contenido de cada página (`compress_content_streams`).
   - Muestra el tamaño original, tamaño final y porcentaje exacto de reducción obtenido.

5. **Imágenes a PDF (JPG/PNG/WEBP/BMP):**
   - Selección múltiple de imágenes en formatos habituales.
   - Reordenamiento interactivo en lista para definir la secuencia de páginas.
   - Normalización a RGB, soporte de transparencia y corrección de orientación EXIF mediante `Pillow`.

6. **Convertir Word (.docx) a PDF (Individual y Lotes):**
   - Conversión local de alta fidelidad mediante la API COM nativa de Office en Windows con `docx2pdf`.
   - Soporte para **seleccionar múltiples documentos Word a la vez**.
   - Opción para guardar en la misma carpeta de cada archivo original o consolidar los PDFs en una carpeta destino seleccionada.
   - Indicador de progreso por archivo en tiempo real.

7. **Seguridad (Proteger / Desproteger con Cifrado AES):**
   - **Proteger:** Cifrado con contraseña bajo algoritmos bancarios robustos: `AES-256` (máxima seguridad recomendada) o `AES-128`.
   - **Desproteger:** Detección de archivos encriptados y remoción permanente de la contraseña una vez ingresada la clave correcta.

8. **Rendimiento y Multihilo:**
   - Todas las tareas pesadas de procesamiento de archivos se ejecutan en segundo plano (`threading.Thread`), garantizando que la ventana nunca se congele ni muestre "No responde".
   - Barra de estado reactiva con códigos de color e indicador de progreso.

---

## Estructura del Proyecto

```text
├── main.py            # Interfaz gráfica moderna (CustomTkinter), control de eventos y multihilo
├── pdf_tools.py       # Módulo con la lógica pura de manipulación de archivos (sin GUI)
├── requirements.txt   # Lista de dependencias del proyecto (pypdf, Pillow, cryptography, docx2pdf, etc.)
├── build.bat          # Script de compilación automática para generar el .exe en Windows
└── README.md          # Manual del proyecto
```

---

## Instalación y Uso Local

### 1. Requisitos Previos
- Python 3.10 o superior instalado en Windows.
- Microsoft Word instalado (requerido únicamente para la conversión de Word `.docx` a `.pdf`).

### 2. Instalación de Dependencias
```powershell
pip install -r requirements.txt
```

### 3. Ejecutar la Aplicación
```powershell
python main.py
```

---

## Compilación a Ejecutable Único (.exe)

Para generar un ejecutable `.exe` independiente, sin consola y con todos los recursos embebidos:

```powershell
python -m PyInstaller --onefile --noconsole --collect-all customtkinter --name "PDFMasterSuite" main.py
```

> **Nota:** También puedes compilar con un solo clic ejecutando el archivo [**`build.bat`**](file:///c:/Users/luisj/OneDrive%20-%20uniminuto.edu/ISUM(materias-documentos-certificados)/Materias/Programacion%20Web/PDF/build.bat). El ejecutable generado estará disponible en la carpeta `dist\PDFMasterSuite.exe`.
