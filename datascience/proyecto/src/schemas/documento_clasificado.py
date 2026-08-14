"""Esquemas de datos Pydantic para la Etapa 1 y Etapa 2."""

from pydantic import BaseModel, Field, model_validator


# --- Etapa 1: Descubrimiento ---
class CategoriaDescubierta(BaseModel):
    nombre: str = Field(description="Nombre conceptual claro, 2-5 palabras, sin números.")
    descripcion: str = Field(description="1 frase describiendo qué cubre esta categoría.")


class TaxonomiaDescubierta(BaseModel):
    categorias: list[CategoriaDescubierta]


# --- Etapa 2: Clasificación en Producción ---
class ClasificacionDocumento(BaseModel):
    documento_id: str
    categorias_asignadas: list[str] = Field(
        description="Nombres EXACTOS de la lista dada, los que apliquen."
    )
    confianzas: list[float] = Field(
        description="Una confianza (0.0-1.0) por cada categoría, mismo orden."
    )


class ClasificacionDocumento(BaseModel):
    documento_id: str = Field(default="desconocido")
    categorias_asignadas: list[str] = Field(default_factory=list)
    confianzas: list[float] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def rellenar_campos_faltantes(cls, data):
        if isinstance(data, dict):
            # Si el LLM no mandó confianzas, les ponemos un valor por defecto basado en la cantidad de categorías
            if "confianzas" not in data or not data["confianzas"]:
                num_cats = len(data.get("categorias_asignadas", []))
                data["confianzas"] = [0.8] * num_cats
        return data

class LoteClasificado(BaseModel):
    clasificaciones: list[ClasificacionDocumento]


class CategoriaMetadatos(BaseModel):
    cluster_id: str
    concepto: str
    categoria: str
    confianza: float


class EtiquetaClasificacion(BaseModel):
    run_id: str
    fecha_procesado: str
    clasificaciones: list[CategoriaMetadatos]
    revisar_manual: bool
    metodo: str = "LLM_puro_titulos"
    modelo_llm: str
    taxonomia_run_id: str