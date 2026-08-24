export const ISO_CATEGORIES = [
  "Política SST",
  "Procedimientos",
  "Matrices de Riesgo",
  "Registros",
  "Auditorías",
] as const

export const DEMO_CLASSIFICATION = {
  titulo: "Política de Seguridad y Salud en el Trabajo",
  texto: "Esta política establece los compromisos de la organización en materia de seguridad y salud en el trabajo: prevención de riesgos laborales, formación de los trabajadores y mejora continua del sistema de gestión.",
  categoria: "Política SST",
  relevancia: 0.91,
  palabras_clave: ["Seguridad", "Salud en el trabajo", "Política SST", "Prevención de riesgos"],
}

export const DEMO_RECENT = [
  { id: "a1b2c3d4", titulo: "Política de Seguridad y Salud en el Trabajo", categoria: "Política SST", relevancia: 0.91, palabras_clave: ["Seguridad", "Política SST", "Prevención de riesgos"], procesado_en: "2026-07-23T14:30:00Z" },
  { id: "e5f6g7h8", titulo: "Matriz de Riesgos Laborales 2026", categoria: "Matrices de Riesgo", relevancia: 0.87, palabras_clave: ["Riesgos", "Matriz", "Evaluación"], procesado_en: "2026-07-22T09:15:00Z" },
  { id: "i9j0k1l2", titulo: "Procedimiento de evacuación y emergencias", categoria: "Procedimientos", relevancia: 0.84, palabras_clave: ["Evacuación", "Emergencias", "Procedimiento"], procesado_en: "2026-07-21T16:45:00Z" },
  { id: "m3n4o5p6", titulo: "Registro de capacitación SST — Q2 2026", categoria: "Registros", relevancia: 0.79, palabras_clave: ["Capacitación", "Registro", "Formación"], procesado_en: "2026-07-20T11:00:00Z" },
  { id: "q7r8s9t0", titulo: "Informe de auditoría interna ISO 45001", categoria: "Auditorías", relevancia: 0.93, palabras_clave: ["Auditoría", "ISO 45001", "Hallazgos"], procesado_en: "2026-07-19T08:30:00Z" },
] as const

export const DEMO_STATS = { consultas: 24, categorias: 5, archivos: 12 }
