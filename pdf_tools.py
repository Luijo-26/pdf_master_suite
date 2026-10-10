"""
pdf_tools.py
Módulo de lógica pura para manipulación de documentos PDF, imágenes y conversión de Word a PDF.
No contiene dependencias de interfaz gráfica (GUI), permitiendo pruebas automatizadas y ejecución limpia.
"""

import os
import io
import math
import gc
from typing import List, Dict, Any, Optional, Tuple, Callable
from pypdf import PdfReader, PdfWriter
from PIL import Image, ImageOps


class PDFToolError(Exception):
    """Excepción base para errores en las herramientas de documentos."""
    pass


# -----------------------------------------------------------------------------
# INFORMACIÓN Y CONSULTA
# -----------------------------------------------------------------------------
def get_pdf_page_count(pdf_path: str) -> int:
    """
    Obtiene el número total de páginas de un archivo PDF.
    
    :param pdf_path: Ruta al archivo PDF.
    :return: Número total de páginas.
    :raises PDFToolError: Si el archivo no existe o no es un PDF legible.
    """
    if not os.path.exists(pdf_path):
        raise PDFToolError(f"El archivo no existe: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            raise PDFToolError("El archivo PDF está protegido con contraseña. Desprotégelo primero.")
        return len(reader.pages)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"No se pudo leer el archivo PDF: {str(e)}")


def is_pdf_encrypted(pdf_path: str) -> bool:
    """Verifica si un archivo PDF está protegido con contraseña."""
    if not os.path.exists(pdf_path):
        raise PDFToolError(f"El archivo no existe: {pdf_path}")
    try:
        reader = PdfReader(pdf_path)
        return bool(reader.is_encrypted)
    except Exception as e:
        raise PDFToolError(f"Error al verificar protección del PDF: {str(e)}")


# -----------------------------------------------------------------------------
# 1. UNIR PDFs (MERGE)
# -----------------------------------------------------------------------------
def merge_pdfs(pdf_paths: List[str], output_path: str) -> None:
    """
    Combina múltiples archivos PDF en un único archivo de salida.
    
    :param pdf_paths: Lista ordenada de rutas a los archivos PDF de entrada.
    :param output_path: Ruta destino donde se guardará el PDF resultante.
    :raises PDFToolError: Si ocurre un error durante el proceso de unión.
    """
    if not pdf_paths:
        raise PDFToolError("La lista de archivos para unir está vacía.")
    
    if len(pdf_paths) < 2:
        raise PDFToolError("Se necesitan al menos 2 archivos PDF para unir.")
    
    writer = PdfWriter()
    
    try:
        for path in pdf_paths:
            if not os.path.exists(path):
                raise PDFToolError(f"El archivo no existe: {path}")
            reader = PdfReader(path)
            if reader.is_encrypted:
                raise PDFToolError(f"El archivo '{os.path.basename(path)}' está protegido con contraseña. Desprotégelo primero.")
            for page in reader.pages:
                writer.add_page(page)
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al unir los PDFs: {str(e)}")


# -----------------------------------------------------------------------------
# 2. DIVIDIR PDF (SPLIT)
# -----------------------------------------------------------------------------
def parse_page_ranges(range_str: str, total_pages: int) -> List[int]:
    """
    Parsea una cadena de rangos de páginas (1-indexada) a una lista de índices (0-indexados).
    Ejemplos de entrada: "1-3, 5, 8-10"
    """
    if not range_str or not range_str.strip():
        raise PDFToolError("El rango de páginas no puede estar vacío.")
    
    selected_indices: List[int] = []
    chunks = [c.strip() for c in range_str.split(",") if c.strip()]
    
    if not chunks:
        raise PDFToolError("No se especificaron rangos válidos.")
    
    for chunk in chunks:
        if "-" in chunk:
            parts = chunk.split("-")
            if len(parts) != 2:
                raise PDFToolError(f"Sintaxis de rango inválida: '{chunk}'. Use el formato 'inicio-fin'.")
            start_str, end_str = parts[0].strip(), parts[1].strip()
            
            if not start_str.isdigit() or not end_str.isdigit():
                raise PDFToolError(f"Rango numérico inválido en '{chunk}'. Solo se permiten enteros positivos.")
            
            start, end = int(start_str), int(end_str)
            if start > end:
                raise PDFToolError(f"Rango inválido '{chunk}': la página inicial ({start}) es mayor que la final ({end}).")
            if start < 1:
                raise PDFToolError(f"Número de página inválido: {start}. Las páginas inician en 1.")
            if end > total_pages:
                raise PDFToolError(f"Página fuera de rango: {end}. El documento solo tiene {total_pages} página(s).")
            
            for p in range(start, end + 1):
                idx = p - 1
                if idx not in selected_indices:
                    selected_indices.append(idx)
        else:
            if not chunk.isdigit():
                raise PDFToolError(f"Valor no numérico en especificación de páginas: '{chunk}'")
            val = int(chunk)
            if val < 1:
                raise PDFToolError(f"Número de página inválido: {val}. Las páginas inician en 1.")
            if val > total_pages:
                raise PDFToolError(f"Página fuera de rango: {val}. El documento solo tiene {total_pages} página(s).")
            
            idx = val - 1
            if idx not in selected_indices:
                selected_indices.append(idx)
                
    if not selected_indices:
        raise PDFToolError("No se seleccionaron páginas válidas.")
        
    return selected_indices


def split_pdf_ranges(input_path: str, range_str: str, output_path: str) -> int:
    """Extrae las páginas especificadas por la cadena de rangos y las guarda en un nuevo PDF."""
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo original no existe: {input_path}")
        
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El documento está protegido con contraseña. Desprotégelo primero.")
            
        total_pages = len(reader.pages)
        indices = parse_page_ranges(range_str, total_pages)
        
        writer = PdfWriter()
        for idx in indices:
            writer.add_page(reader.pages[idx])
            
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            
        return len(indices)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al dividir el PDF por rangos: {str(e)}")


def split_pdf_all(input_path: str, output_folder: str, prefix: str = "pagina") -> List[str]:
    """Extrae cada una de las páginas del PDF como archivos individuales en la carpeta destino."""
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo original no existe: {input_path}")
        
    if not os.path.exists(output_folder):
        try:
            os.makedirs(output_folder, exist_ok=True)
        except Exception as e:
            raise PDFToolError(f"No se pudo crear la carpeta de destino: {str(e)}")
            
    created_files: List[str] = []
    
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El archivo está protegido con contraseña. Desprotégelo primero.")
            
        total_pages = len(reader.pages)
        digits = max(3, len(str(total_pages)))
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        for i, page in enumerate(reader.pages):
            writer = PdfWriter()
            writer.add_page(page)
            
            filename = f"{base_name}_{prefix}_{i + 1:0{digits}d}.pdf"
            file_path = os.path.join(output_folder, filename)
            
            with open(file_path, "wb") as f_out:
                writer.write(f_out)
                
            created_files.append(file_path)
            
        return created_files
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al extraer todas las páginas: {str(e)}")


# -----------------------------------------------------------------------------
# 3. ORGANIZAR Y ROTAR PÁGINAS
# -----------------------------------------------------------------------------
def reorganize_pdf(input_path: str, pages_config: List[Dict[str, Any]], output_path: str) -> int:
    """Reorganiza y rota las páginas de un PDF según una configuración específica."""
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo no existe: {input_path}")
        
    if not pages_config:
        raise PDFToolError("No se especificaron páginas para el documento final.")
        
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El archivo está protegido con contraseña. Desprotégelo primero.")
            
        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        for item in pages_config:
            orig_idx = item.get("original_index")
            rotation = item.get("rotation", 0) % 360
            
            if orig_idx is None or orig_idx < 0 or orig_idx >= total_pages:
                raise PDFToolError(f"Índice de página inválido: {orig_idx}")
                
            page = reader.pages[orig_idx]
            if rotation != 0:
                page.rotate(rotation)
                
            writer.add_page(page)
            
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            
        return len(pages_config)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al reorganizar/rotar páginas del PDF: {str(e)}")


# -----------------------------------------------------------------------------
# 4. COMPRIMIR PDF (COMPRESS)
# -----------------------------------------------------------------------------
def compress_pdf(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Comprime un PDF eliminando metadatos redundantes, recomprimiendo flujos
    de contenido y eliminando objetos duplicados/huérfanos.
    
    :return: Diccionario con estadísticas de tamaño (original, nuevo, porcentaje de ahorro).
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo no existe: {input_path}")

    try:
        original_size = os.path.getsize(input_path)
        reader = PdfReader(input_path)
        
        if reader.is_encrypted:
            raise PDFToolError("El archivo está protegido con contraseña. Desprotégelo antes de comprimirlo.")

        writer = PdfWriter()
        
        for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

        # Eliminar objetos idénticos y huérfanos
        writer.compress_identical_objects(remove_identicals=True, remove_orphans=True)

        # Limpiar metadatos redundantes
        writer.add_metadata({})

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "wb") as f_out:
            writer.write(f_out)

        compressed_size = os.path.getsize(output_path)
        savings = max(0, original_size - compressed_size)
        pct = (savings / original_size * 100) if original_size > 0 else 0.0

        return {
            "original_size": original_size,
            "compressed_size": compressed_size,
            "saved_bytes": savings,
            "reduction_percent": round(pct, 2)
        }
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al comprimir el archivo PDF: {str(e)}")


# -----------------------------------------------------------------------------
# 5. IMÁGENES A PDF (JPG/PNG -> PDF)
# -----------------------------------------------------------------------------
def images_to_pdf(image_paths: List[str], output_path: str) -> int:
    """
    Convierte y compila una lista ordenada de imágenes en un único archivo PDF.
    Ajusta la orientación EXIF y normaliza a RGB con fondo blanco para transparencias.
    
    :param image_paths: Lista ordenada de rutas a imágenes.
    :param output_path: Ruta del PDF destino.
    :return: Número de imágenes compiladas.
    """
    if not image_paths:
        raise PDFToolError("No se proporcionó ninguna imagen para compilar a PDF.")

    pil_images: List[Image.Image] = []

    try:
        for img_path in image_paths:
            if not os.path.exists(img_path):
                raise PDFToolError(f"La imagen no existe: {img_path}")

            raw_img = Image.open(img_path)
            # Corregir orientación según metadata EXIF si proviene de cámara/móvil
            oriented_img = ImageOps.exif_transpose(raw_img)

            # Normalizar espacio de color a RGB (el formato PDF requiere RGB para guardar con Pillow)
            if oriented_img.mode in ("RGBA", "LA") or (oriented_img.mode == "P" and "transparency" in oriented_img.info):
                oriented_img = oriented_img.convert("RGBA")
                background = Image.new("RGB", oriented_img.size, (255, 255, 255))
                background.paste(oriented_img, mask=oriented_img.split()[-1])
                rgb_img = background
            else:
                rgb_img = oriented_img.convert("RGB")

            pil_images.append(rgb_img)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        first_image = pil_images[0]
        other_images = pil_images[1:] if len(pil_images) > 1 else []

        first_image.save(
            output_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=other_images
        )

        return len(pil_images)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al compilar imágenes a PDF: {str(e)}")
    finally:
        # Cerrar manejadores de imágenes en memoria
        for im in pil_images:
            try:
                im.close()
            except Exception:
                pass


# -----------------------------------------------------------------------------
# 6. SEGURIDAD: PROTEGER Y DESPROTEGER PDF (AES-128 / AES-256)
# -----------------------------------------------------------------------------
def encrypt_pdf(input_path: str, output_path: str, password: str, algorithm: str = "AES-256") -> None:
    """
    Protege un PDF con contraseña utilizando cifrado AES-256 o AES-128.
    
    :param input_path: Ruta al PDF original.
    :param output_path: Ruta destino del PDF protegido.
    :param password: Clave de apertura y administración.
    :param algorithm: 'AES-256' o 'AES-128'.
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo original no existe: {input_path}")

    if not password:
        raise PDFToolError("La contraseña no puede estar vacía.")

    if algorithm not in ("AES-256", "AES-128"):
        algorithm = "AES-256"

    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El archivo ya se encuentra protegido con contraseña. Desprotégelo primero.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        writer.encrypt(
            user_password=password,
            owner_password=password,
            algorithm=algorithm
        )

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "wb") as f_out:
            writer.write(f_out)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al encriptar el PDF: {str(e)}")


def decrypt_pdf(input_path: str, output_path: str, password: str) -> None:
    """
    Desbloquea y remueve la contraseña de un PDF protegido.
    
    :param input_path: Ruta al PDF encriptado.
    :param output_path: Ruta destino del PDF sin protección.
    :param password: Clave de desbloqueo.
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo no existe: {input_path}")

    if not password:
        raise PDFToolError("Debes ingresar la contraseña para desencriptar el documento.")

    try:
        reader = PdfReader(input_path)
        if not reader.is_encrypted:
            raise PDFToolError("Este archivo PDF no está protegido con contraseña.")

        res = reader.decrypt(password)
        # res devuelve 1 o 2 en éxito, 0 en fallo de credenciales
        if res == 0:
            raise PDFToolError("Contraseña incorrecta. No fue posible desbloquear el documento.")

        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, "wb") as f_out:
            writer.write(f_out)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al desproteger el PDF: {str(e)}")


# -----------------------------------------------------------------------------
# 7. CONVERTIR WORD (.docx) A PDF (INDIVIDUAL Y POR LOTES)
# -----------------------------------------------------------------------------
def convert_docx_to_pdf(docx_path: str, output_path: str) -> None:
    """Convierte un archivo de Word a PDF de forma nativa en Windows."""
    if not os.path.exists(docx_path):
        raise PDFToolError(f"El archivo Word no existe: {docx_path}")
        
    if not docx_path.lower().endswith((".docx", ".doc")):
        raise PDFToolError("El archivo no es un documento de Word válido (.docx o .doc).")
        
    try:
        from docx2pdf import convert
    except ImportError:
        raise PDFToolError("La librería 'docx2pdf' no está instalada.")
        
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        convert(docx_path, output_path)
        
        if not os.path.exists(output_path):
            raise PDFToolError("La conversión concluyó pero no se generó el archivo PDF esperado.")
            
    except PermissionError:
        raise PDFToolError(
            "Permiso denegado: El archivo Word está abierto en Microsoft Word o bloqueado por otro proceso. "
            "Por favor, cierra el documento e intenta de nuevo."
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "com_error" in err_msg or "rpc" in err_msg or "word.application" in err_msg or "clsid" in err_msg:
            raise PDFToolError(
                "No fue posible comunicarse con Microsoft Word en este equipo Windows. "
                "Asegúrate de tener Microsoft Word instalado y activado."
            )
        elif "locked" in err_msg or "in use" in err_msg:
            raise PDFToolError(
                "El documento de Word parece estar bloqueado o abierto en otra ventana. "
                "Cierra el documento en Word e intenta de nuevo."
            )
        else:
            raise PDFToolError(f"Error durante la conversión de Word a PDF: {str(e)}")


def convert_docx_batch(
    docx_paths: List[str],
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[str]:
    """
    Convierte múltiples archivos .docx a .pdf en lote.
    
    :param docx_paths: Lista de rutas a documentos Word.
    :param output_dir: Directorio de destino opcional (si es None, se guardan junto al original).
    :param progress_callback: Función llamada en cada paso con (índice_actual, total, ruta_actual).
    :return: Lista de archivos PDF generados.
    """
    if not docx_paths:
        raise PDFToolError("No se seleccionaron archivos Word para convertir.")

    converted_files: List[str] = []
    total = len(docx_paths)

    for idx, path in enumerate(docx_paths):
        if progress_callback:
            progress_callback(idx + 1, total, path)

        if output_dir:
            base_name = os.path.splitext(os.path.basename(path))[0] + ".pdf"
            out_target = os.path.join(output_dir, base_name)
        else:
            out_target = os.path.splitext(path)[0] + ".pdf"

        convert_docx_to_pdf(path, out_target)
        converted_files.append(out_target)

    return converted_files


# -----------------------------------------------------------------------------
# 8. CONVERTIR PDF A IMÁGENES (JPG / PNG)
# -----------------------------------------------------------------------------
def pdf_to_images(
    pdf_path: str,
    output_folder: str,
    fmt: str = "png",
    dpi: int = 150,
    pages_range: Optional[List[int]] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[str]:
    """
    Renderiza y extrae las páginas de un documento PDF como imágenes individuales (PNG o JPG).
    Utiliza PySide6.QtPdf de forma 100% nativa y local.
    
    :param pdf_path: Ruta al archivo PDF de entrada.
    :param output_folder: Carpeta destino para las imágenes extraídas.
    :param fmt: 'png' o 'jpg'.
    :param dpi: Densidad de píxeles (ej. 100, 150, 300).
    :param pages_range: Lista de índices 0-indexados opcionales a exportar.
    :param progress_callback: Callback para informar progreso (actual, total, nombre).
    :return: Lista de rutas a las imágenes generadas.
    """
    if not os.path.exists(pdf_path):
        raise PDFToolError(f"El archivo PDF no existe: {pdf_path}")
        
    try:
        from PySide6.QtGui import QGuiApplication, QImage
        from PySide6.QtCore import QSize
        from PySide6.QtPdf import QPdfDocument
        import sys
        
        # Asegurar instancia de QGuiApplication en hilos/procesos
        _app = QGuiApplication.instance()
        if _app is None:
            _app = QGuiApplication(sys.argv)
            
        doc = QPdfDocument()
        err = doc.load(pdf_path)
        if err != QPdfDocument.Error.None_:
            raise PDFToolError(f"No fue posible cargar el documento PDF (código: {err}).")
            
        total_pages = doc.pageCount()
        if total_pages <= 0:
            raise PDFToolError("El documento no contiene páginas legibles.")
            
        indices = pages_range if pages_range is not None else list(range(total_pages))
        if not indices:
            raise PDFToolError("No se especificaron páginas válidas para exportar.")
            
        os.makedirs(output_folder, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]
        ext = "png" if fmt.lower() == "png" else "jpg"
        save_format = "PNG" if ext == "png" else "JPEG"
        digits = max(3, len(str(total_pages)))
        
        generated: List[str] = []
        scale_factor = max(1.0, float(dpi) / 72.0)
        
        for step_idx, page_idx in enumerate(indices):
            if page_idx < 0 or page_idx >= total_pages:
                continue
                
            orig_size = doc.pagePointSize(page_idx)
            w_px = max(10, int(orig_size.width() * scale_factor))
            h_px = max(10, int(orig_size.height() * scale_factor))
            
            img: QImage = doc.render(page_idx, QSize(w_px, h_px))
            if img.isNull():
                continue
                
            out_filename = f"{base_name}_pag_{page_idx + 1:0{digits}d}.{ext}"
            out_path = os.path.join(output_folder, out_filename)
            
            if save_format == "JPEG":
                img.save(out_path, save_format, quality=92)
            else:
                img.save(out_path, save_format)
                
            generated.append(out_path)
            
            if progress_callback:
                progress_callback(step_idx + 1, len(indices), out_filename)
                
        if not generated:
            raise PDFToolError("No se generó ninguna imagen a partir del PDF.")
            
        return generated
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al convertir PDF a imágenes: {str(e)}")
    finally:
        if 'doc' in locals() and doc is not None:
            doc.close()
            del doc
            gc.collect()


# -----------------------------------------------------------------------------
# 9. AÑADIR MARCA DE AGUA (WATERMARK: TEXTO O IMAGEN)
# -----------------------------------------------------------------------------
def add_watermark(
    input_path: str,
    output_path: str,
    watermark_type: str = "text",
    text: str = "CONFIDENCIAL",
    image_path: Optional[str] = None,
    opacity: float = 0.3,
    angle: float = 45.0,
    font_size: int = 40,
    color_hex: str = "#888888",
    position: str = "center",
    scale: float = 0.5,
) -> None:
    """
    Inserta una marca de agua (texto personalizado o imagen PNG/JPG) sobre cada página de un PDF.
    Utiliza ReportLab y pypdf de manera 100% local.
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo original no existe: {input_path}")
        
    if watermark_type == "text" and not text.strip():
        raise PDFToolError("El texto de la marca de agua no puede estar vacío.")
        
    if watermark_type == "image":
        if not image_path or not os.path.exists(image_path):
            raise PDFToolError("Debes seleccionar una imagen válida para la marca de agua.")
            
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
        from reportlab.lib.utils import ImageReader
        
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El documento está protegido con contraseña. Desprotégelo primero.")
            
        writer = PdfWriter()
        alpha = max(0.05, min(1.0, float(opacity)))
        
        for page in reader.pages:
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            
            wbuf = io.BytesIO()
            c = canvas.Canvas(wbuf, pagesize=(w, h))
            
            # Posición base (x, y)
            if position == "top_left":
                x, y = w * 0.2, h * 0.82
            elif position == "top_center":
                x, y = w * 0.5, h * 0.82
            elif position == "top_right":
                x, y = w * 0.8, h * 0.82
            elif position == "bottom_left":
                x, y = w * 0.2, h * 0.18
            elif position == "bottom_center":
                x, y = w * 0.5, h * 0.18
            elif position == "bottom_right":
                x, y = w * 0.8, h * 0.18
            else:  # center
                x, y = w * 0.5, h * 0.5
                
            c.saveState()
            
            if watermark_type == "text":
                c.translate(x, y)
                c.rotate(angle)
                c.setFillColor(HexColor(color_hex), alpha=alpha)
                c.setFont("Helvetica-Bold", font_size)
                c.drawCentredString(0, -font_size / 3.0, text)
            else:
                img_obj = Image.open(image_path)
                img_w, img_h = img_obj.size
                target_w = img_w * scale
                target_h = img_h * scale
                
                # Centrar sobre (x, y)
                c.translate(x, y)
                c.rotate(angle)
                c.setFillAlpha(alpha)
                c.drawImage(
                    image_path,
                    -target_w / 2.0,
                    -target_h / 2.0,
                    width=target_w,
                    height=target_h,
                    mask="auto"
                )
                img_obj.close()
                
            c.restoreState()
            c.save()
            wbuf.seek(0)
            
            overlay_page = PdfReader(wbuf).pages[0]
            page.merge_page(overlay_page)
            writer.add_page(page)
            
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al aplicar la marca de agua: {str(e)}")


# -----------------------------------------------------------------------------
# 10. NUMERAR PÁGINAS (PAGE NUMBERS)
# -----------------------------------------------------------------------------
def add_page_numbers(
    input_path: str,
    output_path: str,
    format_str: str = "Página {n} de {total}",
    position: str = "bottom_center",
    font_size: int = 10,
    font_color: str = "#444444",
    start_page_num: int = 1,
    skip_first_pages: int = 0,
    margin_pt: float = 36.0,
) -> None:
    """
    Añade números de página personalizados a cada hoja del PDF.
    
    :param input_path: Ruta al archivo PDF.
    :param output_path: Ruta de destino.
    :param format_str: Cadena formateable con {n} y {total}.
    :param position: 'bottom_center', 'bottom_right', 'bottom_left', 'top_center', 'top_right', 'top_left'.
    :param font_size: Tamaño de fuente en puntos.
    :param font_color: Color hexadecimal del texto.
    :param start_page_num: Primer número a mostrar (ej. 1).
    :param skip_first_pages: Cantidad de páginas iniciales a omitir sin numerar (ej. portada).
    :param margin_pt: Margen de separación desde el borde en puntos (72 pt = 1 pulgada).
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo original no existe: {input_path}")
        
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.colors import HexColor
        
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El archivo está protegido con contraseña. Desprotégelo primero.")
            
        total_pages = len(reader.pages)
        effective_total = max(1, total_pages - skip_first_pages)
        writer = PdfWriter()
        
        for idx, page in enumerate(reader.pages):
            if idx < skip_first_pages:
                writer.add_page(page)
                continue
                
            curr_num = start_page_num + (idx - skip_first_pages)
            page_text = format_str.format(n=curr_num, total=effective_total)
            
            w = float(page.mediabox.width)
            h = float(page.mediabox.height)
            
            nbuf = io.BytesIO()
            c = canvas.Canvas(nbuf, pagesize=(w, h))
            c.setFont("Helvetica", font_size)
            c.setFillColor(HexColor(font_color))
            
            # Coordenadas
            is_top = position.startswith("top")
            is_right = position.endswith("right")
            is_left = position.endswith("left")
            
            y = (h - margin_pt) if is_top else margin_pt
            
            if is_left:
                x = margin_pt
                c.drawString(x, y, page_text)
            elif is_right:
                x = w - margin_pt
                c.drawRightString(x, y, page_text)
            else:
                x = w / 2.0
                c.drawCentredString(x, y, page_text)
                
            c.save()
            nbuf.seek(0)
            
            overlay_page = PdfReader(nbuf).pages[0]
            page.merge_page(overlay_page)
            writer.add_page(page)
            
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al añadir numeración de páginas: {str(e)}")


# -----------------------------------------------------------------------------
# 11. ROTAR PDF EN BLOQUE (BULK ROTATE)
# -----------------------------------------------------------------------------
def rotate_pdf_bulk(
    input_path: str,
    output_path: str,
    rotation: int = 90,
    page_filter: str = "all"
) -> int:
    """
    Gira las páginas de un PDF en bloque según un filtro.
    
    :param input_path: Ruta al archivo PDF.
    :param output_path: Ruta destino.
    :param rotation: Grados a rotar (+90, -90, 180, 270).
    :param page_filter: 'all', 'odd' (impares: 1, 3, 5...), 'even' (pares: 2, 4, 6...).
    :return: Cantidad de páginas modificadas.
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo no existe: {input_path}")
        
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El documento está protegido con contraseña. Desprotégelo primero.")
            
        writer = PdfWriter()
        rot_norm = rotation % 360
        changed_count = 0
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            should_rotate = False
            
            if page_filter == "odd" and page_num % 2 != 0:
                should_rotate = True
            elif page_filter == "even" and page_num % 2 == 0:
                should_rotate = True
            elif page_filter == "all":
                should_rotate = True
                
            if should_rotate and rot_norm != 0:
                page.rotate(rot_norm)
                changed_count += 1
                
            writer.add_page(page)
            
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            
        return changed_count
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al rotar páginas en bloque: {str(e)}")


# -----------------------------------------------------------------------------
# 12. EXTRAER TEXTO PLANO (PDF A TXT)
# -----------------------------------------------------------------------------
def extract_text_from_pdf(
    input_path: str,
    output_path: str,
    add_page_separator: bool = True
) -> Dict[str, Any]:
    """
    Extrae todo el texto legible del PDF a un archivo .txt plano.
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo no existe: {input_path}")
        
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El documento está protegido con contraseña. Desprotégelo primero.")
            
        total_pages = len(reader.pages)
        all_text_chunks: List[str] = []
        total_chars = 0
        
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            total_chars += len(text)
            
            if add_page_separator:
                all_text_chunks.append(f"--- PÁGINA {idx + 1} DE {total_pages} ---\n\n{text}\n\n")
            else:
                all_text_chunks.append(text + "\n\n")
                
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        full_content = "".join(all_text_chunks)
        with open(output_path, "w", encoding="utf-8") as f_out:
            f_out.write(full_content)
            
        words = len(full_content.split())
        return {
            "page_count": total_pages,
            "character_count": total_chars,
            "word_count": words,
            "output_path": output_path
        }
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al extraer texto del PDF: {str(e)}")


# -----------------------------------------------------------------------------
# 13. RECORTAR PDF (CROP MARGINS)
# -----------------------------------------------------------------------------
def crop_pdf_margins(
    input_path: str,
    output_path: str,
    left_pt: float = 0.0,
    right_pt: float = 0.0,
    top_pt: float = 0.0,
    bottom_pt: float = 0.0
) -> int:
    """
    Ajusta el cuadro de recorte (CropBox) de cada página de un PDF.
    """
    if not os.path.exists(input_path):
        raise PDFToolError(f"El archivo original no existe: {input_path}")
        
    try:
        reader = PdfReader(input_path)
        if reader.is_encrypted:
            raise PDFToolError("El archivo está protegido con contraseña. Desprotégelo primero.")
            
        writer = PdfWriter()
        total_pages = len(reader.pages)
        
        for page in reader.pages:
            orig_ll = page.cropbox.lower_left
            orig_ur = page.cropbox.upper_right
            
            new_ll_x = orig_ll[0] + left_pt
            new_ll_y = orig_ll[1] + bottom_pt
            new_ur_x = orig_ur[0] - right_pt
            new_ur_y = orig_ur[1] - top_pt
            
            if new_ll_x < new_ur_x and new_ll_y < new_ur_y:
                page.cropbox.lower_left = (new_ll_x, new_ll_y)
                page.cropbox.upper_right = (new_ur_x, new_ur_y)
                
            writer.add_page(page)
            
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
            
        return total_pages
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al recortar márgenes del PDF: {str(e)}")


# -----------------------------------------------------------------------------
# 14. EXCEL (.XLSX/.XLS) A PDF
# -----------------------------------------------------------------------------
def convert_excel_to_pdf(excel_path: str, output_path: str) -> None:
    """Convierte una hoja de cálculo Excel a PDF usando COM nativo en Windows."""
    if not os.path.exists(excel_path):
        raise PDFToolError(f"El archivo Excel no existe: {excel_path}")
        
    try:
        import win32com.client
    except ImportError:
        raise PDFToolError("El módulo 'pywin32' no está disponible.")
        
    excel = None
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        
        wb = excel.Workbooks.Open(os.path.abspath(excel_path))
        # 0 corresponde a xlTypePDF
        wb.ExportAsFixedFormat(0, os.path.abspath(output_path))
        wb.Close(False)
    except Exception as e:
        raise PDFToolError(f"Error al convertir Excel a PDF: {str(e)}")
    finally:
        if excel:
            try:
                excel.Quit()
            except Exception:
                pass


def convert_excel_batch(
    excel_paths: List[str],
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[str]:
    """Convierte múltiples archivos Excel a PDF en lote."""
    if not excel_paths:
        raise PDFToolError("No se seleccionaron archivos Excel para convertir.")
        
    converted: List[str] = []
    total = len(excel_paths)
    for idx, path in enumerate(excel_paths):
        if progress_callback:
            progress_callback(idx + 1, total, path)
            
        if output_dir:
            base_name = os.path.splitext(os.path.basename(path))[0] + ".pdf"
            out_target = os.path.join(output_dir, base_name)
        else:
            out_target = os.path.splitext(path)[0] + ".pdf"
            
        convert_excel_to_pdf(path, out_target)
        converted.append(out_target)
    return converted


# -----------------------------------------------------------------------------
# 15. POWERPOINT (.PPTX/.PPT) A PDF
# -----------------------------------------------------------------------------
def convert_powerpoint_to_pdf(ppt_path: str, output_path: str) -> None:
    """Convierte una presentación PowerPoint a PDF usando COM nativo en Windows."""
    if not os.path.exists(ppt_path):
        raise PDFToolError(f"El archivo de presentación no existe: {ppt_path}")
        
    try:
        import win32com.client
    except ImportError:
        raise PDFToolError("El módulo 'pywin32' no está disponible.")
        
    ppt_app = None
    try:
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        ppt_app = win32com.client.DispatchEx("PowerPoint.Application")
        # 32 corresponde a ppSaveAsPDF
        presentation = ppt_app.Presentations.Open(os.path.abspath(ppt_path), WithWindow=False)
        presentation.SaveAs(os.path.abspath(output_path), 32)
        presentation.Close()
    except Exception as e:
        raise PDFToolError(f"Error al convertir PowerPoint a PDF: {str(e)}")
    finally:
        if ppt_app:
            try:
                ppt_app.Quit()
            except Exception:
                pass


def convert_powerpoint_batch(
    ppt_paths: List[str],
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None
) -> List[str]:
    """Convierte múltiples archivos PowerPoint a PDF en lote."""
    if not ppt_paths:
        raise PDFToolError("No se seleccionaron archivos PowerPoint para convertir.")
        
    converted: List[str] = []
    total = len(ppt_paths)
    for idx, path in enumerate(ppt_paths):
        if progress_callback:
            progress_callback(idx + 1, total, path)
            
        if output_dir:
            base_name = os.path.splitext(os.path.basename(path))[0] + ".pdf"
            out_target = os.path.join(output_dir, base_name)
        else:
            out_target = os.path.splitext(path)[0] + ".pdf"
            
        convert_powerpoint_to_pdf(path, out_target)
        converted.append(out_target)
    return converted


# -----------------------------------------------------------------------------
# 16. PDF A WORD (.DOCX)
# -----------------------------------------------------------------------------
def convert_pdf_to_word(pdf_path: str, output_path: str) -> int:
    """
    Convierte el contenido textual y estructura de un PDF a un documento Word (.docx) editable.
    Utiliza python-docx y pypdf de forma 100% local.
    """
    if not os.path.exists(pdf_path):
        raise PDFToolError(f"El archivo PDF no existe: {pdf_path}")
        
    try:
        import docx
        from docx.shared import Pt, Inches
    except ImportError:
        raise PDFToolError("La librería 'python-docx' no está instalada.")
        
    try:
        reader = PdfReader(pdf_path)
        if reader.is_encrypted:
            raise PDFToolError("El documento está protegido con contraseña. Desprotégelo primero.")
            
        doc = docx.Document()
        total_pages = len(reader.pages)
        
        for idx, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            
            for line in lines:
                doc.add_paragraph(line)
                
            if idx < total_pages - 1:
                doc.add_page_break()
                
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        doc.save(output_path)
        return total_pages
    except PDFToolError:
        raise
    except Exception as e:
        raise PDFToolError(f"Error al convertir PDF a Word: {str(e)}")
