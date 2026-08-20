"""
Configuración unificada y centralizada para todo el sistema KNOGMENT_NAYE
utilizando Pydantic Settings V2.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List
from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# FIX: settings.py vive en proyecto/settings.py. Un solo .parent da "proyecto/",
# que es donde también vive el .env real (proyecto/.env). Esto funciona igual
# en local y en Docker: en el contenedor, tras aplanar proyecto/ a /app/,
# settings.py y .env quedan juntos en /app/ — sigue siendo "un solo .parent".
PROJECT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    ROOT_DIR: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent) # apartir de seting general

    @property
    def DB_DIR(self) -> Path:
        return self.ROOT_DIR / "db"

    @property
    def JSON_INPUT_DIR(self) -> Path:
        return self.DB_DIR / "input_json"

    @property
    def SALIDA_JSON_DIR(self) -> Path:
        return self.DB_DIR / "output_json"

    @property
    def ARCHIVOS_DIR(self) -> Path:
        return self.DB_DIR / "archivos"

    # ==========================================================================
    # 2. MODELOS E INTEGRACIONES API (LLMs & NLP)
    # ==========================================================================
    DEEPSEEK_API_KEY: str = Field(default="", validation_alias="DEEPSEEK_API_KEY")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", validation_alias="DEEPSEEK_MODEL")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MAX_RETRIES: int = 2
    DEEPSEEK_RATE_LIMIT_SECONDS: float = 4.0

    GEMINI_API_KEY: str = Field(default="", validation_alias="GEMINI_API_KEY")
    GEMINI_MODEL_1: str = Field(default="gemini-3.5-flash-lite")
    GEMINI_MODEL_2: str = Field(default="gemini-3.1-flash-lite")
    GEMINI_MAX_RETRIES: int = 1
    GEMINI_RATE_LIMIT_SECONDS: float = 5.0

    MODELO_EMBEDDINGS: str = Field(
        default="paraphrase-multilingual-mpnet-base-v2",
        validation_alias="MODELO_EMBEDDINGS"
    )
    SPACY_MODEL: str = Field(default="es_dep_news_trf", validation_alias="SPACY_MODEL")

    # Fuente de datos: la API sincroniza OCI a DB_DIR antes de cargar GraphRAG.
    DATA_SOURCE: str = Field(default="local", validation_alias="DATA_SOURCE")
    OCI_BUCKET_NAME: str = Field(
        default="",
        validation_alias=AliasChoices("OCI_BUCKET_NAME", "OCI_DATASET_BUCKET"),
    )
    OCI_NAMESPACE: str = Field(default="", validation_alias="OCI_NAMESPACE")
    OCI_PREFIX: str = Field(default="prod", validation_alias="OCI_PREFIX")
    OCI_AUTH_MODE: str = Field(default="api_key", validation_alias="OCI_AUTH_MODE")
    OCI_CONFIG_FILE: str = Field(default="", validation_alias="OCI_CONFIG_FILE")
    OCI_CONFIG_PROFILE: str = Field(default="DEFAULT", validation_alias="OCI_CONFIG_PROFILE")
    OCI_SYNC_ON_STARTUP: bool = Field(default=True, validation_alias="OCI_SYNC_ON_STARTUP")

    # ==========================================================================
    # 3. REGLAS Y PROMPTS
    # ==========================================================================
    @property
    def CONFIG_RULES_PATH(self) -> Path:
        return self.JSON_INPUT_DIR / "rules.json"

    @property
    def RELATIONS_PATH(self) -> Path:
        return self.JSON_INPUT_DIR / "relations.json"

    @property
    def GLOSARIO_PATH(self) -> Path:
        return self.JSON_INPUT_DIR / "glosario.json"

    @property
    def CLEANING_RULES_PATH(self) -> Path:
        return self.JSON_INPUT_DIR / "cleaning_rules.json"

    # PROMPTS 

    @property
    def PROMPTS_DIR(self) -> Path:

        return PROJECT_DIR / "prompts"

    @property
    def PROMPT_EXTRACTION_PATH(self) -> Path:
        return self.PROMPTS_DIR / "prompt_extraction.txt"
    @property
    def PROMPT_CLASSIFIER_ETIQUETA(self) -> Path:
        return self.PROMPTS_DIR / "prompt_etiqueta.txt"

    @property
    def PROMT_CLASSIFIER_PATH(self)->Path:
        return self.PROMPTS_DIR / "prompt_clasificacion.txt"

    @property
    def PROMPT_RAG_SISTEMA_PATH(self) -> Path:
        return self.PROMPTS_DIR / "prompt_rag_sistema.txt"

    # ==========================================================================
    # 4. PARÁMETROS POR ETAPAS
    # ==========================================================================
    MIN_CATEGORIAS: int = 12
    MAX_CATEGORIAS_POR_DOCUMENTO: int = 10
    UMBRAL_CONFIANZA: float = 0.60
    DOCUMENTOS_POR_LOTE: int = 5

    BATCH_SIZE_EMBEDDINGS: int = Field(default=32, validation_alias="BATCH_SIZE_EMBEDDINGS")
    CONCEPTOS_TOP_POR_SECCION: int = Field(default=5, validation_alias="CONCEPTOS_TOP_POR_SECCION")
    CONFIANZA_MINIMA_RELACION: float = Field(default=0.75, validation_alias="CONFIANZA_MINIMA_RELACION")
    SCORE_MINIMO_CONCEPTO: float = Field(default=0.65, validation_alias="SCORE_MINIMO_CONCEPTO")
    ROOT_ID: str = Field(default="NODE_ROOT_CORPUS", validation_alias="ROOT_ID")

    TOP_K_NODOS: int = Field(default=5, validation_alias="TOP_K_NODOS")
    TOP_K_SECCIONES_FINAL: int = Field(default=5, validation_alias="TOP_K_SECCIONES_FINAL")

    #----ETAPA 4 BALANCEO DE NODOS Y RUTA JERÁRQUICA----

    MIN_SECCIONES_NIVEL_1_3: int = Field(default=2, validation_alias="MIN_SECCIONES_NIVEL_1_3")
    UMBRAL_NIVEL_4_6: float = Field(default=0.55, validation_alias="UMBRAL_NIVEL_4_6")
    UMBRAL_SIMILITUD_NODO: float = Field(default=0.30, validation_alias="UMBRAL_SIMILITUD_NODO")
    MAX_SECCIONES_POR_DOCUMENTO: int = Field(default=2, validation_alias="MAX_SECCIONES_POR_DOCUMENTO")
    RESERVA_MINIMA_POR_DOMINIO: int = Field(default=1, validation_alias="RESERVA_MINIMA_POR_DOMINIO")
    MAX_ITEMS_RUTA_JERARQUICA: int = Field(default=3, validation_alias="MAX_ITEMS_RUTA_JERARQUICA")
    MAX_LONGITUD_ITEM_RUTA: int = Field(default=120, validation_alias="MAX_LONGITUD_ITEM_RUTA")

    MAX_CARACTERES_CONTENIDO_SECCION: int = Field(default=6000, validation_alias="MAX_CARACTERES_CONTENIDO_SECCION")

    # ==========================================================================
    # 5. ARTEFACTOS Y SALIDAS JSON
    # ==========================================================================
    @property
    def FILE_ISO_EXTRACCION(self) -> Path:
        return self.SALIDA_JSON_DIR / "documentos_iso_extraccion.json"

    @property
    def FILE_LEYES_EXTRACCION(self) -> Path:
        return self.SALIDA_JSON_DIR / "documentos_leyes_extraccion.json"

    @property
    def FILE_ISO_CLASIFICADO(self) -> Path:
        return self.SALIDA_JSON_DIR / "documentos_iso_clasificado_llm.json"

    @property
    def FILE_LEYES_CLASIFICADO(self) -> Path:
        return self.SALIDA_JSON_DIR / "documentos_leyes_clasificado_llm.json"

    @property
    def FILE_GRAFO_JSON(self) -> Path:
        return self.SALIDA_JSON_DIR / "grafo_nodos_subnodos_graphrag.json"

    @property
    def FILE_EMBEDDINGS_JSON(self) -> Path:
        return self.SALIDA_JSON_DIR / "embeddings_llm.json"

    @property
    def FILE_TAXONOMIA_DESCUBIERTA(self) -> Path:
        return self.SALIDA_JSON_DIR / "taxonomia_descubierta.json"


    @property
    def INPUT_FILES_MAP(self) -> Dict[str, Path]:
        return {
            "ISO": self.FILE_ISO_EXTRACCION,
            "LEYES": self.FILE_LEYES_EXTRACCION,
        }

    @property
    def RUTAS_CATEGORIAS(self) -> List[Dict[str, Path]]:
        return [
            {
                "categoria": "ISOS",
                "input_dir": self.ARCHIVOS_DIR / "ISOS" / "pdf",
                "output_dir": self.ARCHIVOS_DIR / "ISOS" / "md",
            },
            {
                "categoria": "LEYES",
                "input_dir": self.ARCHIVOS_DIR / "LEYES" / "pdf",
                "output_dir": self.ARCHIVOS_DIR / "LEYES" / "md",
            },
        ]

    # ==========================================================================
    # 6. MÉTODOS Y PROPIEDADES AUXILIARES
    # ==========================================================================
    @property
    def produccion_backups_dir(self) -> Path:
        return self.DB_DIR / "backups"

    @property
    def GEMINI_MODELS(self) -> List[str]:
        return [self.GEMINI_MODEL_1, self.GEMINI_MODEL_2]

    def ensure_dirs(self) -> None:
        self.DB_DIR.mkdir(parents=True, exist_ok=True)
        self.JSON_INPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.SALIDA_JSON_DIR.mkdir(parents=True, exist_ok=True)
        self.ARCHIVOS_DIR.mkdir(parents=True, exist_ok=True)
        self.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    def validate_keys(self) -> None:
        if not self.DEEPSEEK_API_KEY and not self.GEMINI_API_KEY:
            raise EnvironmentError(
                "Debe proporcionar al menos una API Key (DEEPSEEK_API_KEY o GEMINI_API_KEY) en el archivo .env"
            )


settings = Settings()
