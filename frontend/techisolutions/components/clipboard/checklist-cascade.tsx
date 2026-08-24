"use client"

import { useEffect, useRef, useState } from "react"

import { CheckCell } from "@/components/clipboard/form-elements"

interface ChecklistCascadeProps {
  steps: readonly string[]
}

export function ChecklistCascade({ steps }: ChecklistCascadeProps) {
  const rootRef = useRef<HTMLOListElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = rootRef.current
    if (!el) return

    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches
    if (reduceMotion) {
      const timer = window.setTimeout(() => setVisible(true), 0)
      return () => window.clearTimeout(timer)
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          setVisible(true)
          observer.disconnect()
        }
      },
      { threshold: 0.2 }
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <ol ref={rootRef} className="flex flex-col">
      {steps.map((step, index) => (
        <li
          key={step}
          className="relative flex gap-0 pb-8 last:pb-0"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? "translateY(0)" : "translateY(0.75rem)",
            transition:
              "opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1), transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)",
            transitionDelay: visible ? `${index * 90}ms` : "0ms",
          }}
        >
          {index < steps.length - 1 ? (
            <span
              className="absolute top-9 bottom-0 left-4 w-0.5 -translate-x-1/2 bg-institutional/25"
              aria-hidden
            />
          ) : null}
          <CheckCell
            checked={index < 2}
            number={index + 1}
            stepLabel={`Paso ${index + 1}`}
            label={step}
          />
        </li>
      ))}
    </ol>
  )
}
