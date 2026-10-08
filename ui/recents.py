"""
ui/recents.py
Historial de documentos generados recientemente.
Guarda en JSON en AppData o directorio de configuración del usuario.
Permite abrir el archivo o abrir su carpeta contenedora en el Explorador de Windows.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional


def _get_history_file() -> str:
    app_data = os.getenv("APPDATA") or os.path.expanduser("~")
    base_dir = os.path.join(app_data, "PDFMasterSuite")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "recent_files.json")


def add_recent(file_path: str, tool_name: str) -> None:
    """Registra un archivo generado recientemente."""
    if not file_path or not os.path.exists(file_path):
        return

    path = os.path.normpath(file_path)
    history = get_recents()

    # Eliminar duplicado si ya estaba
    history = [item for item in history if os.path.normpath(item.get("path", "")) != path]

    stat = os.stat(path)
    entry = {
        "path": path,
        "name": os.path.basename(path),
        "tool": tool_name,
        "size": stat.st_size,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "timestamp": datetime.now().timestamp(),
    }
    history.insert(0, entry)
    history = history[:12]  # Máximo 12 recientes

    try:
        with open(_get_history_file(), "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_recents() -> List[Dict[str, Any]]:
    """Devuelve la lista de archivos recientes que aún existen en el disco."""
    hfile = _get_history_file()
    if not os.path.exists(hfile):
        return []

    try:
        with open(hfile, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Filtrar los que sigan existiendo
            valid = [item for item in data if os.path.exists(item.get("path", ""))]
            return valid[:10]
    except Exception:
        return []


def open_file(file_path: str) -> bool:
    """Abre el archivo con su aplicación predeterminada del sistema."""
    if not file_path or not os.path.exists(file_path):
        return False
    try:
        os.startfile(file_path)
        return True
    except Exception:
        try:
            if sys.platform == "win32":
                subprocess.Popen(["start", "", file_path], shell=True)
                return True
        except Exception:
            pass
    return False


def open_folder(file_path: str) -> bool:
    """Abre el Explorador de Windows y selecciona el archivo."""
    if not file_path:
        return False
    try:
        norm_path = os.path.normpath(file_path)
        if os.path.exists(norm_path):
            if sys.platform == "win32":
                subprocess.Popen(f'explorer /select,"{norm_path}"')
                return True
            else:
                folder = os.path.dirname(norm_path)
                os.startfile(folder)
                return True
    except Exception:
        pass
    return False
