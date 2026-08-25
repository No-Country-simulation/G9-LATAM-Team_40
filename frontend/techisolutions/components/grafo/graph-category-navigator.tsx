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
  onReset: () => void
  onSelectCategory: (categoryId: string) => void
  onSelectChild: (childId: string) => void
}

function countLabel(
  value: number,
  singular: string,
  plural = `${singular}s`
): string {
  return `${value} ${value === 1 ? singular : plural}`
}

function SearchField({
  query,
  onQueryChange,
}: {
  query: string
  onQueryChange: (query: string) => void
}) {
  function handleQueryChange(event: ChangeEvent<HTMLInputElement>) {
    onQueryChange(event.target.value)
  }

  return (
    <label className={styles.searchField}>
      <span className={styles.searchLabel}>Buscar en el mapa</span>
      <input
        type="search"
        value={query}
        onChange={handleQueryChange}
        placeholder="Categoría, tema o documento"
        className="w-full border-2 border-institutional bg-card px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground"
      />
    </label>
  )
}

function CategoryRow({
  category,
  selected,
  onSelect,
}: {
  category: GraphExplorerCategory
  selected: boolean
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      aria-current={selected ? "true" : undefined}
      aria-expanded={selected}
      onClick={onSelect}
      className={`${styles.categoryRow} ${selected ? styles.categoryRowSelected : ""}`}
    >
      <span className="block text-left text-sm font-bold leading-tight text-institutional">
        {category.title}
      </span>
      <span className={styles.rowMeta}>
        {countLabel(category.childCount, "tema")} ·{" "}
        {countLabel(category.documentCount, "documento")}
      </span>
    </button>
  )
}

function TopicRow({
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
        className={`${styles.topicRow} ${selected ? styles.topicRowSelected : ""}`}
      >
        <span className="block text-left text-sm font-semibold leading-tight text-institutional">
          {child.title}
        </span>
        <span className={styles.rowMeta}>
          {countLabel(child.sectionCount, "sección", "secciones")} ·{" "}
          {countLabel(child.documentCount, "documento")} ·{" "}
          {countLabel(child.relationCount, "conexión", "conexiones")}
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
  onReset,
  onSelectCategory,
  onSelectChild,
}: GraphCategoryNavigatorProps) {
  const selectedCategory =
    index.find((category) => category.id === selectedCategoryId) ?? null
  const filteredSelected = filteredIndex.find(
    (category) => category.id === selectedCategoryId
  )
  const visibleChildren = filteredSelected?.children ?? []
  const noTopics = Boolean(selectedCategory && selectedCategory.children.length === 0)
  const noMatches = Boolean(
    selectedCategory &&
      !noTopics &&
      (filteredIndex.length === 0 || visibleChildren.length === 0)
  )

  return (
    <section className={styles.index} aria-labelledby="graph-index-heading">
      <div className={styles.panelHeader}>
        <p className={styles.kicker}>Índice</p>
        <h2
          id="graph-index-heading"
          className="mt-1 text-base font-bold text-institutional"
        >
          Categorías y temas
        </h2>
        {selectedCategory ? (
          <button type="button" onClick={onReset} className={`${styles.resetAction} mt-2`}>
            Ver todo el mapa
          </button>
        ) : null}
        <div className="mt-3">
          <SearchField query={query} onQueryChange={onQueryChange} />
        </div>
      </div>
      <div className={styles.panelBody}>
        {filteredIndex.length === 0 ? (
          <p className="border border-dashed border-border p-3 text-sm text-muted-foreground">
            {query && selectedCategory
              ? `No encontramos temas dentro de ${selectedCategory.title} con “${query}”.`
              : query
                ? `No encontramos categorías o temas con “${query}”. Prueba con otro término o identificador de documento.`
                : "Este mapa todavía no tiene categorías."}
          </p>
        ) : (
          <ul className={styles.categoryList} aria-label="Categorías">
            {filteredIndex.map((category) => {
              const selected = category.id === selectedCategoryId
              return (
                <li key={category.id}>
                  <CategoryRow
                    category={category}
                    selected={selected}
                    onSelect={() => onSelectCategory(category.id)}
                  />
                  {selected ? (
                    noTopics ? (
                      <p className="mt-2 border border-dashed border-border p-3 text-sm text-muted-foreground">
                        Esta categoría todavía no tiene temas asociados.
                      </p>
                    ) : noMatches ? (
                      <p className="mt-2 border border-dashed border-border p-3 text-sm text-muted-foreground">
                        No encontramos temas dentro de {category.title} con “
                        {query}”.
                      </p>
                    ) : (
                      <ul
                        className={styles.topicList}
                        aria-label={`Temas de ${category.title}`}
                      >
                        {visibleChildren.map((child) => (
                          <TopicRow
                            key={child.id}
                            child={child}
                            selected={child.id === selectedNodeId}
                            onSelect={() => onSelectChild(child.id)}
                          />
                        ))}
                      </ul>
                    )
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
