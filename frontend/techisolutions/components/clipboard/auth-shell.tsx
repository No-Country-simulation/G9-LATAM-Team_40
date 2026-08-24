import Link from "next/link"

import { FormPaper } from "@/components/clipboard/form-elements"
import { SiteHeader } from "@/components/clipboard/site-header"

interface AuthShellProps {
  formCode: string
  title: string
  description: string
  children: React.ReactNode
  footer: React.ReactNode
}

export function AuthShell({ formCode, title, description, children, footer }: AuthShellProps) {
  return (
    <div className="min-h-svh bg-background">
      <SiteHeader variant="auth" />
      <main className="mx-auto flex max-w-6xl flex-col items-center px-4 py-10 sm:px-6 sm:py-14">
        <FormPaper className="w-full max-w-md p-6 sm:p-8">
          <div className="mb-6 flex flex-wrap items-center gap-3 border-b-2 border-institutional pb-4">
            <span className="tape-strip px-2 py-0.5 text-[10px] font-bold tracking-widest text-institutional uppercase">{formCode}</span>
            <span className="font-mono text-[10px] text-muted-foreground">Acceso restringido · SST</span>
          </div>
          <h1 className="mb-2 text-2xl font-bold text-institutional">{title}</h1>
          <p className="mb-6 text-sm leading-relaxed text-muted-foreground">{description}</p>
          {children}
          <div className="mt-6 border-t-2 border-dashed border-border pt-4 text-center text-sm text-muted-foreground">{footer}</div>
        </FormPaper>
        <p className="mt-6 text-center text-xs text-muted-foreground"><Link href="/" className="font-medium text-carbon hover:underline">Volver al inicio</Link></p>
      </main>
    </div>
  )
}
