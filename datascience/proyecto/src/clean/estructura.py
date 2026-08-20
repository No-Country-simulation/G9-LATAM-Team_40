"""Motor de detección de jerarquía legal/temática: identifica títulos,
capítulos, artículos, decretos, leyes y numeración jerárquica (ISO/normativa), 
respetando reglas gramaticales de mayúsculas, saltos de línea y secuencia."""
from __future__ import annotations

import re

from .modelos import BloqueTexto, Seccion

PATRON_ARTICULO = re.compile(r"^(?:Art[ií]culo|Art\.)\s+\d+°?", re.I)
PATRON_NORMATIVA_LEGAL = re.compile(r"^(?:Decreto|Ley|Decreto-Ley|DFL|Resoluci[oó]n|Reglamento)\s+N?[úu]?m?\.?\s*\d+", re.I)
PATRON_TITULO_CAPITULO = re.compile(r"^(T[ií]tulo|Cap[ií]tulo|P[aá]rrafo|Secci[oó]n|Anexo|§)\s+([IVXLCDM]+|\d+)\b", re.I)
# Patrón mejorado para numeración tipo 1.1, 1.1.1 o A.1, B.2
PATRON_NUMERACION_JERARQUICA = re.compile(r"^(?:(\d+\.)+\d+|[A-Z]\.\d+(?:\.\d+)*)[\.\)]?\s+\S.*$")
PATRON_MAYUSCULAS_CORTAS = re.compile(r"^[A-ZÁÉÍÓÚÑ0-9][A-ZÁÉÍÓÚÑ0-9\s\.,\-:]{2,80}$")


def detectar_tipo_documento(muestra: str, cleaning_rules: dict) -> str:
    patrones = cleaning_rules.get("document_type_patterns", {})
    for tipo, clave in [
        ("LEY_CHILE", "ley_chile"), ("ISO_HSEQ", "iso_hseq"),
        ("PRESENTACION", "presentacion"), ("NORMATIVO", "normativo_extenso"),
    ]:
        if any(re.search(p, muestra, re.I) for p in patrones.get(clave, [])):
            return tipo
    return "GENERAL"


def _es_mayusculas_titulo(linea: str) -> bool:
    palabras = linea.split()
    return (
        linea == linea.upper()
        and 3 <= len(palabras) <= 10
        and not re.search(r"[\.\?\!]$", linea)
        and bool(PATRON_MAYUSCULAS_CORTAS.match(linea))
    )


def _nivel_numeracion(linea: str) -> int:
    m = re.match(r"^(\d+(?:\.\d+)*)[\.\)]?\s+", linea)
    if not m:
        return 3
    return min(m.group(1).count(".") + 1, 6)


class DetectorJerarquia:
    def __init__(self, cleaning_rules: dict | None = None, tipo_documento: str = "GENERAL"):
        cleaning_rules = cleaning_rules or {}
        self.tipo_documento = tipo_documento

        titulos_cfg = cleaning_rules.get("structural_titles", {})
        self._patrones_nivel2_cfg = [
            re.compile(rf"^{re.escape(kw)}\b", re.I) for kw in titulos_cfg.get("level_2", [])
        ]
        self._patrones_nivel3_cfg = [
            re.compile(rf"^{re.escape(kw)}\b", re.I) for kw in titulos_cfg.get("level_3", [])
        ]
        self._patrones_numeracion_cfg = [
            re.compile(p) for p in cleaning_rules.get("hierarchical_numbering", {}).values()
        ]

    def es_linea_estructural(self, linea: str) -> bool:
        limp = linea.strip()
        if not limp:
            return False

        # Regla gramatical anti-falsos positivos (evita oraciones rotas en minúscula)
        if not limp[0].isupper() and not limp[0].isdigit() and not limp.startswith("§"):
            return False

        if PATRON_ARTICULO.match(limp) or PATRON_NORMATIVA_LEGAL.match(limp) or PATRON_TITULO_CAPITULO.match(limp):
            return True
        if any(p.match(limp) for p in self._patrones_nivel2_cfg + self._patrones_nivel3_cfg):
            return True
        if self.tipo_documento in ("ISO_HSEQ", "NORMATIVO"):
            if any(p.match(limp) and len(limp.split()) <= 10 for p in self._patrones_numeracion_cfg):
                return True
        if PATRON_NUMERACION_JERARQUICA.match(limp) and len(limp.split()) <= 12:
            return True
        return _es_mayusculas_titulo(limp)

    def nivel_de(self, linea: str) -> int:
        limp = linea.strip()

        if any(p.match(limp) for p in self._patrones_nivel2_cfg):
            return 2
        if any(p.match(limp) for p in self._patrones_nivel3_cfg):
            return 3
        if PATRON_TITULO_CAPITULO.match(limp) or PATRON_ARTICULO.match(limp) or PATRON_NORMATIVA_LEGAL.match(limp):
            return 2
        if PATRON_NUMERACION_JERARQUICA.match(limp):
            return _nivel_numeracion(limp)
        
        return 3

    def segmentar(self, bloques: list[BloqueTexto]) -> list[Seccion]:
        secciones: list[Seccion] = []
        stack: list[tuple[int, str]] = []
        actual: Seccion | None = None

        def cerrar_actual():
            nonlocal actual
            if actual is not None:
                secciones.append(actual)
            actual = None

        for b in bloques:
            if b.es_titulo:
                nivel = self.nivel_de(b.texto)
                cerrar_actual()
                
                while stack and stack[-1][0] >= nivel:
                    stack.pop()
                    
                stack.append((nivel, b.texto))
                
                actual = Seccion(
                    titulo=b.texto,
                    nivel=nivel,
                    texto="",
                    linea_inicio=b.linea_inicio,
                    linea_fin=b.linea_fin,
                    ruta_jerarquica=[t for _, t in stack],
                )
            else:
                if actual is None:
                    actual = Seccion(
                        titulo="", nivel=1, texto="",
                        linea_inicio=b.linea_inicio, linea_fin=b.linea_fin,
                        ruta_jerarquica=[],
                    )
                actual.texto = f"{actual.texto}\n\n{b.texto}".strip()
                actual.linea_fin = b.linea_fin

        cerrar_actual()
        return [s for s in secciones if s.texto or s.titulo]