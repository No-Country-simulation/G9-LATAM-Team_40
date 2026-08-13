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
