"""Reconstrucción gramatical de párrafos fragmentados por saltos de línea,
usando spaCy para decidir si un salto de línea es fin de oración real o un
corte artificial de la conversión (columna angosta, ancho de página, etc.)."""
from __future__ import annotations

import re
from typing import Callable, List

import spacy

from .modelos import BloqueTexto, LineaFuente


def _cargar_spacy(modelo: str = "es_core_news_sm") -> "spacy.language.Language":
    """Modelo liviano solo para segmentación de oraciones (sentencizer) — no
    hace falta el parser de dependencias completo (el de Etapa 1) para esta
    tarea, así que se desactiva todo lo demás para que sea rápido incluso
    sobre documentos largos. Si el modelo no está instalado, cae a un
    pipeline en blanco + sentencizer basado en reglas (más simple, pero
    funcional)."""
    try:
        nlp = spacy.load(modelo, disable=["ner", "lemmatizer", "tagger", "parser"])
    except OSError:
        nlp = spacy.blank("es")
    if "sentencizer" not in nlp.pipe_names:
        nlp.add_pipe("sentencizer")
    return nlp


class ReconstructorGramatical:
    def __init__(self, modelo_spacy: str = "es_core_news_sm", preservar_hifen: list[str] | None = None):
        self.nlp = _cargar_spacy(modelo_spacy)
        self.preservar_hifen = [p.lower() for p in (preservar_hifen or [])]

    def _fusionar_hifenacion(self, buffer: str, siguiente: str) -> tuple[str, bool]:
        """Si 'buffer' termina en guion de corte de palabra (word wrap), lo
        une con la siguiente línea sin espacio. No lo hace si el guion es
        parte de una palabra compuesta conocida (preservar_hifen)."""
        if not buffer.rstrip().endswith("-"):
            return buffer, False
        cola = buffer.rstrip().rsplit(" ", 1)[-1].lower()
        if any(p in cola for p in self.preservar_hifen):
            return buffer, False
        return buffer.rstrip()[:-1] + siguiente, True

    def _fin_de_oracion(self, texto: str) -> bool:
        """Usa spaCy para decidir si 'texto' termina una oración completa, en
        vez de asumirlo solo por puntuación (evita cortar antes de tiempo en
        abreviaturas tipo 'Art.', 'N°', etc.)."""
        doc = self.nlp(texto[-300:])  # ventana final basta, evita reprocesar todo el buffer cada vez
        oraciones = list(doc.sents)
        if not oraciones:
            return bool(re.search(r"[\.\?\!:;]\s*$", texto))
        return oraciones[-1].text.strip().endswith((".", "?", "!", ":", ";"))

    def reconstruir(
        self,
        lineas: List[LineaFuente],
        es_linea_estructural: Callable[[str], bool],
    ) -> List[BloqueTexto]:
        """Fusiona líneas fragmentadas en párrafos completos, preservando el
        rango [linea_inicio, linea_fin] de cada bloque resultante. Las líneas
        que 'es_linea_estructural' identifica como título nunca se fusionan
        con el párrafo anterior o siguiente."""
        resultado: List[BloqueTexto] = []
        buffer_texto = ""
        buffer_inicio: int | None = None
        buffer_fin: int | None = None

        def cerrar_buffer():
            nonlocal buffer_texto, buffer_inicio, buffer_fin
            if buffer_texto:
                resultado.append(BloqueTexto(
                    texto=buffer_texto.strip(),
                    linea_inicio=buffer_inicio,
                    linea_fin=buffer_fin,
                ))
            buffer_texto, buffer_inicio, buffer_fin = "", None, None

        for l in lineas:
            limp = l.texto.strip()
            if not limp:
                continue

            if es_linea_estructural(limp):
                cerrar_buffer()
                resultado.append(BloqueTexto(
                    texto=limp, linea_inicio=l.linea_original, linea_fin=l.linea_original,
                    es_titulo=True,
                ))
                continue

            if not buffer_texto:
                buffer_texto, buffer_inicio, buffer_fin = limp, l.linea_original, l.linea_original
                continue

            fusionado, hubo_hifen = self._fusionar_hifenacion(buffer_texto, limp)
            if hubo_hifen:
                buffer_texto = fusionado
                buffer_fin = l.linea_original
                continue

            if self._fin_de_oracion(buffer_texto):
                cerrar_buffer()
                buffer_texto, buffer_inicio, buffer_fin = limp, l.linea_original, l.linea_original
            else:
                buffer_texto = f"{buffer_texto} {limp}"
                buffer_fin = l.linea_original

        cerrar_buffer()
        return resultado
