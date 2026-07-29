#!/usr/bin/env python3
"""
descargar_musica.py

Lee un archivo "videos.txt" (ubicado en la misma carpeta que este script,
un nombre de cancion/video por linea), busca en YouTube el resultado
mas relevante para cada linea y descarga el audio en MP3 a 320kbps
(o la maxima calidad posible), dejando los archivos en la carpeta raiz
con el formato "Banda - Cancion.mp3".

Dependencias:
    - yt-dlp   (pip install yt-dlp --break-system-packages)
    - ffmpeg   (debe estar instalado en el sistema)

Uso:
    1) Crea "videos.txt" junto a este script con una busqueda por linea:
         Queen - Bohemian Rhapsody
         Soda Stereo De Musica Ligera
         ...
    2) python3 descargar_musica.py
       (opcionalmente: python3 descargar_musica.py otro_archivo.txt)
"""

import logging
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print(
        "ERROR: falta la libreria 'yt-dlp'.\n"
        "Instalala con: pip install yt-dlp --break-system-packages",
        file=sys.stderr,
    )
    sys.exit(1)

# ----------------------------------------------------------------------
# CONFIGURACION
# ----------------------------------------------------------------------

# Carpeta raiz donde se guardan los MP3 (la misma donde esta el script)
CARPETA_DESTINO = Path(__file__).resolve().parent

# Archivo con la lista de busquedas, una por linea
ARCHIVO_LISTA = CARPETA_DESTINO / "videos.txt"

# ----------------------------------------------------------------------
# LOGGING
# ----------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("descargar_musica")


class LoggerYTDLP:
    """Redirige los mensajes internos de yt-dlp al logging estandar."""

    def debug(self, msg):
        if msg.startswith("[debug] "):
            return
        log.debug(msg)

    def info(self, msg):
        log.info(msg)

    def warning(self, msg):
        log.warning(msg)

    def error(self, msg):
        log.error(msg)


def hook_progreso(d):
    """Callback de progreso de yt-dlp."""
    if d["status"] == "finished":
        log.info("Descarga completa, convirtiendo a MP3: %s", d.get("filename", ""))
    elif d["status"] == "error":
        log.error("Error durante la descarga de: %s", d.get("filename", "desconocido"))


def construir_opciones():
    return {
        # Formato de salida: "Banda - Cancion.mp3"
        "outtmpl": str(CARPETA_DESTINO / "%(artist,uploader)s - %(title)s.%(ext)s"),
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",  # 320kbps o la maxima disponible
            }
        ],
        "logger": LoggerYTDLP(),
        "progress_hooks": [hook_progreso],
        "noplaylist": True,
        "ignoreerrors": True,  # sigue con la siguiente busqueda si una falla
        "quiet": True,
        "no_warnings": False,
        "default_search": "ytsearch1",  # toma el resultado mas relevante
    }


def leer_lista(archivo: Path):
    if not archivo.exists():
        log.error("No se encontro el archivo '%s'.", archivo.name)
        return []

    lineas = [l.strip() for l in archivo.read_text(encoding="utf-8").splitlines()]
    lineas = [l for l in lineas if l and not l.startswith("#")]

    if not lineas:
        log.error("El archivo '%s' esta vacio.", archivo.name)

    return lineas


def descargar(busquedas):
    if not busquedas:
        return

    exitosas = 0
    fallidas = 0

    with yt_dlp.YoutubeDL(construir_opciones()) as ydl:
        for termino in busquedas:
            log.info("Buscando: %s", termino)
            try:
                # ytsearch1: -> toma el primer resultado (el mas relevante)
                resultado = ydl.download([f"ytsearch1:{termino}"])
                if resultado == 0:
                    exitosas += 1
                else:
                    fallidas += 1
                    log.error("Fallo la descarga de: %s", termino)
            except Exception as e:
                fallidas += 1
                log.error("Excepcion al descargar '%s' -> %s", termino, e)

    log.info("Proceso terminado. Exitosas: %d | Fallidas: %d", exitosas, fallidas)


if __name__ == "__main__":
    archivo = Path(sys.argv[1]) if len(sys.argv) > 1 else ARCHIVO_LISTA
    log.info("Leyendo lista desde: %s", archivo)
    descargar(leer_lista(archivo))
