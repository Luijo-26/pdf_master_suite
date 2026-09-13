"""
pdf_tools.py
Módulo de lógica pura para manipulación de documentos PDF, imágenes y conversión de Word a PDF.
No contiene dependencias de interfaz gráfica (GUI), permitiendo pruebas automatizadas y ejecución limpia.
"""

import os
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
