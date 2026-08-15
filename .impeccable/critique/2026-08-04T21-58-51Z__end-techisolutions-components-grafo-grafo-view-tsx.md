---
target: grafo view relations popup
total_score: 16
max_score: 40
na_heuristics: 
p0_count: 3
p1_count: 1
timestamp: 2026-08-04T21-58-51Z
slug: end-techisolutions-components-grafo-grafo-view-tsx
---
Method: dual-agent (A: e6ef082c · B: 3352fd12)

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 1 | 0 relaciones en demo; hover fuera del mapa |
| 2 | Match System / Real World | 2 | Copy SST ok; aristas invisibles rompen trazabilidad |
| 3 | User Control and Freedom | 1 | Clic abandona el mapa; sin pin/dismiss overlay |
| 4 | Consistency and Standards | 2 | Clipboard ok; patrón info no es overlay Operate |
| 5 | Error Prevention | 1 | Demo con categorías únicas → links[] vacío por diseño |
| 6 | Recognition Rather Than Recall | 2 | Sin razón de arista ni preview de destino |
| 7 | Flexibility and Efficiency | 1 | Sin pin, sin CTA archivo, sin foco vecinos |
| 8 | Aesthetic and Minimalist Design | 2 | Card bajo el grafo genera scroll |
| 9 | Error Recovery | 2 | Empty files ok; 0 edges sin recovery |
| 10 | Help and Documentation | 2 | Falta affordance hover/pin/abrir |
| **Total** | | **16/40** | **Poor** |

## Design Specificity Verdict

**LLM:** Chrome clipboard es específico; canvas genérico. Con 0 aristas falla el job.

**Detector:** 0 findings. DEMO_RECENT = 5 categorías únicas → 0 links. Hover fuera de FormPaper.

## Priority Issues

### [P0] Demo sin aristas
### [P0] Hover causa scroll
### [P0] Clic debe fijar popup + CTA archivo
### [P1] Contenido del popup
### [P2] Contraste leyenda aristas
