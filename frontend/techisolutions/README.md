# TechISOlutions — Frontend

Aplicación web de **TechISOlutions** (Hackathon ONE — G9-LATAM-Team_40), construida con **Next.js 16 (App Router) + React 19 + TypeScript**. Las pantallas autenticadas consumen el backend Spring Boot; no incluyen datos mock.

Arquitectura, capacidades y flujos: [`docs/frontend-arquitectura.md`](../../docs/frontend-arquitectura.md).

## Stack

- **Next.js 16** — App Router y routing por convención (`app/`)
- **React 19** + **TypeScript 5**
- **Tailwind CSS 4**, shadcn/ui y `lucide-react`
- **react-force-graph-2d** — visualización del grafo
- **Bun** — package manager (`bun.lock`)

## Requisitos y scripts

- Node.js 20.9+
- Bun 1.x

```bash
bun install
bun run dev       # http://localhost:3000
bun run test      # Vitest
bun run typecheck # tsc --noEmit
bun run lint      # ESLint
bun run format    # Prettier
bun run build
bun run start
```

## Rutas

| Path | Acceso | Contenido |
|------|--------|-----------|
| `/` | Público | Landing con demo estática de clasificación y enlaces al producto |
| `/login`, `/register` | Público | Autenticación mediante `/auth/login` y `/auth/register` |
| `/dashboard` | Sesión | Resumen de consultas, categorías y archivos |
| `/consultar` | Sesión | Consulta GraphRAG, respuesta y trazabilidad por fuente |
| `/archivos` | Sesión | Carga de PDF/TXT/MD, dominio ISOS/LEYES, estado de índice y descargas |
| `/grafo` | Sesión | Visualización del snapshot BASE o del grafo privado del usuario |

`AuthGate` protege las rutas de sesión y lee `access_token` desde `localStorage`. `apiFetch` añade el Bearer JWT a las llamadas y centraliza errores. El navegador nunca recibe URLs de Object Storage: las descargas pasan por `/api/archivos/{id}/descarga`.

## Contratos consumidos

- **Consultas:** `POST /api/consultas` con `{ "pregunta": "..." }`; la pregunta debe tener al menos 20 caracteres. También se usan el historial y la búsqueda por `q`.
- **Archivos:** `POST /api/archivos` como `multipart/form-data` con `file` y `dominio` (`ISOS` o `LEYES`). Solo PDF, TXT y MD de hasta 10 MB.
- **Indexación:** `/api/indice` expone los estados `IDLE`, `DIRTY`, `QUEUED`, `RUNNING`, `SUCCEEDED` y `FAILED`; `/api/indice/reintentar` solicita una nueva reconstrucción.
- **Grafos:** `/api/grafos/actual` muestra el corpus BASE y `/api/grafos/privado` el release aislado del usuario. Las fuentes de consultas indican `corpus: BASE|PRIVADO`.
- **API base:** `NEXT_PUBLIC_API_URL` apunta a Spring Boot; por defecto `http://localhost:8080`.

## Configuración

```bash
NEXT_PUBLIC_API_URL=http://localhost:8080
bun run dev
```

En Docker, `NEXT_PUBLIC_API_URL` se inyecta durante `docker build`; debe ser una URL accesible desde el navegador del usuario, no el hostname interno `backend`.

## Estructura

```
app/          # App Router: landing, consultar, archivos, grafo, auth
components/   # auth, clipboard, contenido, archivos, dashboard, grafo, ui
services/     # auth, consulta, archivo, indice, categoria, grafo
lib/          # api, mappers, search, graph-data, demo-data
types/        # contratos TypeScript de auth, consultas, archivos, índice y grafo
```
