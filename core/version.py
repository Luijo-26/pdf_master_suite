"""
core/version.py
Metadatos de versión y utilidades de comparación semántica para PDF Master Suite.
"""

import re
from typing import Tuple

APP_NAME = "PDF Master Suite"
APP_VERSION = "2.3.0"
GITHUB_REPO = "Luijo-26/pdf_master_suite"
GITHUB_API_LATEST = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_RELEASES_PAGE = f"https://github.com/{GITHUB_REPO}/releases"


def parse_version(version_str: str) -> Tuple[int, ...]:
    """
    Convierte una cadena de versión (ej. 'v2.1', 'V2.1.0', 'v1.0.0.0')
    en una tupla de enteros normalizada de longitud mínima 4 para comparación precisa.
    """
    if not version_str:
        return (0, 0, 0, 0)
    
    # Extraer todos los bloques numéricos
    numbers = [int(n) for n in re.findall(r"\d+", str(version_str))]
    if not numbers:
        return (0, 0, 0, 0)
    
    # Rellenar con ceros hasta al menos 4 posiciones (ej. 2.1 -> 2.1.0.0)
    while len(numbers) < 4:
        numbers.append(0)
        
    return tuple(numbers[:4])


def is_newer_version(remote_version: str, local_version: str = APP_VERSION) -> bool:
    """
    Retorna True si remote_version es estrictamente más reciente que local_version.
    """
    return parse_version(remote_version) > parse_version(local_version)
