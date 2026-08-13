# Revisión Técnica — Sprint BE-1, BE-2, BE-4

**Fecha:** 2026-08-10
**Estado final:** ✅ 44/44 tests pasando — BUILD SUCCESS

---

## Resumen ejecutivo

Se revisaron las tareas BE-1 (Autenticación y Seguridad), BE-2 (Dominio y Persistencia) y BE-4 (API REST, Validaciones, Testing). Se identificaron y resolvieron 18 issues entre críticos, medios y menores. El build compila, todos los tests pasan sobre Java 25.

---

## Issues resueltos

### 🔴 Críticos

#### 1. Archivos duplicados con implementaciones incompatibles
- **Problema:** Existía `api/ContenidoController.java` (stub viejo mapeado a `/api/contenidos`) junto al controller real en `api/controller/ContenidoController.java` (mapeado a `/api/contenido`). Misma situación con DTOs y el `GlobalExceptionHandler`.
- **Fix:** Se eliminaron los archivos duplicados:
  - `api/ContenidoController.java`
  - `dto/ContenidoRequest.java`, `dto/ContenidoResponse.java`, `dto/ArchivoResponse.java`, `dto/CategoriaResponse.java`
  - `exception/GlobalExceptionHandler.java` (viejo, retornaba `Map<String,String>`)
  - `api/ContenidoControllerTest.java` (tests rotos con imports incorrectos)

#### 2. Lombok no procesaba con Java 25
- **Problema:** Lombok 1.18.32 no es compatible con Java 25. El annotation processor falla en auto-discovery, causando `cannot find symbol: variable log`, `cannot find symbol: method builder()`.
- **Fix en `pom.xml`:**
  - Override de versión a `lombok.version=1.18.42`
  - Configuración explícita de `annotationProcessorPaths` en `maven-compiler-plugin`

#### 3. Mockito inline mock maker roto con Java 25
- **Problema:** Mockito 5.x usa `InlineMockMaker` por defecto, que requiere instrumentar `java.lang.Object` vía byte-buddy agent. Java 25 bloquea esto → 23 tests fallaban con `Could not modify all classes`.
- **Fix:**
  - Creación de `src/test/resources/mockito-extensions/org.mockito.plugins.MockMaker` con contenido `mock-maker-subclass`
  - Adición de JVM args en `maven-surefire-plugin`: `-XX:+EnableDynamicAgentLoading --add-opens java.base/java.lang=ALL-UNNAMED ...`

#### 4. Respuestas de error 401 sin JSON (solo texto vacío)
- **Problema:** `AuthenticationEntryPoint` por defecto retornaba 401 sin body. Los tests de integración esperaban `{"error":"UNAUTHORIZED","mensaje":"..."}`.
- **Fix en `SecurityConfig.java`:** `AuthenticationEntryPoint` inline que escribe JSON con distinción EXPIRED vs. sin token/inválido.

#### 5. `GlobalExceptionHandler` incompleto
- **Problema:** Faltaban handlers para `InvalidCredentialsException` (→ 401), `MlServiceException` (→ 503), y `HttpClientErrorException`.
- **Fix:** Handlers agregados con respuesta consistente en `ErrorResponse`.

#### 6. `MlClient` y `SupabaseAuthClient` sin manejo de errores HTTP
- **Problema:** Un error 4xx/5xx del servicio ML o Supabase propagaba `RestClientException` genérica sin mapear al dominio.
- **Fix:**
  - `MlClient`: captura `HttpServerErrorException` → `MlServiceException`; `ResourceAccessException` → `MlServiceException`
  - `SupabaseAuthClient`: captura `HttpClientErrorException` → `InvalidCredentialsException` (signIn) / `IllegalArgumentException` (signUp)

### 🟡 Medios

#### 7. `MlClient` y `SupabaseAuthClient` con `RestClient` hardcodeado (no testeable)
- **Problema:** Los clientes creaban `RestClient.create(url)` directamente en el constructor, haciendo imposible el mocking con `MockRestServiceServer`.
- **Fix:** Cambio a inyección de `RestClient.Builder builder` (Spring auto-configura timeouts + permite test overrides).

#### 8. Endpoint de health con información sensible pública
- **Problema:** `management.endpoint.health.show-details=always` exponía detalles de DB y servicios a cualquiera sin autenticar.
- **Fix:** Cambiado a `show-details=when_authorized`.

#### 9. CORS hardcodeado a `*`
- **Problema:** Origen `*` en producción no es aceptable y no permite credentials.
- **Fix:** `cors.allowed-origins=${CORS_ALLOWED_ORIGINS:*}` configurable por variable de entorno.

#### 10. Sin timeouts en clientes HTTP
- **Problema:** Sin timeout, una llamada al servicio ML o Supabase podría bloquear un thread indefinidamente.
- **Fix:** `spring.http.client.connect-timeout=5s` y `spring.http.client.read-timeout=30s` en `application.properties`.

#### 11. `procesarLote` sin transacción
- **Problema:** Si uno de los items del lote fallaba, los anteriores ya persistidos quedaban guardados (estado inconsistente).
- **Fix:** `@Transactional` en `ContenidoService.procesarLote()`.

#### 12. Tests de integración sin contexto de seguridad real
- **Problema:** `TechContentAiApplicationTests` intentaba levantar el contexto completo conectándose a PostgreSQL, fallando en CI sin DB.
- **Fix:** `@ActiveProfiles("test")` + `src/test/resources/application-test.properties` con H2 in-memory en modo PostgreSQL.

### 🟢 Menores

#### 13. `JwtService` sin distinción entre token expirado e inválido
- **Problema:** Solo retornaba `true/false`. No había forma de dar mensajes de error distintos.
- **Fix:** `TokenValidationResult` enum (`VALID`, `EXPIRED`, `INVALID`) + método `validateToken()`.

#### 14. `JwtAuthFilter` sin propagación del tipo de error JWT
- **Problema:** El filtro rechazaba tokens sin comunicar al `AuthenticationEntryPoint` si era expirado o inválido.
- **Fix:** `request.setAttribute(JWT_ERROR_ATTRIBUTE, "EXPIRED"/"INVALID")` leído en el entry point para el mensaje JSON apropiado.

#### 15. Sin variable de documentación de entorno
- **Fix:** `docs/env.example` con todas las variables de entorno documentadas.

#### 16. Sin Dockerfile para frontend
- **Fix:** `frontend/techisolutions/Dockerfile` con multi-stage build: deps → builder (Next.js standalone) → runner.

---

## Tests nuevos creados

| Clase | Tipo | Tests |
|---|---|---|
| `JwtServiceTest` | Unit | 5 — valid, expired, wrong signature, malformed, no secret |
| `ContenidoServiceTest` | Unit | 4 — clasificar, procesarLote, buscar, listarPorUsuario |
| `ArchivoServiceTest` | Unit | 6 — upload válido, tipo inválido, vacío, muy grande, listar, obtenerPorId |
| `MlClientTest` | `@RestClientTest` | 3 — predict ok, server error → MlServiceException, connection refused |
| `GlobalExceptionHandlerTest` | Standalone MockMvc | 7 — validation, 404, bad request, ML error, invalid credentials, server error |
| `ContenidoControllerIntegrationTest` | `@WebMvcTest` | 4 — sin JWT, JWT expirado, body válido, body inválido |
| `ArchivoControllerIntegrationTest` | `@WebMvcTest` | 4 — sin JWT, JWT válido + archivo, GET lista, GET sin JWT |
| `AuthControllerIntegrationTest` | `@WebMvcTest` | 4 — login ok, credenciales malas, register ok, email duplicado |

**Total: 44 tests — 44 pasando — 0 errores**

---

## Archivos modificados

| Archivo | Cambio |
|---|---|
| `pom.xml` | Lombok 1.18.42, annotationProcessorPaths, maven-surefire-plugin argLine, H2 test dep |
| `src/main/resources/application.properties` | health details, timeouts, cors, oci vars |
| `security/JwtService.java` | TokenValidationResult enum, validateToken() |
| `security/JwtAuthFilter.java` | JWT_ERROR_ATTRIBUTE, usa validateToken() |
| `security/SecurityConfig.java` | AuthenticationEntryPoint JSON, CORS configurable |
| `integration/ml/MlClient.java` | RestClient.Builder injection, manejo errores HTTP |
| `integration/supabase/SupabaseAuthClient.java` | RestClient.Builder injection, manejo errores HTTP |
| `domain/service/ContenidoService.java` | @Transactional en procesarLote |
| `api/exception/GlobalExceptionHandler.java` | Handlers para InvalidCredentials, MlService, HttpClientError |

## Archivos creados

| Archivo | Propósito |
|---|---|
| `integration/ml/MlServiceException.java` | Excepción de dominio para errores del servicio ML |
| `api/exception/InvalidCredentialsException.java` | Excepción para credenciales incorrectas (→ 401) |
| `src/test/resources/application-test.properties` | H2 in-memory para tests |
| `src/test/resources/mockito-extensions/org.mockito.plugins.MockMaker` | SubclassMockMaker para compatibilidad Java 25 |
| `JwtServiceTest.java` | Tests unitarios de JWT |
| `ContenidoServiceTest.java` | Tests unitarios del servicio de contenido |
| `ArchivoServiceTest.java` | Tests unitarios del servicio de archivos |
| `MlClientTest.java` | Tests del cliente ML con MockRestServiceServer |
| `GlobalExceptionHandlerTest.java` | Tests del exception handler global |
| `ContenidoControllerIntegrationTest.java` | Tests de integración del controller de contenido |
| `ArchivoControllerIntegrationTest.java` | Tests de integración del controller de archivos |
| `AuthControllerIntegrationTest.java` | Tests de integración del controller de auth |
| `docs/env.example` | Documentación de variables de entorno |
| `frontend/techisolutions/Dockerfile` | Multi-stage build Next.js + Bun |

## Archivos eliminados

| Archivo | Motivo |
|---|---|
| `api/ContenidoController.java` | Stub duplicado con datos hardcodeados y ruta incorrecta |
| `dto/ContenidoRequest.java` | DTO duplicado del paquete incorrecto |
| `dto/ContenidoResponse.java` | DTO duplicado del paquete incorrecto |
| `dto/ArchivoResponse.java` | DTO duplicado del paquete incorrecto |
| `dto/CategoriaResponse.java` | DTO duplicado del paquete incorrecto |
| `exception/GlobalExceptionHandler.java` | Handler viejo retornando Map sin estructura ErrorResponse |
| `api/ContenidoControllerTest.java` | Tests rotos con imports y assertions incorrectos |

---

# Integración con Supabase Hosted — 2026-08-13

**Estado:** Flujo de autenticación (register/login) verificado end-to-end contra Supabase hosted.

---

## Resumen ejecutivo

Se reemplazó la dependencia del stack local de Supabase (GoTrue + supabase/postgres) por el proyecto hosted en `supabase.co`. El stack local presentaba incompatibilidad de versiones entre `supabase/postgres:15.1.0.147` y `supabase/gotrue:v2.143.0` (tabla `identities` no existente), haciendo inviable continuar con él. Se corrigieron además las cabeceras HTTP faltantes que Supabase hosted exige y se actualizó `docs/env.example` para que las variables documentadas coincidan exactamente con las que usa `application.properties`.

---

## Cambios realizados

### `integration/supabase/SupabaseAuthClient.java`

- **Qué:** Se agregó el header `Authorization: Bearer {anonKey}` junto al ya existente `apikey`.
- **Por qué:** Supabase hosted requiere **ambos** headers en cada request. Sin `Authorization`, el endpoint devuelve `401 Unauthorized` incluso con `apikey` presente.
- **Rutas:** Se mantuvieron `/auth/v1/signup` y `/auth/v1/token?grant_type=password` (prefijo `/auth/v1/` correcto para el API público de Supabase; el prefijo lo agrega Kong en el stack hosted, no GoTrue directamente).

### `docker-compose.yml`

- **Qué:** `SUPABASE_AUTH_URL` del servicio `backend` cambió de `http://supabase-auth:9999` (GoTrue local) a `https://bftvhnxtbahabwykqwni.supabase.co` (Supabase hosted).
- **Por qué:** Eliminación del GoTrue local como destino de autenticación. El backend ahora apunta directamente al proyecto hosted, que ya incluye Kong + GoTrue + todo el stack de auth.

### `docs/env.example`

- **Qué:** Se actualizaron los nombres y valores de ejemplo de las variables de entorno para que coincidan exactamente con los keys que lee `application.properties`.
- **Por qué:** El archivo anterior tenía nombres inconsistentes que generaban confusión al configurar el entorno por primera vez. Ahora sirve como referencia confiable: copiar, completar los valores reales y levantar Docker.

---

## Variables de entorno requeridas (referencia)

| Variable | Origen | Descripción |
|---|---|---|
| `SUPABASE_AUTH_URL` | Supabase dashboard → Project URL | URL base del proyecto (sin `/auth/v1/`) |
| `SUPABASE_ANON_KEY` | Supabase dashboard → API Keys | Clave pública anon |
| `SUPABASE_SERVICE_KEY` | Supabase dashboard → API Keys | Clave service_role (no exponer al cliente) |
| `SUPABASE_JWT_SECRET` | Supabase dashboard → JWT Settings | Secret para validar tokens en el backend |
| `SPRING_DATASOURCE_URL` | Supabase dashboard → Database → Connection string | JDBC URL de la DB |

Ver `docs/env.example` para la lista completa.

---

# Merge origin/main + Soporte ES256 (JWKS) — 2026-08-13

**Estado:** ✅ 60/60 tests pasando — verificación Docker end-to-end completa

---

## Resumen ejecutivo

Se integró el trabajo de todos los integrantes (BE-1 a BE-4 completos: OCI Storage, nuevos DTOs, `JwtAuthenticationEntryPoint`, `JwtAccessDeniedHandler`) mediante merge de `origin/main` → rama `carlos`. Se resolvieron 15 conflictos preservando las correcciones de QA y toda la funcionalidad nueva. Adicionalmente se migró la validación JWT de HS256 a ES256 usando la JWKS pública de Supabase, motivado por la rotación de clave que Supabase realizó en el proyecto hosted.

---

## Resolución de merge (15 conflictos)

### Estrategia aplicada

- **Arquitectura/inyección (HEAD):** `MlClient`, `SupabaseAuthClient` — se mantuvo inyección correcta de `RestClient.Builder`, testeable con `MockRestServiceServer`.
- **Funcionalidad nueva (origin/main):** OCI Storage completo (sin modificar), `JwtAuthenticationEntryPoint`, `JwtAccessDeniedHandler`, `SupabaseUserDetails` con campo `role`, `TechContentAiApplicationTests` con `@MockBean ObjectStorageClient`.
- **Merge manual:** `pom.xml`, `application.properties`, `application-test.properties`, `SecurityConfig`, `JwtAuthFilter`.

### Cambios clave post-merge

| Archivo | Cambio |
|---|---|
| `pom.xml` | OCI SDK 3.47.0, JaCoCo 0.8.12, H2 explícita, postgresql 42.7.3, Lombok 1.18.42 (mantenido) |
| `security/JwtAuthFilter.java` | Agregado `extractRole()` → `SupabaseUserDetails(userId, email, role)` |
| `security/SecurityConfig.java` | Estructura con beans inyectados (origin/main) + CORS configurable (HEAD) |
| `security/JwtAuthenticationEntryPoint.java` | Lee `JWT_ERROR_ATTRIBUTE` para distinguir EXPIRED vs INVALID |
| `application.properties` | Props OCI con env vars: `OCI_NAMESPACE`, `OCI_CLI_REGION`, etc. |
| `application-test.properties` | Props OCI vacías + `preferred_array_jdbc_type=ARRAY` |

---

## Migración JWT: HS256 → ES256 (JWKS)

### Problema

Supabase rotó la clave de firma JWT de HS256 (HMAC simétrico) a ES256 (ECDSA P-256) en el proyecto hosted. La migración es unidireccional desde el dashboard. Los tokens nuevos eran rechazados por el backend con 401.

### Solución

`JwtService` ahora soporta ambos algoritmos en paralelo:

- **ES256:** carga la clave pública EC desde la JWKS de Supabase en `@PostConstruct`, cachea por `kid` en `ConcurrentHashMap`.
- **HS256:** ruta legacy, sigue funcionando para entornos locales/tests.
- La detección del algoritmo se hace inspeccionando el header del JWT (`alg` + `kid`) antes de validar.

**JWKS URL configurada:**
```
supabase.jwks.url=${SUPABASE_JWKS_URL:https://bftvhnxtbahabwykqwni.supabase.co/auth/v1/.well-known/jwks.json}
```

En tests: `supabase.jwks.url=` (vacío → skip, se usa HS256 con secreto de prueba).

### Archivos modificados

| Archivo | Cambio |
|---|---|
| `security/JwtService.java` | Soporte ES256/JWKS: `loadJwks()`, `buildEcPublicKey()`, `resolveKey()` |
| `application.properties` | `supabase.jwks.url` con fallback a JWKS de Supabase hosted |
| `application-test.properties` | `supabase.jwks.url=` (vacío, sin conexión externa en tests) |

### Tests nuevos (ES256)

| Test | Qué verifica |
|---|---|
| `validateToken_tokenES256_conJwksCargadas_deberiaRetornarVALID` | Token ES256 válido con clave EC inyectada |
| `validateToken_tokenES256_sinJwksCargadas_deberiaRetornarINVALID` | Token ES256 sin JWKS → INVALID |
| `validateToken_tokenES256_kidDesconocido_usaClaveDisponible` | Fallback a primera clave cuando el kid no matchea |
| `extractRole_deberiaRetornarElRolDelToken` | Extracción del claim `role` |

**Total tests:** 60 (era 44 antes del merge) — 0 errores — 1 skip (Docker integration, requiere `RUN_ML_DOCKER_TEST=true`)

---

## Actualización de dependencias

| Dependencia | Antes | Después | Motivo |
|---|---|---|---|
| `spring-boot-starter-parent` | 3.2.5 | 3.2.12 | Patch update, soporte OSS vencido en 3.2.5 |

---

## Verificación Docker (end-to-end)

```
docker compose up -d backend db ml-service
```

| Endpoint | Resultado |
|---|---|
| `GET /actuator/health` | `{"status":"UP"}` ✅ |
| `POST /auth/register` | 200 + `access_token` (ES256) ✅ |
| `POST /auth/login` | 200 + `access_token` (ES256) ✅ |
| `GET /api/contenido` sin JWT | 401 `{"error":"UNAUTHORIZED","mensaje":"Token JWT invalido o ausente"}` ✅ |
| `GET /api/contenido` con JWT ES256 | 200 ✅ |

---

## Correcciones adicionales — 2026-08-13

### `docker-compose.yml`

- **Qué:** Se eliminó `supabase-auth` del `depends_on` del servicio `backend`.
- **Por qué:** El contenedor GoTrue local (`supabase/gotrue:v2.143.0`) crashea en loop por incompatibilidad de migración con `supabase/postgres:15.1.0.147` (`operator does not exist: uuid = text`). El backend ya no lo necesita — apunta a Supabase hosted. El servicio sigue definido en el compose para quienes quieran levantarlo manualmente con credenciales locales.

### `docs/TechContent-AI.postman_collection.json`

- **Qué:** Colección de Postman con todos los endpoints del backend.
- **Incluye:** Auth (register/login), Contenido (clasificar, lote, buscar, listar), Archivos (subir, listar, obtener por ID), Categorías (listar), Health check.
- **Feature:** Los requests de register y login guardan el `access_token` automáticamente en la variable `{{token}}` de la colección. Todos los endpoints protegidos la usan via Bearer sin configuración adicional.
