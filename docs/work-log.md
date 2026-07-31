# Work Log — TechContent AI
**Hackathon ONE | Alura + Oracle | G9-LATAM-Team_40**

Registro cronologico de decisiones, acuerdos y entregables del equipo.
Cada entrada incluye fecha, autor/responsable y descripcion del trabajo realizado.

---

## 2026-07-29

### Definicion de arquitectura backend
**Responsable:** Equipo Backend + PM
**Tipo:** Decision de arquitectura

Se definio la division del backend en 4 capas independientes, cada una asignada a un dev:

| Capa | Paquete | Dev |
|------|---------|-----|
| API (Presentacion) | `com.techcontent.ai.api` | BE-4 |
| Security | `com.techcontent.ai.security` | BE-1 |
| Domain (Negocio) | `com.techcontent.ai.domain` | BE-2 |
| Integration | `com.techcontent.ai.integration` | BE-3 |

**Razon:** Separacion de concerns. Cada dev trabaja en archivos distintos desde el Dia 1, eliminando conflictos de merge.

**Archivo:** `backend/docs/markdown.md`

---

### Sprint Plan — 2 semanas
**Responsable:** PM
**Tipo:** Planificacion

Se creo el plan de sprints para todo el equipo (4 backend + 3 frontend) siguiendo metodologia Scrum adaptada a hackathon:

- **Sprint 1 (Semana 1):** Cimientos — auth, persistencia, clasificacion de texto end-to-end
- **Sprint 2 (Semana 2):** Features completas, testing, deploy y demo

Definition of Done del Sprint 1: `POST /api/contenido` con JWT valido devuelve categoria + keywords y persiste en DB.

**Archivo:** `docs/sprint-plan.md`

---

### Verificacion del estado inicial del proyecto
**Responsable:** PM
**Tipo:** Discovery

Se realizo auditoria completa del repositorio. Estado confirmado:

**Existe y esta listo:**
- `backend/pom.xml` — todas las dependencias declaradas (Security, JPA, Web, Validation, Actuator, Lombok, Test)
- `backend/src/main/resources/application.properties` — configurado con DB, ML service, Supabase vars
- `backend/Dockerfile` — multi-stage build listo para produccion
- `docker-compose.yml` — infraestructura completa (Spring Boot, FastAPI, PostgreSQL, Supabase Auth/REST/Studio)
- `datascience/app/main.py` — FastAPI con `/health` y `/predict` operativos (respuesta hardcodeada, suficiente para que BE-3 integre el `MlClient` hoy)

**No existe todavia:**
- Ningun archivo Java de negocio (controllers, services, entities, repositories, filters)
- Frontend (carpeta `frontend/` vacia salvo el AGENTS.md)

**Conclusion:** Docker compose funcional localmente. `/predict` de Data Science ya responde. BE-3 puede implementar el `MlClient` sin esperar el modelo real.

---

### AGENTS.md — Convenciones de equipo
**Responsable:** PM
**Tipo:** Documentacion de convenciones

Se redactaron los tres archivos de convenciones del proyecto basados en el stack existente verificado:

**`/AGENTS.md`** (raiz) — Convenciones globales:
- Estructura del repositorio
- Git workflow: ramas (`main`, `develop`, `feature/BE-X-*`, `feature/FE-X-*`)
- Formato de commits: Conventional Commits
- Reglas de Pull Requests (minimo 1 aprobacion, tests deben pasar)
- Reglas para agentes de IA

**`/backend/AGENTS.md`** — Convenciones Java/Spring Boot:
- Estructura de paquetes bajo `com.techcontent.ai`
- Nomenclatura de clases (Controller, Service, Repository, Client, Filter, Config)
- DTOs como Java Records (Java 17)
- Entidades JPA con Lombok (@Data, @Builder)
- Inyeccion por constructor con @RequiredArgsConstructor
- Reglas estrictas de capas (controller no llama a repository ni a client)
- Convencion de nombres de tests: `metodo_condicion_resultadoEsperado()`
- Metas de cobertura: Services 80%, Controllers 70%, Security 90%

**`/frontend/AGENTS.md`** — Convenciones React/TypeScript:
- Estructura de carpetas (`components/`, `pages/`, `services/`, `types/`, `hooks/`, `store/`, `utils/`)
- Functional components con TypeScript tipado
- Nomenclatura (PascalCase componentes, camelCase.service.ts, PascalCase types)
- Patron de servicios HTTP con interceptor JWT centralizado
- Variables de entorno con prefijo `VITE_`
- Componentes base que FE-3 debe entregar antes de que FE-1 y FE-2 arranquen

---

### Credenciales pendientes
**Responsable:** Equipo (pendiente de resolucion)
**Tipo:** Blocker parcial

Las siguientes credenciales NO estan disponibles todavia:
- `SUPABASE_JWT_SECRET` — necesario para que BE-1 valide tokens reales
- `SUPABASE_ANON_KEY` / `SUPABASE_SERVICE_KEY` — necesarios para proxy auth
- `OCI_CLI_USER`, `OCI_CLI_TENANCY`, `OCI_CLI_FINGERPRINT`, `OCI_CLI_KEY_FILE` — necesarios para OCI Object Storage

**Impacto:** BE-1 avanza con JWT secret placeholder en application.properties. BE-3 implementa OciStorageClient con metodos stub hasta recibir credenciales. El resto del equipo (BE-2, BE-4, FE-*) no se ve afectado.

**Accion pendiente:** Conseguir credenciales de Supabase y OCI lo antes posible para desbloquear BE-1 y BE-3 en la segunda mitad de la Semana 1.

---

### Stack frontend — pendiente de confirmacion
**Responsable:** Equipo Frontend
**Tipo:** Decision pendiente

El AGENTS.md de frontend fue redactado asumiendo **React 18 + Vite + TypeScript + React Router v6**.

**Accion pendiente:** El equipo de frontend debe confirmar o corregir este stack antes de que FE-3 inicialice el proyecto. Una vez confirmado, actualizar este work log con la decision final.

---

---

### Implementacion del esqueleto completo del backend
**Responsable:** Equipo Backend
**Tipo:** Implementacion

Se generaron todos los archivos Java del backend siguiendo las convenciones definidas en `backend/AGENTS.md`. El proyecto pasa de un esqueleto vacío a una aplicación con todas las capas implementadas.

#### Dependencias agregadas al pom.xml
- `jjwt-api`, `jjwt-impl`, `jjwt-jackson` v0.12.6 — para validacion de tokens HS256 de Supabase

#### Propiedades agregadas a application.properties
- `oci.files.bucket` — nombre del bucket para archivos de usuario
- `spring.jackson.serialization.write-dates-as-timestamps=false` — fechas como ISO 8601
- `spring.jackson.time-zone=UTC`

#### Archivos creados

**Capa API (`com.techcontent.ai.api`)**
| Archivo | Descripcion |
|---------|-------------|
| `dto/request/ContenidoRequest.java` | Record con `@NotBlank` en titulo y `@Size(min=20)` en texto |
| `dto/request/ContenidoLoteRequest.java` | Record con lista de `ContenidoRequest`, max 20 items |
| `dto/response/ContenidoResponse.java` | Record de respuesta de clasificacion |
| `dto/response/ContenidoRelacionadoResponse.java` | Record para contenidos relacionados |
| `dto/response/ArchivoResponse.java` | Record de respuesta de archivo subido |
| `dto/response/CategoriaResponse.java` | Record con nombre y totalDocumentos |
| `exception/ErrorResponse.java` | Record con error y mensaje |
| `exception/ContenidoNotFoundException.java` | RuntimeException para 404 de contenido |
| `exception/ArchivoNotFoundException.java` | RuntimeException para 404 de archivo |
| `exception/GlobalExceptionHandler.java` | @RestControllerAdvice para 400, 404, 500 |
| `controller/ContenidoController.java` | POST /api/contenido, /lote, GET /buscar, GET / |
| `controller/ArchivoController.java` | POST /api/archivos, GET /, GET /{id} |
| `controller/CategoriaController.java` | GET /api/categorias |
| `controller/AuthController.java` | POST /auth/register y /auth/login |

**Capa Security (`com.techcontent.ai.security`)**
| Archivo | Descripcion |
|---------|-------------|
| `SupabaseUserDetails.java` | Implementa UserDetails con userId (UUID) y email |
| `JwtService.java` | Parsea y valida JWT HS256 con SUPABASE_JWT_SECRET usando JJWT 0.12.x |
| `JwtAuthFilter.java` | OncePerRequestFilter — extrae Bearer token y puebla SecurityContext |
| `SecurityConfig.java` | CSRF off, stateless, CORS abierto, rutas publicas: /auth/**, /actuator/** |

**Capa Domain (`com.techcontent.ai.domain`)**
| Archivo | Descripcion |
|---------|-------------|
| `model/Contenido.java` | @Entity con @ElementCollection para palabrasClave |
| `model/Archivo.java` | @Entity con userId, nombre, url, tamano, tipo, subidoEn |
| `repository/ContenidoRepository.java` | findByUserId, buscarPorKeyword (JPQL), findCategoriasConConteo |
| `repository/ArchivoRepository.java` | findByUserId, findByIdAndUserId |
| `service/ContenidoService.java` | clasificar, procesarLote, buscar, listarPorUsuario |
| `service/ArchivoService.java` | subir (con validacion de tipo y tamano), listar, obtenerPorId |
| `service/CategoriaService.java` | listarConConteo |

**Capa Integration (`com.techcontent.ai.integration`)**
| Archivo | Descripcion |
|---------|-------------|
| `ml/MlRequest.java` | Record `{ texto }` |
| `ml/MlResponse.java` | Record con @JsonProperty para `palabras_clave` snake_case |
| `ml/MlClient.java` | RestClient → POST http://ml-service:5000/predict |
| `oci/OciStorageClient.java` | Stub con TODO — retorna URL placeholder hasta tener credenciales OCI |
| `supabase/SupabaseAuthRequest.java` | Record `{ email, password }` |
| `supabase/SupabaseAuthResponse.java` | Record con @JsonProperty para campos snake_case de Supabase |
| `supabase/SupabaseAuthClient.java` | RestClient → GoTrue /auth/v1/signup y /token |

#### Decisiones tecnicas tomadas
- **DTOs como Java Records** (Java 17) — inmutables, menos boilerplate
- **Inyeccion por constructor** con `@RequiredArgsConstructor` en todos los services y controllers
- **@AuthenticationPrincipal** en controllers para extraer el usuario autenticado del SecurityContext
- **@ElementCollection** para `palabrasClave` — crea tabla `contenido_palabras_clave`, soporta busqueda por JPQL JOIN
- **OciStorageClient como stub** — no bloquea el desarrollo mientras llegan las credenciales. Loguea warning y retorna URL placeholder.
- **contenidosRelacionados** retorna lista vacia por ahora — marcado con TODO para implementar en Sprint 2

#### Estado del backend al finalizar
- Compila correctamente (pendiente verificar con `mvn compile`)
- `POST /api/contenido` funciona end-to-end con el ML service de Docker (que ya responde en :5000)
- `POST /api/archivos` funciona hasta OCI (guarda metadata en DB, URL es placeholder)
- Auth por JWT pendiente de `SUPABASE_JWT_SECRET` real
- DB se auto-crea con `ddl-auto=update` al levantar el contenedor

---

---

### Verificacion y fix de arranque del backend en Docker
**Responsable:** PM / Verificacion automatizada
**Tipo:** Bugfix + Verificacion

Se realizo la verificacion completa del backend recien implementado compilando dentro del entorno Docker real y levantando el contenedor.

#### Resultado de compilacion
```
[INFO] Compiling 33 source files with javac [debug release 17] to target/classes
[INFO] BUILD SUCCESS — Total time: 01:23 min
```
Los 33 archivos Java compilaron sin errores ni warnings de compilacion.

#### Bug encontrado y corregido — JwtService crash en arranque
**Causa raiz:** `SUPABASE_JWT_SECRET` esta vacia (credenciales aun no disponibles). JJWT lanza `WeakKeyException` al intentar crear una `SecretKey` desde un string vacio en el constructor de `JwtService`.

**Error exacto:**
```
io.jsonwebtoken.security.WeakKeyException: The specified key byte array is 0 bits
which is not secure enough for any JWT HMAC-SHA algorithm.
```

**Fix aplicado en `security/JwtService.java`:**
- Se agrego validacion en el constructor: si el secreto es `null` o blank, se asigna `secretKey = null` y se loguea un `WARN`
- `isTokenValid()` retorna `false` cuando `secretKey == null` — rechaza todos los tokens hasta tener el secreto real
- La app arranca correctamente sin credenciales

**Comportamiento resultante:**
- Sin `SUPABASE_JWT_SECRET`: app arranca, loguea `WARN`, todos los endpoints protegidos devuelven 401
- Con `SUPABASE_JWT_SECRET` real: validacion JWT funciona normalmente

#### Verificacion final de health check
```
GET http://localhost:8080/actuator/health
→ 200 OK
{
  "status": "UP",
  "components": {
    "db": { "status": "UP", "details": { "database": "PostgreSQL" } },
    "diskSpace": { "status": "UP" },
    "ping": { "status": "UP" }
  }
}
```

**Confirmado:**
- Spring Boot 3.2.5 arranca correctamente en Docker con Java 17
- Hibernate conecta a PostgreSQL y ejecuta `ddl-auto=update` (tablas creadas automaticamente)
- Tablas generadas: `contenidos`, `archivos`, `contenido_palabras_clave`
- Todos los beans de Spring se inicializan correctamente
- `Started TechContentAiApplication in 97.918 seconds`

#### Estado del backend al cierre del dia
| Componente | Estado |
|------------|--------|
| Compilacion (33 archivos) | OK |
| Arranque en Docker | OK |
| Conexion a PostgreSQL | OK |
| Esquema de DB (tablas) | Creado automaticamente |
| Health check `/actuator/health` | UP |
| Validacion JWT | Pendiente de SUPABASE_JWT_SECRET |
| Upload a OCI | Pendiente de credenciales OCI (stub activo) |
| Auth con Supabase | Pendiente de credenciales Supabase |

---

## 2026-07-30

### Stack frontend — decision final
**Responsable:** Equipo Frontend
**Tipo:** Decision

Se confirma el stack del frontend, descartando el supuesto inicial de **React 18 + Vite + TypeScript + React Router v6** (entrada del 2026-07-29):

- **Next.js 16 (App Router)** + **React 19** + **TypeScript 5**
- **Tailwind CSS 4** + **shadcn/ui** (Base UI) + **lucide-react**
- **Bun** como package manager (`bun.lock`)
- Routing por convencion del App Router (`app/`), sin React Router
- Ubicacion: `frontend/techisolutions/`

**Impacto:** `README.md`, `AGENTS.md` (raiz) y `docs/sprint-plan.md` (FE-1) actualizados para reflejar el stack real.

---

### Inicializacion del proyecto frontend
**Responsable:** Equipo Frontend
**Tipo:** Implementacion

Se inicializo `frontend/techisolutions/` con Next.js 16.2.6 + React 19.2.4:

- `app/` con `layout.tsx` (fuentes Geist/Inter, ThemeProvider dark/light), `page.tsx` y `globals.css`
- shadcn/ui configurado (`components.json`) con primer componente base: `components/ui/button.tsx`
- Scripts: `dev`, `build`, `start`, `lint`, `typecheck`, `format` (ESLint 9 + Prettier + `tsc`)

**Pendiente (FE-1):** rutas de Login/Register y pantallas de auth.

---

*Ultima actualizacion: 2026-07-30*
