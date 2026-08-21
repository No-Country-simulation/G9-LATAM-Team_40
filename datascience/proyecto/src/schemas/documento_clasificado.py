from pydantic import BaseModel, Field


# ============================================================
# ETAPA 1 — DESCUBRIMIENTO DE TAXONOMÍA
# ============================================================

class CategoriaDescubierta(BaseModel):
    nombre: str = Field(
        description="Nombre conceptual claro, 2-5 palabras, sin números."
    )
    descripcion: str = Field(
        description="Una frase describiendo qué cubre esta categoría."
    )


class TaxonomiaDescubierta(BaseModel):
    categorias: list[CategoriaDescubierta]


# ============================================================
# ETAPA 2 — CLASIFICACIÓN
# ============================================================

class CategoriaAsignada(BaseModel):
    categoria: str = Field(
        description=(
            "Nombre exacto de una categoría existente en la taxonomía "
            "o una nueva si ninguna aplica."
        )
    )

    confianza: float = Field(
        ge=0.0,
        le=1.0,
        description="Confianza entre 0.0 y 1.0."
    )

    palabras_claves: list[str] = Field(
        default_factory=list,
        description=(
            "Entre 3 y 8 términos o frases breves extraídos "
            "exclusivamente del título y títulos de secciones del documento "
            "que justifican la asignación de esta categoría."
        )
    )

    justificacion: str = Field(
        default="",
        description=(
            "Justificación breve basada únicamente en el título "
            "y títulos de secciones."
        )
    )

class ClasificacionDocumento(BaseModel):
    documento_id: str = Field(
        description="ID exacto del documento."
    )
    categorias_asignadas: list[CategoriaAsignada] = Field(
        default_factory=list
    )


class LoteClasificado(BaseModel):
    clasificaciones: list[ClasificacionDocumento]


# ============================================================
# SALIDA FINAL
# ============================================================

class CategoriaMetadatos(BaseModel):
    cluster_id: str
    categoria: str
    confianza: float


class EtiquetaClasificacion(BaseModel):
    run_id: str
    taxonomia_run_id: str
    modelo_llm: str
    tipo_documento: str
    clasificaciones: list[CategoriaMetadatos]
    revisar_manual: bool