"use client"

import type {
  GraphExplorerCategory,
  GraphExplorerChild,
} from "@/lib/graph-data"
import styles from "@/components/grafo/graph-observatory.module.css"

export interface GraphInspectorProps {
  category: GraphExplorerCategory | null
  child: GraphExplorerChild | null
}

function confidenceLabel(confidence: number): string {
  return `${Math.round(confidence * 100)}%`
}

function MetricRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="border-b border-border/70 py-2 last:border-b-0">
      <span className="font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
        {label}
      </span>
      <strong className="ml-2 font-mono text-sm text-institutional">{value}</strong>
    </div>
  )
}

function EmptyInspector() {
  return (
    <div className="space-y-3">
      <p className="text-sm leading-relaxed text-foreground">
        Selecciona una categoría o un tema en el índice o en el plano.
      </p>
      <p className="text-sm leading-relaxed text-muted-foreground">
        La ficha muestra la descripción, las fuentes y las conexiones del
        elemento elegido.
      </p>
    </div>
  )
}

function CategoryInspector({ category }: { category: GraphExplorerCategory }) {
  return (
    <div className="space-y-4">
      <p className="text-sm leading-relaxed text-foreground">
        {category.description || "Esta categoría no tiene una descripción registrada."}
      </p>
      <p className="font-mono text-xs text-stamp-red">
        Confianza de clasificación: {confidenceLabel(category.confidence)}
      </p>
      <div className="border-y border-border/70 py-2">
        <MetricRow label="Temas" value={category.childCount} />
        <MetricRow label="Secciones" value={category.sectionCount} />
        <MetricRow label="Documentos" value={category.documentCount} />
        <MetricRow label="Conexiones" value={category.relationCount} />
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">
        Elige un tema en el índice o en el plano para revisar sus fuentes.
      </p>
    </div>
  )
}

type DocumentSections = {
  documentId: string
  titles: string[]
}

function groupSectionsByDocument(
  child: GraphExplorerChild
): DocumentSections[] {
  const grouped = new Map<string, string[]>()

  for (const section of child.sections) {
    const documentId = section.documento_id || "—"
    const titles = grouped.get(documentId) ?? []
    const title = section.titulo || "—"
    if (!titles.includes(title)) titles.push(title)
    grouped.set(documentId, titles)
  }

  for (const documentId of child.documentIds) {
    if (!grouped.has(documentId)) grouped.set(documentId, [])
  }

  return [...grouped.entries()].map(([documentId, titles]) => ({
    documentId,
    titles,
  }))
}

function SourcesSection({ child }: { child: GraphExplorerChild }) {
  const grouped = groupSectionsByDocument(child)

  return (
    <section>
      <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
        Fuentes
      </p>
      {child.documentIds.length === 0 ? (
        <p className="text-xs text-muted-foreground">
          No hay documentos asociados a este tema.
        </p>
      ) : (
        <ul className="space-y-3">
          {grouped.map((document) => (
            <li key={document.documentId}>
              <p className="border-l-2 border-sst-yellow px-2 font-mono text-[10px] text-foreground">
                {document.documentId}
              </p>
              {document.titles.length > 0 ? (
                <ul className="mt-1 space-y-1 pl-4 text-xs text-muted-foreground">
                  {document.titles.map((title) => (
                    <li key={`${document.documentId}-${title}`}>{title}</li>
                  ))}
                </ul>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {child.sections.length === 0 ? (
        <p className="mt-3 text-xs text-muted-foreground">
          No hay secciones asociadas a este tema.
        </p>
      ) : null}
    </section>
  )
}

function RelationRow({
  relation,
}: {
  relation: GraphExplorerChild["relations"][number]
}) {
  return (
    <li className="border-b border-border/70 pb-3 last:border-b-0 last:pb-0">
      <p className="text-sm leading-relaxed">
        <span className="font-semibold text-institutional">{relation.sujeto}</span>{" "}
        <span className="font-mono text-[10px] font-bold uppercase text-stamp-red">
          → {relation.relacion} →
        </span>{" "}
        <span className="text-foreground">{relation.objeto}</span>
      </p>
      <p className="mt-1 font-mono text-[10px] leading-relaxed text-muted-foreground">
        Fuente: {relation.titulo_seccion || "—"} · {relation.documento_id || "—"}
        <br />
        Agrupación: {relation.groupTitle || relation.groupId}
      </p>
    </li>
  )
}

function ChildInspector({
  category,
  child,
}: {
  category: GraphExplorerCategory
  child: GraphExplorerChild
}) {
  return (
    <div className="space-y-4">
      <p className="text-sm">
        Categoría: <strong className="text-institutional">{category.title}</strong>
      </p>
      <p className="font-mono text-xs text-muted-foreground">
        {child.documentCount} documentos · {child.sectionCount} secciones ·{" "}
        {child.relationCount} conexiones
      </p>
      <SourcesSection child={child} />
      <section>
        <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
          Conexiones encontradas ({child.relationCount})
        </p>
        {child.relations.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            No se encontraron conexiones semánticas para este tema.
          </p>
        ) : (
          <ul className="space-y-3">
            {child.relations.map((relation, index) => (
              <RelationRow
                key={`${relation.groupId}-${relation.documento_id}-${index}`}
                relation={relation}
              />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

export function GraphInspector({
  category,
  child,
}: GraphInspectorProps) {
  const heading = child?.title ?? category?.title ?? "Sin selección"

  return (
    <aside className={styles.ficha} aria-labelledby="graph-inspector-heading">
      <div className={styles.panelHeader}>
        <p className={styles.kicker}>Ficha</p>
        <h2
          id="graph-inspector-heading"
          className="mt-1 text-base font-bold text-institutional"
        >
          {heading}
        </h2>
        {category ? (
          <p className={styles.route}>
            <span>{category.title}</span>
            {child ? (
              <>
                <span aria-hidden> / </span>
                <span className={styles.routeCurrent}>{child.title}</span>
              </>
            ) : null}
          </p>
        ) : (
          <p className={`${styles.route} ${styles.routeCurrent}`}>
            Esperando selección
          </p>
        )}
      </div>
      <div className={`${styles.panelBody} overflow-y-auto`}>
        {child && category ? (
          <ChildInspector category={category} child={child} />
        ) : category ? (
          <CategoryInspector category={category} />
        ) : (
          <EmptyInspector />
        )}
      </div>
    </aside>
  )
}
