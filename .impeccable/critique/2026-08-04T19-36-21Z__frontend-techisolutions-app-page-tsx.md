---
target: landing hero visual ISO animation
total_score: 17
max_score: 24
na_heuristics: 5,7,9,10
p0_count: 2
p1_count: 2
timestamp: 2026-08-04T19-36-21Z
slug: frontend-techisolutions-app-page-tsx
---
Method: dual-agent (A: 265dab6c · B: inline — subagent resource_exhausted)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 2 | Hero sin output de clasificación; producto invisible en primer viewport |
| 2 | Match System / Real World | 4 | Formulario SST, tape, categorías ISO coherentes |
| 3 | User Control and Freedom | 3 | Login/registro siempre accesibles |
| 4 | Consistency and Standards | 4 | Tokens clipboard alineados con DESIGN.md |
| 5 | Error Prevention | n/a | Landing informativa |
| 6 | Recognition Rather Than Recall | 1 | Solo texto; sin imagen ISO, demo o animación en hero |
| 7 | Flexibility and Efficiency | n/a | Persuade surface |
| 8 | Aesthetic and Minimalist Design | 3 | Coherente pero hero vacío (minimal → empty) |
| 9 | Error Recovery | n/a | — |
| 10 | Help and Documentation | n/a | Persuade surface |
| **Total** | | **17/24** | **Good** (~71%) |

## Design Specificity Verdict

**LLM assessment:** El mundo clipboard es distintivo en tokens y demo (CategoryBadge, 91%, keywords). El hero viola la promesa de Persuade: es portada de formulario (tape + H1 + CTAs) sin mostrar el acto central (documento → categoría ISO). ISO aparece solo como texto en cinta; cero assets raster/SVG en repo (`public/` vacío). La página mejora en legibilidad tras polish pero sigue siendo narrativa textual hasta la sección 3.

**Deterministic scan:** 0 findings en `page.tsx`. No detecta hero sin demostración visual ni ausencia de assets.

**Browser overlays:** No disponibles.

## Overall Impression

El usuario acierta: el hero no enseña qué hace el producto. El mejor UI (clasificación con badge y probabilidad) está dos scrolls abajo. Sin logos ISO, ilustraciones ni motion, la landing parece carta administrativa, no herramienta ML. La demo estática existente debería ser el hero, no un apéndice.

## What's Working

1. **Demo section** — `DEMO_CLASSIFICATION` con CategoryBadge y keywords es proof concreto cuando el usuario llega.
2. **Identidad clipboard** — tape, FormPaper, mono metadata: credibilidad SST sin parecer SaaS genérico.
3. **Copy post-clarify** — H1 outcome-first, sin jargon de API; tono compliance español.

## Priority Issues

### [P0] Hero no demuestra el producto
- **Why:** Primer viewport = H1 + botones; coordinador SST no ve clasificación, formatos ni categorías en 5s.
- **Fix:** Grid hero 2 columnas: izquierda promesa + línea mecanismo + CTA; derecha mini-demo embebida (reutilizar DEMO_CLASSIFICATION o pipeline Recibir→Clasificar animado).
- **Suggested command:** `/impeccable layout` + `/impeccable animate`

### [P0] Drift vs FIRST VIEWPORT (layout.tsx)
- **Why:** Seed promete checklist visible en primer viewport; checklist es sección 2.
- **Fix:** Mover demo al hero o primeros 2 pasos del checklist junto al H1.
- **Suggested command:** `/impeccable layout`

### [P1] Sin identidad visual ISO (solo texto)
- **Why:** 0 svg/png en proyecto; ISO 45001 solo en strings; usuario pide logos/imágenes alusivas.
- **Fix:** SVG inline (escudo/marca estilizada sin infringir ISO oficial), franja de CategoryBadge colors, clip clipboard silhouette, sello de aprobación CSS — sin depender de assets externos hasta que el equipo suba logo.
- **Suggested command:** `/impeccable colorize` + `/impeccable delight`

### [P1] Animación inexistente en landing
- **Why:** Solo `hover:-translate-y-px`; ML "en segundos" no se siente; página estática.
- **Fix:** Un momento authored: sello que aparece sobre badge, checklist cascade on scroll, flecha demo pulse — respetar `prefers-reduced-motion`.
- **Suggested command:** `/impeccable animate`

### [P2] Hero sin línea de mecanismo
- **Why:** H1 dice resultado, no método (¿PDFs? ¿qué categorías?).
- **Fix:** Una línea: "Sube políticas, matrices y registros → categoría ISO 45001 y palabras clave."
- **Suggested command:** `/impeccable clarify`

### [P3] Capabilities genéricas (icon cards)
- **Fix:** Mini document specimens o pipeline strip en lugar de Lucide genéricos.
- **Suggested command:** `/impeccable polish`

## Persona Red Flags

**Jordan:** No diferencia vs SharePoint en 5s; CTA antes de comprender valor.

**Casey (móvil):** Demo oculta bajo scroll; flecha causa→efecto solo en lg.

**Coordinador SST:** No ve Política/Matriz/Registro al llegar; checklist con ✓ en pasos 1–2 parece auditoría ya hecha.

## Minor Observations

- Header duplica login/register del hero.
- CTA final (fondo institucional) es el bloque visual más fuerte — hero el más débil.
- `FormPaper plain` en hero elimina ruled-paper que vendía clipboard.

## Questions to Consider

- ¿Por qué el hero es login gate si la demo es el único lugar donde existe el producto?
- ¿Un coordinador registra antes de ver 91% en Política SST?
- ¿SVG inline basta o el equipo debe subir logo ISO/producto?
