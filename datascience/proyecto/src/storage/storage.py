"""Módulo para lectura, escrituras atómicas y copias de respaldo."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

from settings import Settings

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, settings: Settings):
        self.settings = settings

    def cargar_taxonomia(self) -> tuple[dict, dict, list[str]]:
        path = self.settings.FILE_TAXONOMIA_DESCUBIERTA
        if not path.exists():
            raise FileNotFoundError(
                f"No existe el archivo de taxonomía en {path}. "
                "Ejecuta primero el script: descubrimiento_taxonomia.py"
            )

        info_taxonomia = json.loads(path.read_text(encoding="utf-8"))
        categorias = info_taxonomia.get("categorias", {})
        nombres_a_id = {info["nombre"]: cid for cid, info in categorias.items()}
        return info_taxonomia, nombres_a_id, list(nombres_a_id.keys())

    def cargar_salida_previa(self, path_salida: Path) -> dict:
        if not path_salida.exists():
            return {}
        try:
            lista = json.loads(path_salida.read_text(encoding="utf-8"))
            return {
                d.get("documento_id") or d.get("metadata", {}).get("archivo"): d
                for d in lista
            }
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("No se pudo leer la salida previa (%s): %s", path_salida, e)
            return {}

    def respaldar_salida_anterior(self, path_salida: Path) -> None:
        if not path_salida.exists():
            return
        self.settings.produccion_backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destino = (
            self.settings.produccion_backups_dir / f"{path_salida.stem}_{timestamp}.json"
        )
        shutil.copy2(path_salida, destino)
        logger.info("Respaldo previo creado en: %s", destino)

    def guardar_json_atomico(self, path_salida: Path, data: list[dict]) -> None:
        path_salida.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path_salida.with_suffix(".tmp")
        temp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temp_path.replace(path_salida)