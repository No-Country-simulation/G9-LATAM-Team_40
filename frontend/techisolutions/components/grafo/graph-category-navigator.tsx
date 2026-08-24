"use client"

import type { ChangeEvent } from "react"

import type {
  GraphExplorerCategory,
  GraphExplorerChild,
} from "@/lib/graph-data"
import styles from "@/components/grafo/graph-observatory.module.css"

export interface GraphCategoryNavigatorProps {
  index: GraphExplorerCategory[]
  filteredIndex: GraphExplorerCategory[]
  query: string
  selectedCategoryId: string | null
  selectedNodeId: string | null
  onQueryChange: (query: string) => void
  onSelectCategory: (categoryId: string) => void
  onSelectChild: (childId: string) => void
}

function confidenceLabel(confidence: number): string {
  return `${Math.round(confidence * 100)}%`
}

function Counter({ label, value }: { label: string; value: number }) {
  return (
    <span className="font-mono text-[10px] text-muted-foreground">
      {value} {label}
    </span>
  )
}

function ChildButton({
  child,
  selected,
  onSelect,
}: {
  child: GraphExplorerChild
  selected: boolean
  onSelect: () => void
}) {
  return (
    <li>
      <button
        type="button"
        aria-current={selected ? "true" : undefined}
        onClick={onSelect}
        className={`w-full border-l-2 px-3 py-2 text-left transition-colors hover:bg-sst-yellow/15 focus-visible:bg-sst-yellow/15 ${selected ? "border-stamp-red bg-sst-yellow/20" : "border-border/70"}`}
      >
        <span className="block text-sm font-semibold leading-tight text-institutional">
          {child.title}
        </span>
        <span className="mt-1 flex flex-wrap gap-x-2 gap-y-0.5">
          <Counter label="secc." value={child.sectionCount} />
          <Counter label="docs." value={child.documentCount} />
          <Counter label="rel." value={child.relationCount} />
        </span>
      </button>
    </li>
  )
}

export function GraphCategoryNavigator({
  index,
  filteredIndex,
  query,
  selectedCategoryId,
  selectedNodeId,
  onQueryChange,
  onSelectCategory,
  onSelectChild,
}: GraphCategoryNavigatorProps) {
  const activeCategory = filteredIndex.find(
    (category) => category.id === selectedCategoryId
  )

  function handleQueryChange(event: ChangeEvent<HTMLInputElement>) {
    onQueryChange(event.target.value)
  }

  return (
    <section className={styles.panel} aria-labelledby="graph-category-heading">
      <div className={styles.panelHeader}>
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className={styles.workspaceKicker}>Navegador de conceptos</p>
            <h2
              id="graph-category-heading"
              className="mt-1 text-base font-bold text-institutional"
            >
              Categorías y subnodos
            </h2>
          </div>
          <span className="font-mono text-[10px] text-muted-foreground">
            {filteredIndex.length}/{index.length}
          </span>
        </div>
        <label className="mt-3 block">
          <span className="sr-only">Buscar categoría, sección o documento</span>
          <input
            type="search"
            value={query}
            onChange={handleQueryChange}
            placeholder="Buscar categoría, sección o documento"
            className="w-full border-2 border-institutional bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground"
          />
        </label>
      </div>

      <div className={styles.panelBody}>
        {filteredIndex.length === 0 ? (
          <p className="border border-dashed border-border p-4 text-sm text-muted-foreground">
            No hay conceptos que coincidan con esta búsqueda.
          </p>
        ) : (
          <ul className="space-y-1" aria-label="Categorías del grafo">
            {filteredIndex.map((category) => {
              const selected = category.id === selectedCategoryId
              return (
                <li key={category.id}>
                  <button
                    type="button"
                    aria-current={selected ? "true" : undefined}
                    onClick={() => onSelectCategory(category.id)}
                    className={`w-full border-2 px-3 py-2 text-left transition-colors hover:border-institutional hover:bg-sst-yellow/10 focus-visible:bg-sst-yellow/10 ${selected ? "border-institutional bg-sst-yellow/20" : "border-transparent"}`}
                  >
                    <span className="flex items-start justify-between gap-2">
                      <span className="min-w-0 text-sm font-bold leading-tight text-institutional">
                        {category.title}
                      </span>
                      <span className="shrink-0 font-mono text-[10px] font-bold text-stamp-red">
                        {confidenceLabel(category.confidence)}
                      </span>
                    </span>
                    <span className="mt-1 flex flex-wrap gap-x-2 gap-y-0.5">
                      <Counter label="N2" value={category.childCount} />
                      <Counter label="docs." value={category.documentCount} />
                      <Counter label="rel." value={category.relationCount} />
                    </span>
                  </button>

                  {selected && activeCategory ? (
                    <ul
                      className="mt-1 space-y-0.5 border-l border-institutional/30 pl-2"
                      aria-label={`Subnodos de ${category.title}`}
                    >
                      {activeCategory.children.map((child) => (
                        <ChildButton
                          key={child.id}
                          child={child}
                          selected={child.id === selectedNodeId}
                          onSelect={() => onSelectChild(child.id)}
                        />
                      ))}
                    </ul>
                  ) : null}
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </section>
  )
}
