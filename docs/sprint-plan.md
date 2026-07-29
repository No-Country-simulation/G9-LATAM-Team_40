# TechContent AI — Sprint Plan
**Hackathon ONE | Alura + Oracle | G9-LATAM-Team_40**

> Metodologia: Scrum adaptado a hackathon
> Duracion total: 2 semanas (10 dias habiles)
> Equipos: Backend (4 devs) + Frontend (3 devs)
> Data Science: equipo independiente, expone API en `:5000`

---

## Roles y Responsabilidades

| Dev | Rol | Ownership |
|-----|-----|-----------|
| **BE-1** | Security Lead | Capa de seguridad, JWT Supabase, Spring Security |
| **BE-2** | Domain Lead | Entidades JPA, Repositories, Services de negocio |
| **BE-3** | Integration Lead | ML Client, OCI Storage, Supabase Auth Client |
| **BE-4** | API Lead + QA | Controllers, DTOs, validacion, pruebas unitarias e integracion |
| **FE-1** | Auth + Routing + Dashboard | Login, Register, rutas protegidas, Dashboard principal |
| **FE-2** | Clasificacion + Busqueda | Formulario de clasificacion, resultados, busqueda semantica, proceso por lote |
| **FE-3** | Archivos + Componentes base | Upload de archivos, listado, descarga, design system compartido |

---

## Acuerdos de Equipo (Day 0 — antes de arrancar)

Estas decisiones hay que tomarlas ANTES del Sprint 1. Si no, se bloquean todos.

- [ ] Definir rama de integracion: `develop` (cada dev trabaja en `feature/BE-X-descripcion`)
- [x] Levantar entorno local con `docker compose up -d` — todos deben tenerlo funcionando
- [x] Acordar el contrato de la API (DTOs de request/response) — BE-4 redacta, todos aprueban
- [x] Confirmar con Data Science que el endpoint `POST /predict` responde y el schema del response
- [ ] Crear el proyecto en Supabase (o levantar local) y compartir las env vars
- [ ] Crear los buckets en OCI Object Storage y compartir credenciales al equipo

---

## Sprint 1 — Semana 1: Cimientos
**Objetivo:** API funcional con auth, persistencia y clasificacion de un solo texto end-to-end.
**Definition of Done del Sprint:** `POST /api/contenido` con JWT valido devuelve categoria + keywords y persiste en la DB.

### Dia 1-2 — Setup y contratos

#### BE-1 | Security Setup
- [x] Configurar `SecurityConfig` con Spring Security (CORS, CSRF deshabilitado, rutas publicas vs protegidas)
- [x] Implementar `JwtService` — parsear y validar JWT firmado con `SUPABASE_JWT_SECRET` (HS256) — maneja secreto vacio sin crashear
- [x] Implementar `JwtAuthFilter` — `OncePerRequestFilter` que extrae Bearer token y puebla `SecurityContext`
- [x] Implementar `SupabaseUserDetails` con sub (userId), email y rol del JWT
- [ ] Prueba manual: request sin token → 401, con token valido → pasa el filtro

#### BE-2 | Domain Setup
- [x] Crear entidad `Contenido` con todos los campos (`@Entity`, `@Table`, Lombok)
- [x] Crear entidad `Archivo` con todos los campos
- [x] Configurar `application.properties` para PostgreSQL y `ddl-auto=update`
- [x] Verificar que el schema se crea en PostgreSQL al iniciar la app
- [x] Crear `ContenidoRepository` y `ArchivoRepository` (JpaRepository)

#### BE-3 | Integration Setup
- [x] Implementar `MlClient` con `RestClient` — POST a `${ML_SERVICE_URL}/predict`
- [x] Definir `MlRequest` y `MlResponse` (DTOs para la comunicacion con FastAPI)
- [ ] Prueba manual contra el servicio de Data Science: enviar texto y recibir respuesta JSON
- [ ] Configurar `OciStorageConfig` con las credenciales OCI (ObjectStorageClient) — pendiente credenciales, stub activo

#### BE-4 | API Contracts + Project Setup
- [x] Redactar y compartir el contrato de DTOs: `ContenidoRequest`, `ContenidoResponse`, `ArchivoResponse`
- [x] Crear `GlobalExceptionHandler` con `@ControllerAdvice` para 400, 401, 403, 404, 500
- [x] Crear `ErrorResponse` DTO
- [x] Configurar Actuator: exponer `/actuator/health`
- [x] Verificar que el proyecto compila — BUILD SUCCESS 33 archivos, `/actuator/health` UP

#### FE-1 | Project Setup
- [ ] Inicializar proyecto frontend (React + Vite o el stack elegido)
- [ ] Configurar routing y layout base
- [ ] Implementar pantalla de Login con formulario email/password
- [ ] Implementar pantalla de Register
- [ ] Integrar con Supabase Auth directamente desde el frontend para obtener el JWT
- [ ] Guardar JWT en localStorage/sessionStorage y adjuntarlo en `Authorization: Bearer <token>`

#### FE-2 | Clasificacion Setup
- [ ] Implementar servicio HTTP base (axios/fetch) con interceptor que adjunta el JWT
- [ ] Implementar manejo de errores HTTP global (401 → redirigir a login)
- [ ] Crear pantalla "Clasificar Contenido" con campos titulo y texto (estructura, sin conectar aun)
- [ ] Definir los tipos TypeScript para `ContenidoRequest` y `ContenidoResponse` segun el contrato de API

#### FE-3 | Componentes Base + Archivos Setup
- [ ] Crear la libreria de componentes compartidos: Button, Input, Card, Spinner, Badge, Alert
- [ ] Definir paleta de colores, tipografia y estilos globales (variables CSS o tokens)
- [ ] Crear pantalla "Mis Archivos" con estructura base (sin conectar aun)
- [ ] Definir los tipos TypeScript para `ArchivoResponse` segun el contrato de API

---

### Dia 3-4 — Integracion core

#### BE-1 | Auth Endpoints
- [x] Implementar `AuthController` — `POST /auth/register` y `POST /auth/login`
- [x] Implementar `SupabaseAuthClient` que delega a GoTrue (`/auth/v1/signup`, `/auth/v1/token`)
- [x] Manejar respuesta de GoTrue y mapear al `SupabaseAuthResponse` propio
- [ ] Prueba: register → login → recibir access_token funcional — pendiente credenciales Supabase

#### BE-2 | ContenidoService
- [x] Implementar `ContenidoService.clasificar(request, userId)`:
  1. Llamar a `MlClient.predict(texto)`
  2. Mapear respuesta del ML al modelo `Contenido`
  3. Persistir en PostgreSQL con `ContenidoRepository.save()`
  4. Retornar `ContenidoResponse`
- [x] Implementar `CategoriaRepository` con query para contar documentos por categoria (JPQL en ContenidoRepository)
- [x] Implementar `CategoriaService.listarConConteo()`

#### BE-3 | OCI Storage
- [x] Implementar `OciStorageClient.upload(bucketName, objectName, inputStream, contentType)` — stub activo
- [ ] Implementar `OciStorageClient` real con OCI Java SDK — pendiente credenciales OCI
- [ ] Prueba manual: subir un archivo de prueba y verificar que aparece en el bucket de OCI

#### BE-4 | ContenidoController
- [x] Implementar `POST /api/contenido` con `@Valid` sobre `ContenidoRequest`
- [x] Extraer `userId` del `SecurityContext` con `@AuthenticationPrincipal`
- [x] Llamar a `ContenidoService.clasificar()` y retornar `ContenidoResponse`
- [x] Implementar `GET /api/categorias` con `CategoriaService.listarConConteo()`
- [ ] Prueba con curl/Postman: flujo completo con JWT valido — pendiente credenciales Supabase

#### FE-1 | Dashboard Base
- [ ] Implementar ruta protegida (redirect a login si no hay JWT)
- [ ] Implementar Dashboard con lista de contenidos clasificados del usuario (cards con categoria + keywords)
- [ ] Implementar sidebar o tabs de categorias (datos estaticos por ahora, conectar en Sprint 2)
- [ ] Implementar estado de carga (skeleton/spinner) y estado vacio
- [ ] Implementar logout (limpiar JWT + redirect)

#### FE-2 | Formulario de Clasificacion Conectado
- [ ] Conectar pantalla "Clasificar Contenido" con `POST /api/contenido`
- [ ] Mostrar resultado en pantalla: categoria con badge de color, probabilidad en porcentaje, lista de palabras clave
- [ ] Mostrar contenidos relacionados si vienen en la respuesta
- [ ] Manejar errores del backend (400 → mostrar en el campo, 401 → redirigir, 500 → mensaje generico)

#### FE-3 | Upload de Archivos Conectado
- [ ] Implementar file picker (o drag & drop) en la pantalla "Mis Archivos"
- [ ] Conectar con `POST /api/archivos` (multipart/form-data)
- [ ] Mostrar barra de progreso durante la carga
- [ ] Mostrar la URL resultante con boton de copiar
- [ ] Manejar error de tipo de archivo no permitido con mensaje claro

---

### Dia 5 — Integration Day (Sprint Review interno)
> Todos integran sus ramas en `develop`. Objetivo: el flujo completo funciona de punta a punta.

- [ ] BE-1 + BE-4: verificar que el filtro JWT bloquea correctamente en los controllers
- [ ] BE-2 + BE-3: verificar que `ContenidoService` llama al ML y persiste correctamente
- [ ] BE-4 + FE-2: verificar que el frontend llama a `POST /api/contenido` y muestra el resultado
- [ ] BE-4 + FE-3: verificar que el upload de archivos llega al backend (aunque OCI no este listo aun)
- [ ] FE-1 + BE-1: verificar que login/register desde el frontend genera un JWT que Spring acepta
- [ ] FE-3: verificar que los componentes base (Button, Input, Card) son usables por FE-1 y FE-2
- [ ] Identificar y registrar blockers para el Sprint 2
- [ ] Demo interna del flujo: register → login → clasificar texto → ver resultado

---

## Sprint 2 — Semana 2: Features completas + Testing
**Objetivo:** Todos los endpoints implementados, frontend completo, suite de pruebas cubriendo casos criticos.
**Definition of Done del Sprint:** App deployada (o lista para demo), cobertura de tests en features criticas.

### Dia 6-7 — Features restantes

#### BE-1 | Hardening de seguridad
- [ ] Revisar configuracion CORS para aceptar el origen del frontend
- [ ] Agregar manejo de excepciones de JWT expirado vs JWT invalido (mensajes distintos)
- [ ] Verificar que rutas de actuator no expongan datos sensibles
- [ ] Documentar las variables de entorno requeridas en un `.env.example`

#### BE-2 | Features de dominio
- [ ] Implementar `ContenidoService.buscar(query, userId)` — busqueda por palabras clave en la DB
- [ ] Implementar `ContenidoService.procesarLote(lista, userId)` — iterar y clasificar cada item
- [ ] Implementar `ArchivoService.subir(file, userId)` — llama a OCI y persiste metadata
- [ ] Implementar `ArchivoService.listar(userId)` y `ArchivoService.obtenerUrl(id, userId)`

#### BE-3 | Integracion OCI completa
- [ ] Conectar `ArchivoService` con `OciStorageClient` (upload real a bucket `OCI_FILES_BUCKET`)
- [ ] Implementar listado de objetos desde OCI si aplica
- [ ] Prueba end-to-end: subir PDF → URL en respuesta → descargar desde esa URL
- [ ] Agregar timeout y manejo de error si OCI no responde (fallback con mensaje claro)

#### BE-4 | Endpoints restantes
- [ ] Implementar `POST /api/contenido/lote`
- [ ] Implementar `GET /api/contenido/buscar?q=`
- [ ] Implementar `POST /api/archivos` (multipart/form-data)
- [ ] Implementar `GET /api/archivos` y `GET /api/archivos/{id}`
- [ ] Validar tipos de archivo permitidos en el upload (PDF, TXT, MD, DOCX)

#### FE-1 | Dashboard completo
- [ ] Conectar lista de categorias con conteo real (llama a `GET /api/categorias`)
- [ ] Implementar buscador global por palabras clave (llama a `GET /api/contenido/buscar`)
- [ ] Mostrar resultados de busqueda en el Dashboard (filtrar cards existentes)
- [ ] Navegacion entre secciones: Dashboard / Clasificar / Archivos (menu lateral o navbar)
- [ ] Pulir responsive: que funcione en mobile y desktop

#### FE-2 | Proceso por lote + UX de clasificacion
- [ ] Implementar pantalla "Clasificar en lote" — textarea con multiples textos (uno por bloque)
- [ ] Conectar con `POST /api/contenido/lote`
- [ ] Mostrar resultados del lote en una tabla o lista expandible
- [ ] Agregar feedback visual despues de clasificar: notificacion de exito y redireccion al Dashboard
- [ ] Pulir el flujo completo de clasificacion individual: estado vacio, loading, error, exito

#### FE-3 | Archivos completo + UX global
- [ ] Conectar listado de archivos con `GET /api/archivos` — mostrar tabla con nombre, tipo, tamano, fecha
- [ ] Implementar boton de descarga/ver por archivo (llama a `GET /api/archivos/{id}`)
- [ ] Pulir el estado vacio de "Mis Archivos" (ilustracion o mensaje con call-to-action)
- [ ] Revisar consistencia visual en toda la app: espaciado, colores, tipografia
- [ ] Asegurarse de que todos los estados de error muestran el componente `Alert` de manera uniforme

---

### Dia 8 — Testing

#### BE-4 coordina, todos contribuyen

**Pruebas unitarias (JUnit 5 + Mockito):**
- [ ] `JwtServiceTest` — token valido, expirado, firma incorrecta, claims faltantes
- [ ] `ContenidoServiceTest` — mockear `MlClient` y `ContenidoRepository`, verificar logica de mapeo
- [ ] `ArchivoServiceTest` — mockear `OciStorageClient` y `ArchivoRepository`
- [ ] `MlClientTest` — mockear `RestClient`, verificar serializacion/deserializacion del request/response
- [ ] `GlobalExceptionHandlerTest` — verificar que cada excepcion retorna el HTTP status correcto

**Pruebas de integracion (Spring Boot Test + `@SpringBootTest`):**
- [ ] `ContenidoControllerIntegrationTest`:
  - POST sin JWT → 401
  - POST con JWT valido + body invalido → 400 con mensaje de error
  - POST con JWT valido + body valido → 200 con `ContenidoResponse`
- [ ] `ArchivoControllerIntegrationTest`:
  - POST multipart sin JWT → 401
  - POST multipart con JWT valido → 200 con `ArchivoResponse`
- [ ] `AuthControllerIntegrationTest`:
  - POST /auth/login con credenciales correctas → 200 con token
  - POST /auth/login con credenciales incorrectas → 401

**Meta minima de cobertura:**
- Services: 80%
- Controllers: 70%
- Security filters: 90%

---

### Dia 9 — Pre-demo: integracion final y deploy

- [ ] Merge de todas las ramas a `develop`, resolver conflictos
- [ ] `docker compose up -d` en entorno de staging — verificar que todos los servicios levantan
- [ ] Smoke test completo del flujo:
  1. Register desde el frontend
  2. Login y obtencion de JWT
  3. Clasificar un texto desde el UI
  4. Subir un archivo PDF
  5. Buscar contenido por keyword
  6. Ver categorias en el dashboard
- [ ] Verificar `/actuator/health` responde `UP`
- [ ] Ajustar CORS si el frontend esta en dominio/puerto distinto al backend
- [ ] Completar `.env.example` con todas las variables necesarias
- [ ] Actualizar README si hay cambios en el setup

---

### Dia 10 — Buffer + Demo final

- [ ] Correccion de bugs criticos encontrados en el smoke test
- [ ] Ensayo de la demo (5 min max): quien habla, que muestra, en que orden
- [ ] Preparar capturas o video de respaldo por si hay problemas de red en la demo
- [ ] Subir codigo final al repositorio

---

## Tablero de Issues sugerido (GitHub Projects o Trello)

Columnas:
```
Backlog → Sprint 1 → En progreso → En revision (PR) → Hecho
```

Etiquetas:
- `backend` / `frontend`
- `security` / `domain` / `integration` / `api`
- `feature` / `test` / `bug` / `chore`
- `blocker` (para lo que frena a otros)

---

## Contrato de API — Referencia rapida

### POST /api/contenido
```json
// Request
{ "titulo": "string", "texto": "string (min 20 chars)" }

// Response 200
{
  "id": "uuid",
  "categoria": "Backend | Frontend | DevOps | Data Science | ...",
  "probabilidad": 0.89,
  "palabras_clave": ["Java", "Spring Boot"],
  "contenidos_relacionados": [{ "id": "uuid", "titulo": "string", "similitud": 0.76 }],
  "procesado_en": "2026-07-28T00:00:00Z"
}

// Response 400
{ "error": "VALIDATION_ERROR", "mensaje": "El campo texto es requerido" }

// Response 401
{ "error": "UNAUTHORIZED", "mensaje": "Token JWT invalido o expirado" }
```

### POST /api/archivos (multipart/form-data)
```json
// Request: campo "file" (PDF, TXT, MD, DOCX — max 10MB)

// Response 200
{
  "id": "uuid",
  "nombre": "documento.pdf",
  "url": "https://objectstorage.sa-saopaulo-1.oraclecloud.com/...",
  "tamano": 1048576,
  "tipo": "application/pdf",
  "subido_en": "2026-07-28T00:00:00Z"
}
```

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|-----------|
| OCI Object Storage tarda en configurarse | Alta | Alto | BE-3 lo prioriza el Dia 1. Si falla, usar almacenamiento local temporalmente para no bloquear el resto |
| El endpoint `/predict` de Data Science no esta listo | Media | Alto | BE-3 crea un mock del ML Client (respuesta hardcodeada) para que BE-2 y BE-4 no se bloqueen |
| JWT de Supabase no valida correctamente | Media | Alto | BE-1 escribe prueba unitaria el Dia 1 antes de integrar con los demas |
| Conflictos de merge al integrar | Alta | Medio | Cada dev trabaja en su propia rama. Integration Day el Dia 5 para resolver todo junto |
| Frontend no recibe CORS del backend | Media | Medio | BE-1 configura CORS desde el primer dia con el origen del frontend |
| No hay tiempo para testing | Alta | Alto | Testing arranca el Dia 8, no el ultimo dia. BE-4 es responsable de no ceder ese tiempo |

---

## Ceremoniass Scrum (adaptadas a hackathon)

| Ceremonia | Cuando | Duracion | Formato |
|-----------|--------|----------|---------|
| Daily Standup | Cada manana (9:00 AM) | 15 min | Que hice ayer / Que hago hoy / Tengo blockers? |
| Sprint Review interna | Dia 5 y Dia 9 | 30 min | Demo del flujo funcional al equipo |
| Retrospectiva rapida | Dia 5 | 15 min | Que funciono / Que cambiamos para la semana 2 |
| Sesion de bugs | Dia 9 AM | 1 hora | Toda el equipo en call resolviendo lo que falle |

---

## Checklist de Entrega Final

- [ ] `docker compose up -d` levanta toda la infraestructura sin errores
- [ ] Todos los endpoints del README responden correctamente
- [ ] Frontend conectado al backend en entorno productivo/staging
- [ ] Suite de tests pasa (`mvn test`)
- [ ] `.env.example` con todas las variables documentadas
- [ ] README actualizado con instrucciones de setup
- [ ] Video o capturas de la demo preparadas como respaldo
