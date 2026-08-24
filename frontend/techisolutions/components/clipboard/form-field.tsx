import { cn } from "@/lib/utils"

interface FormFieldProps {
  id: string
  label: string
  type?: "email" | "password" | "text"
  value: string
  onChange: (value: string) => void
  error?: string
  hint?: string
  required?: boolean
  autoComplete?: string
  disabled?: boolean
}

export function FormField({
  id,
  label,
  type = "text",
  value,
  onChange,
  error,
  hint,
  required,
  autoComplete,
  disabled,
}: FormFieldProps) {
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
      <input
        id={id}
        name={id}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        autoComplete={autoComplete}
        disabled={disabled}
        aria-invalid={error ? true : undefined}
        aria-describedby={
          error ? `${id}-error` : hint ? `${id}-hint` : undefined
        }
        className={cn(
          "w-full border-2 bg-background px-3 py-2.5 text-sm text-foreground outline-none transition-colors",
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

interface FormAlertProps {
  variant: "error" | "info"
  children: React.ReactNode
  className?: string
}

export function FormAlert({ variant, children, className }: FormAlertProps) {
  return (
    <div
      role={variant === "error" ? "alert" : "status"}
      className={cn(
        "border-2 px-4 py-3 text-sm",
        variant === "error" &&
          "border-stamp-red bg-stamp-red/10 text-stamp-red",
        variant === "info" &&
          "border-institutional bg-institutional/5 text-institutional",
        className
      )}
    >
      {children}
    </div>
  )
}
