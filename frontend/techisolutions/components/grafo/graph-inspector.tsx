"use client"

import type {
  GraphExplorerCategory,
  GraphExplorerChild,
  GraphStats,
} from "@/lib/graph-data"
import styles from "@/components/grafo/graph-observatory.module.css"

export interface GraphInspectorProps {
  stats: GraphStats
  category: GraphExplorerCategory | null
  child: GraphExplorerChild | null
  onSelectChild: (childId: string) => void
}

function confidenceLabel(confidence: number): string {
  return `${Math.round(confidence * 100)}% confianza`
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

function Summary({ stats }: { stats: GraphStats }) {
  return (
    <div className="space-y-4">
      <p className="text-sm leading-relaxed text-foreground">
        Selecciona una categoría para abrir sus subnodos. El canvas muestra el
        mapa relacional y este inspector conserva el contexto completo.
      </p>
      <div className="border-y border-border/70 py-2">
        <MetricRow label="Categorías N1" value={stats.categories} />
        <MetricRow label="Subnodos N2" value={stats.subcategories} />
        <MetricRow label="Relaciones N3" value={stats.relations} />
        <MetricRow label="Documentos únicos" value={stats.documents} />
      </div>
      <div>
        <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
          Lectura del plano
        </p>
        <div className="space-y-2 text-xs text-muted-foreground">
          <p>
            <span className="font-semibold text-institutional">N1</span> ·
            baliza de categoría y punto de expansión.
          </p>
          <p>
            <span className="font-semibold text-stamp-red">N2</span> · subnodo
            seleccionado dentro de la categoría activa.
          </p>
          <p>Las relaciones N3 se leen aquí, sin saturar el campo cartográfico.</p>
        </div>
      </div>
    </div>
  )
}

function CategoryInspector({
  category,
  onSelectChild,
}: {
  category: GraphExplorerCategory
  onSelectChild: (childId: string) => void
}) {
  return (
    <div className="space-y-4">
      <div>
        <p className={styles.workspaceKicker}>Categoría N1</p>
        <h3 className="mt-1 text-xl font-bold leading-tight text-institutional">
          {category.title}
        </h3>
        <p className="mt-2 font-mono text-xs text-stamp-red">
          {confidenceLabel(category.confidence)}
        </p>
      </div>
      <p className="text-sm leading-relaxed text-foreground">
        {category.description || "Esta categoría no tiene una descripción registrada."}
      </p>
      <div className="border-y border-border/70 py-2">
        <MetricRow label="Subnodos N2" value={category.childCount} />
        <MetricRow label="Secciones" value={category.sectionCount} />
        <MetricRow label="Documentos únicos" value={category.documentCount} />
        <MetricRow label="Relaciones N3" value={category.relationCount} />
      </div>
      <div>
        <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
          Abrir subnodo
        </p>
        {category.children.length === 0 ? (
          <p className="text-xs text-muted-foreground">Sin subnodos registrados.</p>
        ) : (
          <ul className="space-y-1">
            {category.children.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => onSelectChild(item.id)}
                  className="w-full border border-border px-3 py-2 text-left text-sm font-semibold text-institutional transition-colors hover:border-institutional hover:bg-sst-yellow/15 focus-visible:bg-sst-yellow/15"
                >
                  <span className="block leading-tight">{item.title}</span>
                  <span className="mt-1 block font-mono text-[10px] font-normal text-muted-foreground">
                    {item.documentCount} docs. · {item.relationCount} rel.
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
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
        Documento: {relation.documento_id || "—"}
        <br />
        Sección: {relation.titulo_seccion || "—"}
        <br />
        Grupo: {relation.groupTitle || relation.groupId}
      </p>
    </li>
  )
}

function ChildInspector({
  category,
  child,
}: {
  category: GraphExplorerCategory | null
  child: GraphExplorerChild
}) {
  return (
    <div className="space-y-4">
      <div>
        <p className={styles.workspaceKicker}>Subnodo N2</p>
        <h3 className="mt-1 text-xl font-bold leading-tight text-institutional">
          {child.title}
        </h3>
        <p className="mt-2 font-mono text-[10px] text-muted-foreground">
          ID {child.id}
        </p>
      </div>
      <div className="border-y border-border/70 py-2 text-sm">
        <p>
          Padre: <strong className="text-institutional">{category?.title ?? child.parentId}</strong>
        </p>
        <p className="mt-1 font-mono text-xs text-muted-foreground">
          {child.documentCount} documentos únicos · {child.sectionCount} secciones · {child.relationCount} relaciones
        </p>
      </div>
      <div>
        <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
          Documentos únicos
        </p>
        {child.documentIds.length === 0 ? (
          <p className="text-xs text-muted-foreground">Sin documentos asociados.</p>
        ) : (
          <ul className="space-y-1">
            {child.documentIds.map((documentId) => (
              <li
                key={documentId}
                className="border-l-2 border-sst-yellow px-2 font-mono text-[10px] text-foreground"
              >
                {documentId}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div>
        <p className="mb-2 font-mono text-[10px] font-bold uppercase tracking-wider text-institutional">
          Relaciones N3 ({child.relationCount})
        </p>
        {child.relations.length === 0 ? (
          <p className="text-xs text-muted-foreground">
            Sin relaciones semánticas registradas para este subnodo.
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
      </div>
    </div>
  )
}

export function GraphInspector({
  stats,
  category,
  child,
  onSelectChild,
}: GraphInspectorProps) {
  return (
    <aside className={styles.panel} aria-labelledby="graph-inspector-heading">
      <div className={styles.panelHeader}>
        <p className={styles.workspaceKicker}>Registro de evidencia</p>
        <h2
          id="graph-inspector-heading"
          className="mt-1 text-base font-bold text-institutional"
        >
          Inspector
        </h2>
      </div>
      <div className={`${styles.panelBody} overflow-y-auto`}>
        {child ? (
          <ChildInspector category={category} child={child} />
        ) : category ? (
          <CategoryInspector category={category} onSelectChild={onSelectChild} />
        ) : (
          <Summary stats={stats} />
        )}
      </div>
    </aside>
  )
}
