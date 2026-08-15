"""
Módulo para lectura y escritura atómica de archivos JSON.

Sin memoria de corridas anteriores ni copias de respaldo: cada
guardado sobreescribe directamente el archivo oficial.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from settings import Settings

logger = logging.getLogger(__name__)


class StorageManager:
    def __init__(self, settings: Settings):
        self.settings = settings

    def cargar_taxonomia(self) -> tuple[dict, dict, list[str]]:
        path = self.settings.FILE_TAXONOMIA_DESCUBIERTA
        if not path.exists():
            raise FileNotFoundError(f"No existe el archivo de taxonomía en {path}.")

        data = json.loads(path.read_text(encoding="utf-8"))

        # Manejar ambos formatos: dict directo o lista con un dict (por compatibilidad)
        if isinstance(data, list) and len(data) > 0:
            info_taxonomia = data[0]
            logger.warning("Taxonomía cargada en formato legado (lista). Convirtiendo a dict directo.")
        elif isinstance(data, dict):
            info_taxonomia = data
        else:
            raise ValueError(f"Formato de taxonomía no reconocido en {path}")

        categorias = info_taxonomia.get("categorias", {})

        nombres_a_id = {info.get("nombre", cid): cid for cid, info in categorias.items()}
        lista_nombres = [info.get("nombre", cid) for cid, info in categorias.items()]

        return info_taxonomia, nombres_a_id, lista_nombres

    def guardar_json_atomico(self, path_salida: Path, data: list[dict]) -> None:
        """Guarda los datos de forma atómica directamente en la ruta oficial especificada."""
        path_salida.parent.mkdir(parents=True, exist_ok=True)

        temp_path = path_salida.with_suffix(".tmp")
        temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Reemplaza o crea el archivo oficial en su ruta de producción
        temp_path.replace(path_salida)
        logger.info("Archivo oficial guardado correctamente en: %s", path_salida.resolve())