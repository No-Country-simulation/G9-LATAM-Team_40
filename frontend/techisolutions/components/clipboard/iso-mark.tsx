import { cn } from "@/lib/utils"

interface IsoMarkProps {
  className?: string
  /** Compact for header chrome; default for hero */
  size?: "sm" | "md"
}

/**
 * Escudo estilizado alusivo a inspección SST / ISO 45001.
 * No es el logo oficial de ISO — marca propia del producto.
 */
export function IsoMark({ className, size = "md" }: IsoMarkProps) {
  const dim = size === "sm" ? "size-10" : "size-16 sm:size-[4.5rem]"

  return (
    <svg
      className={cn(dim, "shrink-0 text-institutional", className)}
      viewBox="0 0 72 72"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Marca de inspección ISO 45001"
    >
      <path
        d="M36 4L62 16V36C62 50 50 62 36 68C22 62 10 50 10 36V16L36 4Z"
        fill="var(--card)"
        stroke="currentColor"
        strokeWidth="2.5"
      />
      <path
        d="M36 12L54 20V36C54 46 46 55 36 60C26 55 18 46 18 36V20L36 12Z"
        stroke="currentColor"
        strokeWidth="1.5"
        opacity="0.35"
      />
      <text
        x="36"
        y="34"
        textAnchor="middle"
        fill="currentColor"
        fontFamily="ui-monospace, monospace"
        fontSize="11"
        fontWeight="700"
        letterSpacing="0.06em"
      >
        ISO
      </text>
      <text
        x="36"
        y="48"
        textAnchor="middle"
        fill="currentColor"
        fontFamily="ui-monospace, monospace"
        fontSize="9"
        fontWeight="700"
        letterSpacing="0.04em"
      >
        45001
      </text>
      <rect
        x="22"
        y="52"
        width="28"
        height="4"
        fill="var(--sst-yellow)"
        stroke="currentColor"
        strokeWidth="1"
      />
    </svg>
  )
}

interface ApprovalStampProps {
  className?: string
}

/** Sello de evidencia para el análisis GraphRAG. */
export function ApprovalStamp({ className }: ApprovalStampProps) {
  return (
    <svg
      className={cn("size-16 text-stamp-red sm:size-20", className)}
      viewBox="0 0 80 80"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden
    >
      <circle
        cx="40"
        cy="40"
        r="34"
        stroke="currentColor"
        strokeWidth="3"
        strokeDasharray="4 3"
        opacity="0.9"
      />
      <circle cx="40" cy="40" r="28" stroke="currentColor" strokeWidth="2" />
      <text
        x="40"
        y="36"
        textAnchor="middle"
        fill="currentColor"
        fontFamily="ui-monospace, monospace"
        fontSize="9"
        fontWeight="700"
        letterSpacing="0.12em"
      >
        GRAPHRAG
      </text>
      <text
        x="40"
        y="50"
        textAnchor="middle"
        fill="currentColor"
        fontFamily="ui-monospace, monospace"
        fontSize="10"
        fontWeight="700"
      >
        OK
      </text>
    </svg>
  )
}
