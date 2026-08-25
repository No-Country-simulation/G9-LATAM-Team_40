import { GraphRagQuery } from "@/components/contenido/graph-rag-query"

type ConsultarPageProps = {
  searchParams: Promise<{ consulta?: string | string[] }>
}

export default async function ConsultarPage({ searchParams }: ConsultarPageProps) {
  const params = await searchParams
  const consulta = Array.isArray(params.consulta) ? params.consulta[0] : params.consulta

  return <GraphRagQuery initialConsultaId={consulta ?? null} />
}
