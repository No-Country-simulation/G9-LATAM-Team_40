"use client"

import dynamic from "next/dynamic"
import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type { ForceGraphMethods } from "react-force-graph-2d"

import {
  hashColor,
  type GraphData,
  type GraphNode,
} from "@/lib/graph-data"
import styles from "@/components/grafo/graph-observatory.module.css"

const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full min-h-[420px] items-center justify-center bg-[#10283d]">
      <p className="font-mono text-xs text-[#eaf1f4]">Cargando plano…</p>
    </div>
  ),
})

type ForceNode = GraphNode & { x?: number; y?: number }
type GraphApi = ForceGraphMethods

export interface GraphObservatoryCanvasProps {
  data: GraphData
  selectedNodeId: string | null
  selectedCategoryId: string | null
  reduceMotion: boolean
  onSelectNode: (node: GraphNode) => void
  onClearNode: () => void
  onShowCategories: () => void
}

function isPositioned(node: ForceNode | undefined): node is ForceNode & { x: number; y: number } {
  return Boolean(node && Number.isFinite(node.x) && Number.isFinite(node.y))
}

function drawDiamond(
  context: CanvasRenderingContext2D,
  x: number,
  y: number,
  radius: number
) {
  context.beginPath()
  context.moveTo(x, y - radius)
  context.lineTo(x + radius, y)
  context.lineTo(x, y + radius)
  context.lineTo(x - radius, y)
  context.closePath()
}

function drawField(context: CanvasRenderingContext2D) {
  const width = context.canvas.width
  const height = context.canvas.height
  context.save()
  context.setTransform(1, 0, 0, 1, 0, 0)
  context.fillStyle = "#10283d"
  context.fillRect(0, 0, width, height)

  const minor = 48
  const major = minor * 4
  context.lineWidth = 1
  for (let x = 0; x <= width; x += minor) {
    context.strokeStyle = x % major === 0 ? "rgba(142,181,207,.2)" : "rgba(142,181,207,.12)"
    context.beginPath()
    context.moveTo(x + 0.5, 0)
    context.lineTo(x + 0.5, height)
    context.stroke()
  }
  for (let y = 0; y <= height; y += minor) {
    context.strokeStyle = y % major === 0 ? "rgba(142,181,207,.2)" : "rgba(142,181,207,.12)"
    context.beginPath()
    context.moveTo(0, y + 0.5)
    context.lineTo(width, y + 0.5)
    context.stroke()
  }

  const centerX = width / 2
  const centerY = height / 2
  context.strokeStyle = "rgba(234,241,244,.18)"
  context.lineWidth = 1
  for (const radius of [80, 160, 240]) {
    context.beginPath()
    context.arc(centerX, centerY, radius, 0, Math.PI * 2)
    context.stroke()
  }
  context.strokeStyle = "rgba(240,196,25,.28)"
  context.beginPath()
  context.moveTo(centerX, 0)
  context.lineTo(centerX, height)
  context.moveTo(0, centerY)
  context.lineTo(width, centerY)
  context.stroke()
  context.restore()
}

export function GraphObservatoryCanvas({
  data,
  selectedNodeId,
  selectedCategoryId,
  reduceMotion,
  onSelectNode,
  onClearNode,
  onShowCategories,
}: GraphObservatoryCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const graphRef = useRef<GraphApi | undefined>(undefined)
  const fitPendingRef = useRef(true)
  const focusPendingRef = useRef<string | null>(selectedNodeId)
  const [dims, setDims] = useState({ width: 640, height: 560 })
  const [hoverId, setHoverId] = useState<string | null>(null)
  const [zoomScale, setZoomScale] = useState(1)

  useEffect(() => {
    const element = containerRef.current
    if (!element || typeof ResizeObserver === "undefined") return
    const observer = new ResizeObserver(([entry]) => {
      const box = entry?.contentRect
      if (!box) return
      setDims({
        width: Math.max(280, Math.floor(box.width)),
        height: Math.max(420, Math.floor(box.height)),
      })
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])
  const graphShape = useMemo(
    () =>
      `${data.nodes.map((node) => node.id).join(",")}|${data.links
        .map((link) => `${link.source}->${link.target}`)
        .join(",")}`,
    [data]
  )

  useEffect(() => {
    fitPendingRef.current = true
  }, [graphShape, selectedCategoryId])

  useEffect(() => {
    focusPendingRef.current = selectedNodeId
  }, [selectedNodeId])

  const focusNode = useCallback(
    (node: ForceNode | undefined) => {
      const api = graphRef.current
      if (!api || !isPositioned(node)) return false
      const duration = reduceMotion ? 0 : 350
      api.centerAt(node.x, node.y, duration)
      api.zoom(Math.max(api.zoom(), 1.8), duration)
      focusPendingRef.current = null
      return true
    },
    [reduceMotion]
  )

  useEffect(() => {
    if (!selectedNodeId) return
    const node = data.nodes.find((item) => item.id === selectedNodeId) as ForceNode | undefined
    if (!focusNode(node)) focusPendingRef.current = selectedNodeId
  }, [data.nodes, focusNode, selectedNodeId])

  const handleEngineStop = useCallback(() => {
    const api = graphRef.current
    if (!api) return
    if (fitPendingRef.current) {
      api.zoomToFit(reduceMotion ? 0 : 450, 64)
      fitPendingRef.current = false
    }
    if (focusPendingRef.current) {
      const node = data.nodes.find((item) => item.id === focusPendingRef.current) as
        | ForceNode
        | undefined
      focusNode(node)
    }
  }, [data.nodes, focusNode, reduceMotion])

  const paintNode = useCallback(
    (node: object, context: CanvasRenderingContext2D, globalScale: number) => {
      const current = node as ForceNode
      const x = current.x ?? 0
      const y = current.y ?? 0
      const isSelected = current.id === selectedNodeId
      const isHovered = current.id === hoverId
      const isCategoryActive = current.kind === "n1" && current.id === selectedCategoryId
      const isActive = isSelected || isHovered || isCategoryActive
      const baseRadius = current.kind === "n1" ? 12 + current.val * 3 : 8 + current.val * 2
      const radius = baseRadius / Math.max(globalScale, 0.75)

      context.save()
      context.translate(x, y)
      context.lineWidth = (isActive ? 2.5 : 1.2) / globalScale

      if (current.kind === "n1") {
        context.beginPath()
        context.arc(0, 0, radius + 6 / globalScale, 0, Math.PI * 2)
        context.strokeStyle = isActive ? "#c0392b" : "rgba(234,241,244,.72)"
        context.stroke()
        context.beginPath()
        context.arc(0, 0, radius, 0, Math.PI * 2)
        context.fillStyle = "#eaf1f4"
        context.fill()
        context.strokeStyle = isActive ? "#f0c419" : "#eaf1f4"
        context.stroke()
        context.beginPath()
        context.arc(0, 0, Math.max(3, radius * 0.45), 0, Math.PI * 2)
        context.fillStyle = hashColor(current.categoryId)
        context.fill()
      } else {
        drawDiamond(context, 0, 0, radius)
        context.fillStyle = hashColor(current.categoryId)
        context.fill()
        context.strokeStyle = isActive ? "#c0392b" : "#eaf1f4"
        context.stroke()
      }

      const showLabel =
        current.kind === "n1" ||
        isSelected ||
        isHovered ||
        globalScale >= 1.6
      if (showLabel) {
        const label = current.kind === "n1" ? current.name : current.name
        const fontSize = (current.kind === "n1" ? 12 : 10) / globalScale
        context.font = `600 ${fontSize}px "Source Sans 3", system-ui, sans-serif`
        context.textAlign = "center"
        context.textBaseline = "top"
        context.fillStyle = "#eaf1f4"
        context.fillText(label, 0, radius + (current.kind === "n1" ? 12 : 8) / globalScale)
      }
      context.restore()
    },
    [hoverId, selectedCategoryId, selectedNodeId]
  )

  const paintPointerArea = useCallback(
    (node: object, color: string, context: CanvasRenderingContext2D, globalScale: number) => {
      const current = node as ForceNode
      const radius = (current.kind === "n1" ? 18 : 13) / Math.max(globalScale, 0.75)
      context.beginPath()
      if (current.kind === "n1") {
        context.arc(current.x ?? 0, current.y ?? 0, radius, 0, Math.PI * 2)
      } else {
        drawDiamond(context, current.x ?? 0, current.y ?? 0, radius)
      }
      context.fillStyle = color
      context.fill()
    },
    []
  )

  function zoomBy(factor: number) {
    const api = graphRef.current
    if (!api) return
    api.zoom(api.zoom() * factor, reduceMotion ? 0 : 220)
  }

  function fitGraph() {
    graphRef.current?.zoomToFit(reduceMotion ? 0 : 450, 64)
    fitPendingRef.current = false
  }

  function showCategories() {
    onShowCategories()
    graphRef.current?.centerAt(0, 0, reduceMotion ? 0 : 220)
    graphRef.current?.zoomToFit(reduceMotion ? 0 : 450, 64)
  }

  return (
    <div
      ref={containerRef}
      className={`${styles.canvasFrame} h-full`}
      role="img"
      aria-label="Canvas cartográfico del grafo GraphRAG. Usa el navegador paralelo para seleccionar categorías y subnodos."
    >
      <div className={styles.coordinate + " " + styles.coordinateNorth} aria-hidden>
        N 00° · E 00°
      </div>
      <div className={styles.coordinate + " " + styles.coordinateSouth} aria-hidden>
        CAMPO GRF · ESCALA {zoomScale.toFixed(1)}×
      </div>
      <div className={styles.canvasToolbar} role="toolbar" aria-label="Controles del canvas">
        <button type="button" className={styles.canvasTool} onClick={() => zoomBy(1.25)}>
          Acercar
        </button>
        <button type="button" className={styles.canvasTool} onClick={() => zoomBy(0.8)}>
          Alejar
        </button>
        <button type="button" className={styles.canvasTool} onClick={fitGraph}>
          Ajustar grafo
        </button>
        <button type="button" className={styles.canvasTool} onClick={showCategories}>
          Volver a categorías
        </button>
      </div>
      <div className={styles.canvasLegend} aria-hidden>
        <span className={styles.legendItem}>
          <span className={`${styles.legendMark} ${styles.legendMarkBeacon}`} /> N1 categoría
        </span>
        <span className={styles.legendItem}>
          <span className={`${styles.legendMark} ${styles.legendMarkDiamond}`} /> N2 subnodo
        </span>
      </div>
      <p className="sr-only">
        Las categorías son balizas de doble anillo. Los subnodos son rombos. Las flechas indican relación de pertenencia.
      </p>
      <ForceGraph2D
        ref={graphRef}
        width={dims.width}
        height={dims.height}
        graphData={data}
        nodeCanvasObject={paintNode}
        nodePointerAreaPaint={paintPointerArea}
        onRenderFramePre={drawField}
        linkColor={() => "rgba(142,181,207,.72)"}
        linkWidth={1.2}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowColor={() => "#eaf1f4"}
        linkDirectionalArrowRelPos={0.86}
        linkDirectionalParticles={0}
        cooldownTicks={reduceMotion ? 0 : 90}
        enableNodeDrag={!reduceMotion}
        onEngineStop={handleEngineStop}
        onZoom={(transform) => setZoomScale(transform.k)}
        onNodeClick={(node) => onSelectNode(node as GraphNode)}
        onNodeHover={(node) => setHoverId(node ? String((node as GraphNode).id) : null)}
        onBackgroundClick={onClearNode}
      />
    </div>
  )
}
