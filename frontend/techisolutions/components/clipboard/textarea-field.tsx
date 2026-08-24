import { cn } from "@/lib/utils"

interface TextAreaFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  error?: string
  hint?: string
  required?: boolean
  disabled?: boolean
  rows?: number
  placeholder?: string
}

export function TextAreaField({
  id,
  label,
  value,
  onChange,
  error,
  hint,
  required,
  disabled,
  rows = 6,
  placeholder,
}: TextAreaFieldProps) {
  return (
    <div className="space-y-1.5">
      <label
        htmlFor={id}
        className="block font-mono text-[10px] font-bold uppercase tracking-wider text-institutional"
      >
        {label}
        {required ? (
          <span className="text-stamp-red" aria-hidden> *</span>
        ) : null}
      </label>
      <textarea
        id={id}
        name={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        disabled={disabled}
        rows={rows}
        placeholder={placeholder}
        aria-invalid={error ? true : undefined}
        aria-describedby={
          error ? `${id}-error` : hint ? `${id}-hint` : undefined
        }
        className={cn(
          "w-full resize-y border-2 bg-background px-3 py-2.5 text-sm leading-relaxed text-foreground outline-none transition-colors",
          "placeholder:text-muted-foreground/70",
          "focus-visible:border-carbon focus-visible:ring-2 focus-visible:ring-carbon/25",
          "disabled:cursor-not-allowed disabled:opacity-60",
          error
            ? "border-stamp-red focus-visible:border-stamp-red focus-visible:ring-stamp-red/20"
            : "border-border"
        )}
      />
      {hint && !error ? (
        <p id={`${id}-hint`} className="text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p
          id={`${id}-error`}
          role="alert"
          className="text-xs font-medium text-stamp-red"
        >
          {error}
        </p>
      ) : null}
    </div>
  )
}
