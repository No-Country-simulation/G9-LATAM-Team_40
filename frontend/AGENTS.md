# AGENTS.md — Frontend
**Stack:** React 18 | Vite | TypeScript | React Router v6

Todo agente de IA y todo desarrollador debe leer este archivo antes de generar o modificar codigo en `frontend/`.

---

## Estructura de Carpetas

```
frontend/src/
├── main.tsx                  # Entry point
├── App.tsx                   # Router principal
├── components/               # Componentes reutilizables (sin logica de negocio)
│   ├── ui/                   # Atomicos: Button, Input, Card, Spinner, Badge, Alert
│   └── layout/               # Navbar, Sidebar, PageLayout
├── pages/                    # Una carpeta por pagina/ruta
│   ├── auth/                 # Login, Register
│   ├── dashboard/            # Dashboard principal
│   ├── content/              # Clasificar contenido (individual y lote)
│   └── files/                # Mis Archivos, Upload
├── services/                 # Llamadas HTTP a la API backend
│   ├── http.ts               # Instancia base con interceptor JWT
│   ├── contenido.service.ts
│   ├── archivo.service.ts
│   └── auth.service.ts
├── types/                    # Tipos TypeScript de la API
│   ├── contenido.types.ts
│   ├── archivo.types.ts
│   └── auth.types.ts
├── hooks/                    # Custom hooks
│   └── useAuth.ts
├── store/                    # Estado global (Context API o Zustand)
│   └── auth.store.ts
└── utils/                    # Helpers puros sin efectos
    └── token.utils.ts
```

---

## Convenciones de Codigo

### Componentes — siempre functional components con TypeScript
```tsx
// Correcto
interface Props {
  titulo: string;
  onSubmit: (data: ContenidoRequest) => void;
}

export function ClasificarForm({ titulo, onSubmit }: Props) {
  return <form>...</form>;
}

// Incorrecto — no usar default export anonimo ni class components
export default function() { ... }
```

### Nomenclatura
| Elemento | Convencion | Ejemplo |
|----------|------------|---------|
| Componente | PascalCase | `ClasificarForm`, `ArchivoCard` |
| Archivo de componente | PascalCase.tsx | `ClasificarForm.tsx` |
| Servicio HTTP | camelCase.service.ts | `contenido.service.ts` |
| Tipo / Interface | PascalCase | `ContenidoResponse`, `ArchivoRequest` |
| Hook | use + PascalCase | `useAuth`, `useContenido` |
| Carpeta de pagina | kebab-case | `pages/content/`, `pages/auth/` |

### Tipos TypeScript — siempre definir los contratos de la API

```typescript
// types/contenido.types.ts
export interface ContenidoRequest {
  titulo: string;
  texto: string;
}

export interface ContenidoResponse {
  id: string;
  categoria: string;
  probabilidad: number;
  palabras_clave: string[];
  contenidos_relacionados: ContenidoRelacionado[];
  procesado_en: string;
}

export interface ContenidoRelacionado {
  id: string;
  titulo: string;
  similitud: number;
}
```

### Servicios HTTP — centralizar en `services/`
```typescript
// services/http.ts — instancia base con interceptor
import axios from 'axios';

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

```typescript
// services/contenido.service.ts
import { http } from './http';
import type { ContenidoRequest, ContenidoResponse } from '../types/contenido.types';

export const contenidoService = {
  clasificar: (data: ContenidoRequest) =>
    http.post<ContenidoResponse>('/api/contenido', data).then(r => r.data),
};
```

### Reglas de capas
- Los **componentes UI** (`components/ui/`) no hacen llamadas HTTP. Reciben datos por props.
- Las **paginas** (`pages/`) llaman a los services o usan custom hooks. Manejan el estado local de la pagina.
- Los **services** solo manejan HTTP. Sin logica de presentacion.
- No llamar a `localStorage` directamente en componentes — usar `token.utils.ts` o `auth.store.ts`.

### Manejo de errores HTTP
- Error 400 → mostrar mensaje de validacion en el formulario correspondiente
- Error 401 → el interceptor redirige a `/login` automaticamente
- Error 500 → mostrar componente `Alert` con mensaje generico

---

## Variables de entorno

Prefijo obligatorio `VITE_` para que Vite las exponga al cliente:

```
VITE_API_URL=http://localhost:8080
```

No commitear `.env.local`. El archivo `.env.example` en `/frontend` documenta las variables necesarias.

---

## Autenticacion

- El JWT se obtiene desde Supabase Auth (el backend lo valida, no lo emite directamente en la mayoria de los casos).
- Almacenar el `access_token` en `localStorage` bajo la clave `access_token`.
- Adjuntar en cada request via el interceptor de `http.ts`.
- Rutas protegidas: si no hay token, redirigir a `/login` con React Router.

---

## Componentes Base (responsabilidad de FE-3)

Antes de que FE-1 y FE-2 implementen sus pantallas, estos componentes deben existir:

| Componente | Uso |
|------------|-----|
| `Button` | props: `variant` (primary/secondary/danger), `loading`, `disabled` |
| `Input` | props: `label`, `error`, `type` |
| `Card` | contenedor con sombra y padding estandar |
| `Spinner` | indicador de carga |
| `Badge` | etiqueta de categoria con color |
| `Alert` | mensajes de error/exito/info |

---

## Rutas de la aplicacion

| Path | Componente | Protegida |
|------|------------|-----------|
| `/login` | `pages/auth/Login` | No |
| `/register` | `pages/auth/Register` | No |
| `/` | `pages/dashboard/Dashboard` | Si |
| `/clasificar` | `pages/content/ClasificarContent` | Si |
| `/clasificar/lote` | `pages/content/ClasificarLote` | Si |
| `/archivos` | `pages/files/Archivos` | Si |

---

## Comandos

```bash
# Instalar dependencias
npm install

# Desarrollo
npm run dev

# Build de produccion
npm run build

# Preview del build
npm run preview
```
