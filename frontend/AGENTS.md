# AGENTS.md — Frontend (TechISOlutions)
**Stack:** Next.js 16 (App Router) | React 19 | TypeScript | Tailwind CSS 4 | shadcn/ui | Bun

Todo agente de IA y todo desarrollador debe leer este archivo antes de generar o modificar codigo en `frontend/`. El codigo vive en `frontend/techisolutions/`.

Antes de escribir codigo Next.js, leer las guias en `frontend/techisolutions/node_modules/next/dist/docs/` si existen (APIs de esta version pueden diferir del entrenamiento).

---

## Estructura de Carpetas

```
frontend/techisolutions/
├── app/                          # App Router
│   ├── layout.tsx                # Root layout, fuentes, ThemeProvider
│   ├── page.tsx                  # Landing publica ISO 45001
│   ├── globals.css
│   ├── login/page.tsx
│   ├── register/page.tsx
│   ├── dashboard/page.tsx
│   ├── clasificar/page.tsx
│   ├── clasificar/lote/page.tsx
│   ├── archivos/page.tsx
│   └── grafo/page.tsx            # Snapshot GraphRAG (/api/grafos)
├── components/
│   ├── ui/                       # shadcn (p. ej. button)
│   ├── auth/                     # AuthGate, formularios, logout
│   ├── clipboard/                # Shell, nav, header, busqueda, sellos
│   ├── contenido/
│   ├── archivos/
│   ├── dashboard/
│   └── grafo/
├── services/                     # Llamadas HTTP al backend
│   ├── auth.service.ts
│   ├── contenido.service.ts
│   ├── archivo.service.ts
│   ├── categoria.service.ts
│   ├── grafo.service.ts
│   └── document.service.ts
├── types/
│   ├── contenido.types.ts
│   ├── archivo.types.ts
│   └── auth.types.ts
├── lib/
│   ├── api.ts                    # fetch + Bearer + 401 → /login
│   ├── token.ts                  # localStorage access_token
│   ├── mock-config.ts            # USE_MOCK_API
│   └── ...
└── hooks/
```

---

## Convenciones de Codigo

### Componentes — functional components con TypeScript
```tsx
interface Props {
  titulo: string
  onSubmit: (data: ContenidoRequest) => void
}

export function ClasificarForm({ titulo, onSubmit }: Props) {
  return <form>...</form>
}
```

No usar class components. Paginas de `app/` pueden usar default export (convencion App Router).

### Nomenclatura
| Elemento | Convencion | Ejemplo |
|----------|------------|---------|
| Componente | PascalCase | `ClasificarForm`, `ArchivoCard` |
| Archivo de componente | kebab-case.tsx | `import-document-form.tsx` |
| Servicio HTTP | camelCase.service.ts | `contenido.service.ts` |
| Tipo / Interface | PascalCase | `ContenidoResponse` |
| Hook | use + PascalCase | `useAuth` |
| Carpeta de ruta | kebab-case | `app/clasificar/` |

### Tipos TypeScript — contratos de la API
```typescript
export interface ContenidoRequest {
  titulo: string
  texto: string
}

export interface ContenidoResponse {
  id: string
  categoria: string
  probabilidad: number
  palabrasClave: string[]
  contenidosRelacionados: ContenidoRelacionado[]
  procesadoEn: string
}
```

El backend serializa varios campos de contenido en snake_case (`palabras_clave`, `procesado_en`, `respuesta`). Al cablear el API real, mapear o alinear nombres; no asumir que el JSON coincide 1:1 con estos tipos.

### Servicios HTTP — `lib/api.ts` + `services/`
```typescript
import { apiFetch } from "@/lib/api"

export async function clasificar(data: ContenidoRequest) {
  return apiFetch<ContenidoResponse>("/api/contenido", {
    method: "POST",
    body: JSON.stringify(data),
  })
}
```

`apiFetch` adjunta `Authorization: Bearer` desde `lib/token.ts` y en 401 limpia el token y redirige a `/login`.

### Reglas de capas
- `components/ui/` no hace HTTP; recibe datos por props.
- Paginas en `app/` componen vistas; la logica de datos va a `services/` o a vistas cliente.
- No llamar a `localStorage` en componentes: usar `lib/token.ts`.
- Rutas de la app autenticada van envueltas en `AuthGate`.

### Manejo de errores HTTP
- 400 → mensaje de validacion en el formulario
- 401 → `apiFetch` redirige a `/login`
- 500 → mensaje generico en UI

---

## Variables de entorno

Prefijo `NEXT_PUBLIC_` (build-time en el bundle):

```
NEXT_PUBLIC_API_URL=http://localhost:8080
NEXT_PUBLIC_USE_MOCK_API=true
```

`USE_MOCK_API` es **false** salvo que `NEXT_PUBLIC_USE_MOCK_API` sea exactamente `"true"` (`lib/mock-config.ts`). Extraer PDF en el cliente (`pdfjs-dist`); tipos de archivo: PDF, TXT, MD. No commitear `.env.local`.

---

## Autenticacion

- Login/register contra `POST /auth/login` y `POST /auth/register` (el backend proxifica Supabase).
- Guardar `access_token` en `localStorage` (`lib/token.ts`).
- Rutas protegidas: sin token, `AuthGate` redirige a `/login`.

---

## Rutas de la aplicacion

| Path | Protegida | Notas |
|------|-----------|--------|
| `/` | No | Landing ISO 45001 |
| `/login` | No | |
| `/register` | No | |
| `/dashboard` | Si | Panel |
| `/clasificar` | Si | Importar documento |
| `/clasificar/lote` | Si | Lote |
| `/archivos` | Si | Repositorio |
| `/grafo` | Si | Snapshot GraphRAG (`/api/grafos`) |

Nav autenticada: Panel, Importar, Grafo, Repositorio.

---

## Comandos

```bash
cd frontend/techisolutions
bun install
bun run dev          # puerto 3000; con Compose usar --port 3002
bun run build
bun run start
bun run lint
bun run typecheck
bun run format
```
