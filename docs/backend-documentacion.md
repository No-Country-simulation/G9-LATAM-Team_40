# TechContent AI — Documentación Backend

**Versión:** 0.0.1
**Stack:** Java 17 · Spring Boot 3.2.12 · PostgreSQL · Docker

---

## Descripción general

TechContent AI es una API REST que permite clasificar contenido técnico usando un modelo de machine learning. El usuario sube texto o archivos, el sistema los analiza y devuelve una categoría (Backend, Frontend, DevOps, etc.) junto con palabras clave y probabilidad de clasificación. Todo el contenido queda persistido y asociado al usuario autenticado.

---

## Arquitectura

El proyecto sigue una arquitectura en capas con separación clara de responsabilidades:

```
api/          → Controllers, DTOs, excepciones HTTP
domain/       → Modelos de negocio, repositorios, servicios
integration/  → Clientes externos (ML, Supabase, OCI)
security/     → JWT, filtros, configuración de Spring Security
```

La capa `domain` no conoce ni a los controllers ni a los clientes externos — solo trabaja con sus propios modelos y los resultados que le pasan los servicios de integración. Los controllers se limitan a transformar requests HTTP en llamadas al dominio y devolver la respuesta adecuada.

---

## Stack tecnológico

| Componente | Tecnología |
|---|---|
| Lenguaje | Java 17 |
| Framework | Spring Boot 3.2.12 |
| Seguridad | Spring Security + JWT (JJWT 0.12.6) |
| Autenticación | Supabase Auth (hosted) |
| Base de datos | PostgreSQL (producción) / H2 (tests) |
| ORM | Spring Data JPA + Hibernate |
| Almacenamiento | Oracle OCI Object Storage |
| ML | FastAPI Python (servicio separado) |
| Contenedores | Docker + Docker Compose |
| Build | Maven 3.9+ |
| Cobertura | JaCoCo |

---

## Estructura del proyecto

```
backend/
├── src/main/java/com/techcontent/ai/
│   ├── api/
│   │   ├── controller/        # AuthController, ContenidoController,
│   │   │                      # ArchivoController, CategoriaController
│   │   ├── dto/
│   │   │   ├── request/       # ContenidoRequest, ContenidoLoteRequest
│   │   │   └── response/      # ContenidoResponse, ArchivoResponse,
│   │   │                      # CategoriaResponse, ContenidoRelacionadoResponse
│   │   └── exception/         # GlobalExceptionHandler, excepciones de dominio
│   ├── domain/
│   │   ├── model/             # Contenido, Archivo, Categoria
│   │   ├── repository/        # ContenidoRepository, ArchivoRepository, CategoriaRepository
│   │   └── service/           # ContenidoService, ArchivoService, CategoriaService
│   ├── integration/
│   │   ├── ml/                # MlClient, QueryRequest/Response, trazabilidad
│   │   ├── oci/               # OciStorageClient, OciStorageConfig
│   │   └── supabase/          # SupabaseAuthClient, SupabaseAuthRequest/Response
│   └── security/              # JwtService, JwtAuthFilter, SecurityConfig,
│                              # JwtAuthenticationEntryPoint, JwtAccessDeniedHandler,
│                              # SupabaseUserDetails
└── src/test/                  # Tests unitarios e integración
```

---

## Autenticación y seguridad

### Flujo general

1. El cliente llama a `/auth/register` o `/auth/login`
2. El backend delega en Supabase Auth (hosted) vía `SupabaseAuthClient`
3. Supabase devuelve un JWT firmado con ES256 (ECDSA P-256)
4. El cliente incluye ese token en el header `Authorization: Bearer <token>` en cada request
5. `JwtAuthFilter` intercepta la request, valida el token y setea el contexto de seguridad

### Validación JWT

El `JwtService` soporta dos algoritmos:

- **ES256** (principal): valida usando la clave pública EC obtenida de la JWKS de Supabase en el arranque. La URL de JWKS se configura en `supabase.jwks.url`. Las claves se cachean en memoria por `kid`.
- **HS256** (legacy/local): valida con el secreto simétrico `supabase.jwt.secret`. Útil para entornos de desarrollo que no usen Supabase hosted.

El algoritmo se detecta automáticamente desde el header del JWT (`alg` + `kid`), sin configuración adicional.

### Respuestas de error de autenticación

| Situación | HTTP | Body |
|---|---|---|
| Sin token | 401 | `{"error":"UNAUTHORIZED","mensaje":"Token JWT invalido o ausente"}` |
| Token expirado | 401 | `{"error":"UNAUTHORIZED","mensaje":"Token JWT expirado"}` |
| Token inválido | 401 | `{"error":"UNAUTHORIZED","mensaje":"Token JWT invalido o ausente"}` |
| Sin permisos | 403 | `{"error":"FORBIDDEN","mensaje":"Acceso denegado"}` |

### Endpoints públicos

- `POST /auth/register`
- `POST /auth/login`
- `GET /actuator/health`
- `GET /actuator/info`
- `OPTIONS /**` (preflight CORS)

Todo lo demás requiere Bearer token válido.

---

## API Reference

Base URL: `http://localhost:8080`

### Auth

#### `POST /auth/register`

Registra un nuevo usuario en Supabase.

**Body:**
```json
{
  "email": "usuario@example.com",
  "password": "MiPassword123"
}
```

**Respuesta 200:**
```json
{
  "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6Ii...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

#### `POST /auth/login`

Inicia sesión con un usuario existente.

**Body:** igual que register.

**Respuesta 200:** igual que register.

**Respuesta 401** (credenciales incorrectas):
```json
{
  "error": "UNAUTHORIZED",
  "mensaje": "Credenciales invalidas"
}
```

---

### Contenido

Todos los endpoints de esta sección requieren `Authorization: Bearer <token>`.

#### `POST /api/contenido`

Clasifica un texto usando el servicio ML y lo persiste.

**Body:**
```json
{
  "titulo": "Cómo desarrollar una API REST con Spring Boot",
  "texto": "Spring Boot facilita la creación de APIs REST en Java..."
}
```

Validaciones: `titulo` obligatorio, `texto` obligatorio y mínimo 20 caracteres.

**Respuesta 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "categoria": "Backend",
  "probabilidad": 0.93,
  "palabrasClave": ["Java", "Spring Boot", "API REST"],
  "relacionados": [],
  "procesadoEn": "2026-08-13T09:30:00"
}
```

---

#### `POST /api/contenido/lote`

Clasifica múltiples textos en una sola llamada. Toda la operación es transaccional — si uno falla, se revierten los anteriores.

**Body:**
```json
{
  "contenidos": [
    {
      "titulo": "Introducción a React",
      "texto": "React es una librería de JavaScript..."
    },
    {
      "titulo": "Docker para desarrolladores",
      "texto": "Docker permite empaquetar aplicaciones..."
    }
  ]
}
```

Límite: máximo 20 elementos por lote.

**Respuesta 200:** array de `ContenidoResponse`.

---

#### `GET /api/contenido`

Lista todos los contenidos clasificados por el usuario autenticado.

**Respuesta 200:** array de `ContenidoResponse`.

---

#### `GET /api/contenido/buscar?q={texto}`

Busca contenidos del usuario por keyword.

**Query param:** `q` — texto a buscar.

**Respuesta 200:** array de `ContenidoResponse`.

---

### Archivos

#### `POST /api/archivos`

Sube un archivo al OCI Object Storage.

**Content-Type:** `multipart/form-data`
**Campo:** `file`

Tipos permitidos: PDF, DOCX, TXT. Tamaño máximo: 10 MB.

**Respuesta 200:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "nombre": "documento.pdf",
  "url": "https://objectstorage.../documento.pdf",
  "tamano": 204800,
  "tipo": "application/pdf",
  "subidoEn": "2026-08-13T09:30:00"
}
```

---

#### `GET /api/archivos`

Lista todos los archivos subidos por el usuario autenticado.

**Respuesta 200:** array de `ArchivoResponse`.

---

#### `GET /api/archivos/{id}`

Obtiene los metadatos de un archivo específico.

**Path param:** `id` — UUID del archivo.

**Respuesta 404** si no existe o no pertenece al usuario:
```json
{
  "error": "NOT_FOUND",
  "mensaje": "Archivo no encontrado"
}
```

---

### Categorías

#### `GET /api/categorias`

Lista las categorías disponibles con el conteo de contenidos clasificados en cada una.

**Respuesta 200:**
```json
[
  { "nombre": "Backend", "conteo": 12 },
  { "nombre": "Frontend", "conteo": 7 },
  { "nombre": "DevOps", "conteo": 3 }
]
```

---

### Health

#### `GET /actuator/health`

```json
{ "status": "UP" }
```

---

## Integración con servicios externos

### Supabase Auth

`SupabaseAuthClient` usa `RestClient` para comunicarse con la API de Supabase. Envía dos headers en cada request: `apikey` (anon key) y `Authorization: Bearer {anonKey}`. Las rutas son `/auth/v1/signup` y `/auth/v1/token?grant_type=password`.

Los errores 4xx de Supabase se mapean a excepciones de dominio (`InvalidCredentialsException`) con respuesta HTTP 401.

### Servicio GraphRAG (Python/FastAPI)

`MlClient` llama a `POST /api/v1/query` del servicio GraphRAG con `{ "pregunta": "..." }`. Recibe la respuesta generada, el tiempo de procesamiento y la trazabilidad de las secciones recuperadas. Los errores 5xx se mapean a `MlServiceException` → respuesta HTTP 503.

### OCI Object Storage

`OciStorageClient` maneja la subida de archivos binarios al bucket configurado. La integración usa el SDK oficial de Oracle (`oci-java-sdk-objectstorage:3.47.0`).

---

## Variables de entorno

| Variable | Descripción | Requerida |
|---|---|---|
| `SUPABASE_AUTH_URL` | URL base del proyecto Supabase (sin `/auth/v1/`) | Sí |
| `SUPABASE_ANON_KEY` | Clave pública anon de Supabase | Sí |
| `SUPABASE_SERVICE_KEY` | Clave service_role de Supabase | Sí |
| `SUPABASE_JWT_SECRET` | Secret para validación HS256 (legacy) | No* |
| `SUPABASE_JWKS_URL` | URL JWKS para validación ES256 | No* |
| `SPRING_DATASOURCE_URL` | JDBC URL de PostgreSQL | Sí |
| `SPRING_DATASOURCE_USERNAME` | Usuario de la DB | Sí |
| `SPRING_DATASOURCE_PASSWORD` | Contraseña de la DB | Sí |
| `ML_SERVICE_URL` | URL del servicio ML Python | Sí |
| `OCI_CLI_REGION` | Región de OCI | Para archivos |
| `OCI_CLI_TENANCY` | OCID del tenancy | Para archivos |
| `OCI_CLI_USER` | OCID del usuario OCI | Para archivos |
| `OCI_CLI_FINGERPRINT` | Fingerprint de la clave OCI | Para archivos |
| `OCI_CLI_KEY_FILE` | Path a la clave privada OCI | Para archivos |
| `OCI_FILES_BUCKET` | Nombre del bucket de archivos | Para archivos |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS permitidos (default: `*`) | No |

*Al menos uno de `SUPABASE_JWT_SECRET` o `SUPABASE_JWKS_URL` debe estar configurado.

---

## Levantar el proyecto

### Con Docker (recomendado)

```bash
# 1. Copiá el archivo de ejemplo y completá los valores reales
cp docs/env.example .env

# 2. Levantá los servicios necesarios
docker compose up -d backend db ml-service

# 3. Verificá que esté up
curl http://localhost:8080/actuator/health
```

### Local (desarrollo)

```bash
cd backend
mvn spring-boot:run
```

Requiere PostgreSQL corriendo localmente y las variables de entorno configuradas.

### Tests

```bash
cd backend
mvn clean test
```

60 tests, sin dependencias externas (H2 in-memory + mocks).

---

## Manejo de errores

Todos los errores siguen el mismo formato:

```json
{
  "error": "CODIGO_ERROR",
  "mensaje": "Descripción legible del problema"
}
```

| Código | HTTP | Cuándo ocurre |
|---|---|---|
| `UNAUTHORIZED` | 401 | Token ausente, inválido o expirado |
| `FORBIDDEN` | 403 | Token válido pero sin permisos |
| `NOT_FOUND` | 404 | Recurso no encontrado |
| `BAD_REQUEST` | 400 | Validación fallida |
| `INTERNAL_ERROR` | 500 | Error no controlado |
| `SERVICE_UNAVAILABLE` | 503 | Servicio ML no disponible |

---

## Tests

| Clase | Tipo | Cobertura |
|---|---|---|
| `JwtServiceTest` | Unitario | HS256 y ES256, valid/expired/invalid, extractors |
| `JwtAuthFilterTest` | Unitario | Sin token, token válido, token inválido |
| `SupabaseUserDetailsTest` | Unitario | Constructor, getters, authorities |
| `JwtAccessDeniedHandlerTest` | Unitario | Respuesta 403 JSON |
| `ContenidoServiceTest` | Unitario | clasificar, lote, buscar, listar |
| `ArchivoServiceTest` | Unitario | subir, validaciones, listar, obtener |
| `MlClientTest` | `@RestClientTest` | predict ok, error 5xx, connection refused |
| `GlobalExceptionHandlerTest` | MockMvc standalone | Todos los handlers de error |
| `ContenidoControllerIntegrationTest` | `@WebMvcTest` | Auth requerida, request válida/inválida |
| `ArchivoControllerIntegrationTest` | `@WebMvcTest` | Upload, listar, sin auth |
| `AuthControllerIntegrationTest` | `@WebMvcTest` | Register, login, errores |
| `TechContentAiApplicationTests` | `@SpringBootTest` | Contexto de Spring carga correctamente |

**Total: 60 tests — 0 errores**
