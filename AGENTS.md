# AGENTS.md — TechContent AI
**Hackathon ONE | Alura + Oracle | G9-LATAM-Team_40**

Este archivo define las convenciones globales del proyecto. Todo agente de IA y todo desarrollador debe leerlo antes de tocar cualquier archivo.

---

## Estructura del Repositorio

```
G9-LATAM-Team_40/
├── backend/          # Java 17 + Spring Boot 3.2.5
├── datascience/      # Python 3.11 + FastAPI (equipo independiente)
├── frontend/         # React + Vite + TypeScript
├── docs/             # Documentacion, decisiones, sprint plan
└── docker-compose.yml
```

El equipo de Data Science trabaja de forma independiente. No modificar `datascience/` sin coordinacion con ese equipo.

---

## Git Workflow

### Ramas
- `main` — produccion. Solo recibe merges desde `develop` cuando todo pasa.
- `develop` — rama de integracion del equipo. Todos los PRs van aqui.
- `feature/BE-1-nombre-tarea` — features de backend (BE-1, BE-2, BE-3, BE-4)
- `feature/FE-1-nombre-tarea` — features de frontend (FE-1, FE-2, FE-3)
- `fix/descripcion-del-bug` — correcciones

### Reglas de commits
Usar **Conventional Commits**:
```
feat: agregar JwtAuthFilter para validacion de tokens Supabase
fix: corregir manejo de JWT expirado en JwtService
chore: actualizar application.properties con nueva variable ML_SERVICE_URL
test: agregar ContenidoServiceTest con mock de MlClient
docs: actualizar sprint-plan con tareas del dia 3
```

### Pull Requests
- Todo PR va a `develop`, nunca directo a `main`
- Minimo 1 aprobacion antes de mergear
- El PR debe pasar `mvn test` (backend) o el test runner de frontend antes de mergear
- Titulo del PR: `[BE-X] Descripcion` o `[FE-X] Descripcion`

---

## Variables de Entorno

Nunca hardcodear credenciales en el codigo. Siempre usar variables de entorno definidas en `docker-compose.yml` o en un `.env` local (no commitear `.env`).

El archivo `.env.example` en la raiz documenta todas las variables necesarias.

---

## Reglas para Agentes de IA

- Leer el `AGENTS.md` del subproyecto correspondiente (`backend/AGENTS.md` o `frontend/AGENTS.md`) antes de generar codigo.
- No generar codigo que hardcodee credenciales, URLs o secrets.
- No modificar `docker-compose.yml` ni `datascience/` sin instruccion explicita.
- No crear archivos fuera de la estructura de paquetes definida en el AGENTS.md del subproyecto.
- Ante la duda sobre una convencion, preguntar antes de asumir.
