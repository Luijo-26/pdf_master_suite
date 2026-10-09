"""
core/updater.py
Motor de comprobación, descarga y actualización automática para PDF Master Suite.
Integra la API pública de GitHub Releases, descarga multihilo con PySide6
y mecanismo de reemplazo en caliente (hot-swap) para ejecutables de Windows.
"""

from dataclasses import dataclass
import json
import os
import subprocess
import sys
import tempfile
import time
from typing import Optional, Tuple
import urllib.request
import urllib.error

from PySide6.QtCore import QSettings, QThread, Signal
from PySide6.QtWidgets import QApplication

from core.version import (
    APP_VERSION,
    GITHUB_API_LATEST,
    GITHUB_RELEASES_PAGE,
    is_newer_version,
)

SETTINGS_ORG = "PDFMaster"
SETTINGS_APP = "PDFMasterSuite"
SETTINGS_KEY_IGNORED = "updates/ignored_version"
SETTINGS_KEY_LAST_CHECK = "updates/last_check_timestamp"


@dataclass
class ReleaseInfo:
    tag_name: str
    version: str
    title: str
    body: str
    download_url: str
    asset_name: str
    asset_size: int
    published_at: str
    html_url: str


def get_ignored_version() -> str:
    """Obtiene la versión omitida por el usuario si existe."""
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    return str(settings.value(SETTINGS_KEY_IGNORED, ""))


def set_ignored_version(version: str):
    """Guarda una versión para no volver a notificar automáticamente."""
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    settings.setValue(SETTINGS_KEY_IGNORED, version)


def clear_ignored_version():
    """Limpia la versión omitida."""
    settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
    settings.remove(SETTINGS_KEY_IGNORED)


def fetch_latest_release(timeout: int = 6) -> Optional[ReleaseInfo]:
    """
    Consulta la API de GitHub Releases para obtener los metadatos de la última versión pública.
    Retorna ReleaseInfo si tiene éxito, o None si no hay conexión o falla la petición.
    """
    req = urllib.request.Request(
        GITHUB_API_LATEST,
        headers={
            "User-Agent": f"PDFMasterSuite-Updater/{APP_VERSION}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

    tag_name = data.get("tag_name", "")
    version_clean = tag_name.lstrip("vV")
    title = data.get("name") or f"PDF Master Suite {tag_name}"
    body = data.get("body", "").strip()
    html_url = data.get("html_url") or GITHUB_RELEASES_PAGE
    published_at = data.get("published_at", "")

    # Buscar el ejecutable de Windows (.exe) en los assets
    download_url = ""
    asset_name = ""
    asset_size = 0

    assets = data.get("assets", [])
    for asset in assets:
        name = asset.get("name", "")
        if name.lower().endswith(".exe"):
            download_url = asset.get("browser_download_url", "")
            asset_name = name
            asset_size = asset.get("size", 0)
            break

    # Si no hay asset .exe compilado, fallback a la URL del release en navegador
    if not download_url and assets:
        download_url = assets[0].get("browser_download_url", "")
        asset_name = assets[0].get("name", "")
        asset_size = assets[0].get("size", 0)

    if not download_url:
        download_url = html_url

    return ReleaseInfo(
        tag_name=tag_name,
        version=version_clean,
        title=title,
        body=body,
        download_url=download_url,
        asset_name=asset_name,
        asset_size=asset_size,
        published_at=published_at,
        html_url=html_url,
    )


class UpdateCheckThread(QThread):
    """Hilo asíncrono para comprobar si hay una nueva versión sin bloquear la UI."""
    check_finished = Signal(object, bool)  # (ReleaseInfo or None, has_update: bool)
    check_failed = Signal(str)

    def __init__(self, force_check: bool = False, parent=None):
        super().__init__(parent)
        self.force_check = force_check

    def run(self):
        try:
            info = fetch_latest_release(timeout=6)
            if not info:
                self.check_finished.emit(None, False)
                return

            has_update = is_newer_version(info.version, APP_VERSION)

            # Si no es forzado, revisar si el usuario pidió omitir esta versión
            if has_update and not self.force_check:
                ignored = get_ignored_version()
                if ignored and ignored == info.version:
                    has_update = False

            self.check_finished.emit(info, has_update)
        except Exception as e:
            self.check_failed.emit(str(e))


class UpdateDownloadThread(QThread):
    """Hilo asíncrono para descargar el ejecutable de la nueva versión con reporte de progreso."""
    progress = Signal(int, int, float, float)  # downloaded_bytes, total_bytes, percent, speed_kbps
    finished = Signal(str)  # temp_filepath
    error = Signal(str)
    cancelled = Signal()

    def __init__(self, download_url: str, file_name: str = "", parent=None):
        super().__init__(parent)
        self.download_url = download_url
        self.file_name = file_name or "PDFMasterSuite_update.exe"
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f"PDFMasterSuite_update_{int(time.time())}.exe")

        req = urllib.request.Request(
            self.download_url,
            headers={
                "User-Agent": f"PDFMasterSuite-Updater/{APP_VERSION}",
                "Accept": "*/*",
            },
        )

        try:
            start_time = time.time()
            downloaded = 0
            chunk_size = 64 * 1024  # 64 KB

            with urllib.request.urlopen(req, timeout=30) as response, open(temp_path, "wb") as out_file:
                total_size = int(response.headers.get("Content-Length", 0))

                while not self._is_cancelled:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)

                    elapsed = max(0.001, time.time() - start_time)
                    speed_kbps = (downloaded / 1024.0) / elapsed
                    percent = (downloaded / total_size * 100.0) if total_size > 0 else 0.0

                    self.progress.emit(downloaded, total_size, percent, speed_kbps)

            if self._is_cancelled:
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                self.cancelled.emit()
                return

            self.finished.emit(temp_path)

        except Exception as e:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            self.error.emit(str(e))


def apply_update_and_restart(temp_exe_path: str) -> Tuple[bool, str]:
    """
    Aplica la actualización reemplazando el binario actual mediante un script
    de relevo desacoplado en Windows y relanza la aplicación.
    
    Retorna (True, "") si se lanzó exitosamente el proceso de relevo,
    o (False, reason) si está en modo desarrollo o hubo un fallo.
    """
    is_frozen = getattr(sys, "frozen", False)
    
    if not is_frozen:
        # Modo de desarrollo (ejecutado con python main.py)
        return (False, "dev_mode")

    current_exe = sys.executable
    if not os.path.exists(temp_exe_path):
        return (False, "El archivo de actualización descargado no existe.")

    # Generar script batch de relevo en %TEMP%
    bat_path = os.path.join(tempfile.gettempdir(), f"pms_updater_{os.getpid()}.bat")
    current_pid = os.getpid()

    bat_content = f"""@echo off
chcp 65001 > nul
set "TARGET_PID={current_pid}"
set "NEW_EXE={temp_exe_path}"
set "DEST_EXE={current_exe}"

:: Esperar a que el proceso anterior finalice completamente
:wait_loop
tasklist /fi "PID eq %TARGET_PID%" | findstr /i "%TARGET_PID%" > nul
if %errorlevel% equ 0 (
    timeout /t 1 /nobreak > nul
    goto wait_loop
)

:: Reemplazar el binario existente por el nuevo
copy /y /b "%NEW_EXE%" "%DEST_EXE%" > nul
if %errorlevel% neq 0 (
    :: Reintento en caso de demora del sistema de archivos
    timeout /t 1 /nobreak > nul
    copy /y /b "%NEW_EXE%" "%DEST_EXE%" > nul
)

:: Relanzar la aplicación actualizada
start "" "%DEST_EXE%"

:: Limpieza de temporales y autoeliminación del script
del "%NEW_EXE%" > nul 2>&1
(goto) 2>nul & del "%~f0"
"""

    try:
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(bat_content)

        # Lanzar el proceso desacoplado en Windows
        creation_flags = 0
        if os.name == "nt":
            creation_flags = (
                getattr(subprocess, "DETACHED_PROCESS", 0) |
                getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )

        subprocess.Popen(
            ["cmd.exe", "/c", bat_path],
            creationflags=creation_flags,
            close_fds=True,
        )

        # Cerrar la aplicación actual de forma ordenada
        QApplication.quit()
        return (True, "")
    except Exception as e:
        return (False, f"Error al iniciar el asistente de reemplazo: {e}")
