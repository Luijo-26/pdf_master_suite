"""
core/settings.py
Gestor centralizado de configuración y preferencias de usuario para PDF Master Suite.
Guarda las preferencias en formato JSON en el directorio de datos de la aplicación.
"""

import json
import os
from typing import Any, Callable, Dict, List, Optional

_DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "dark",             # "dark", "light", "oled", "navy", "emerald"
    "accent": "indigo",          # "indigo", "blue", "emerald", "amber", "rose"
    "auto_open_viewer": True,    # Abrir visor automáticamente al finalizar tareas
    "check_updates_startup": True, # Comprobar versión al inicio
    "fit_mode": "fit_width",     # "fit_width", "fit_page"
}

_listeners: List[Callable[[str, Any], None]] = []


def _get_settings_path() -> str:
    app_data = os.getenv("APPDATA") or os.path.expanduser("~")
    base_dir = os.path.join(app_data, "PDFMasterSuite")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "settings.json")


def load_settings() -> Dict[str, Any]:
    """Carga todas las configuraciones almacenadas, rellenando con valores por defecto."""
    path = _get_settings_path()
    settings = dict(_DEFAULT_SETTINGS)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved, dict):
                    settings.update(saved)
        except Exception:
            pass
    return settings


def save_settings(settings: Dict[str, Any]) -> bool:
    """Guarda el diccionario de configuración completo en el archivo JSON."""
    path = _get_settings_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_setting(key: str, default: Any = None) -> Any:
    """Obtiene el valor de una clave específica."""
    settings = load_settings()
    return settings.get(key, default if default is not None else _DEFAULT_SETTINGS.get(key))


def set_setting(key: str, value: Any) -> bool:
    """Establece y guarda una clave específica, notificando a los listeners."""
    settings = load_settings()
    old_value = settings.get(key)
    settings[key] = value
    ok = save_settings(settings)
    if ok and old_value != value:
        for listener in _listeners:
            try:
                listener(key, value)
            except Exception:
                pass
    return ok


def reset_settings() -> bool:
    """Restaura todas las configuraciones a sus valores predeterminados."""
    ok = save_settings(dict(_DEFAULT_SETTINGS))
    if ok:
        for listener in _listeners:
            try:
                listener("__reset__", _DEFAULT_SETTINGS)
            except Exception:
                pass
    return ok


def add_settings_listener(listener: Callable[[str, Any], None]) -> None:
    """Registra una función a invocar cuando cambie una configuración."""
    if listener not in _listeners:
        _listeners.append(listener)


def remove_settings_listener(listener: Callable[[str, Any], None]) -> None:
    if listener in _listeners:
        _listeners.remove(listener)
