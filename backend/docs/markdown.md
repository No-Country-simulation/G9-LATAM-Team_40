# Backend — TechContent AI

API REST en Java 17 + Spring Boot 3.2 para la organización inteligente de contenido técnico.
Orquesta la validación de entrada, autenticación JWT con Supabase, persistencia en PostgreSQL, integración con el Motor ML (FastAPI) y almacenamiento en OCI Object Storage.

---

## Division en 4 Partes

```
com.techcontent.ai/
├── 1. api/          → Capa de Presentacion (Controllers, DTOs, validacion)
├── 2. security/     → Capa de Seguridad   (JWT Supabase, Spring Security)
├── 3. domain/       → Capa de Dominio     (Entities, Repositories, Services)
└── 4. integration/  → Capa de Integracion (ML Client, OCI Storage, Supabase Auth)
```

---

## Parte 1 — API (Capa de Presentacion)

**Paquete:** `com.techcontent.ai.api`

Punto de entrada de todas las peticiones HTTP. Responsable de recibir, validar y transformar los datos antes de delegarlos al dominio. No contiene logica de negocio.

### Responsabilidades
- Definir los endpoints REST publicos
- Validar la estructura de los requests con Bean Validation (`@Valid`)
- Mapear entidades de dominio a DTOs de respuesta
- Manejar errores HTTP con `@ControllerAdvice`

### Estructura interna

```
api/
├── controller/
│   ├── ContenidoController.java     # POST /api/contenido, POST /api/contenido/lote, GET /api/contenido/buscar
│   ├── ArchivoController.java       # POST /api/archivos, GET /api/archivos, GET /api/archivos/{id}
│   ├── CategoriaController.java     # GET /api/categorias
│   └── AuthController.java          # POST /auth/register, POST /auth/login (proxy a Supabase)
├── dto/
│   ├── request/
│   │   ├── ContenidoRequest.java    # { titulo, texto } con @NotBlank
│   │   └── ContenidoLoteRequest.java
│   └── response/
│       ├── ContenidoResponse.java   # { id, categoria, probabilidad, palabras_clave, contenidos_relacionados, procesado_en }
│       ├── ArchivoResponse.java     # { id, nombre, url, tamano, tipo, subido_en }
│       └── CategoriaResponse.java
└── exception/
    ├── GlobalExceptionHandler.java  # @ControllerAdvice → 400, 401, 403, 404, 500
    └── ErrorResponse.java
```

### Endpoints

| Metodo | Path                        | Descripcion                                      |
|--------|-----------------------------|--------------------------------------------------|
| POST   | `/api/contenido`            | Clasifica un texto y extrae palabras clave       |
| POST   | `/api/contenido/lote`       | Procesa multiples documentos en una sola llamada |
| GET    | `/api/contenido/buscar`     | Busqueda semantica por palabras clave (`?q=`)    |
| POST   | `/api/archivos`             | Sube un archivo a OCI Object Storage             |
| GET    | `/api/archivos`             | Lista archivos del usuario autenticado           |
| GET    | `/api/archivos/{id}`        | Obtiene URL de descarga de un archivo            |
| GET    | `/api/categorias`           | Lista categorias con cantidad de documentos      |
| POST   | `/auth/register`            | Registro delegado a Supabase Auth                |
| POST   | `/auth/login`               | Login y obtencion de JWT delegado a Supabase     |
| GET    | `/actuator/health`          | Health check del servicio                        |

---

## Parte 2 — Security (Capa de Seguridad)

**Paquete:** `com.techcontent.ai.security`

Gestiona la autenticacion y autorizacion de todas las peticiones. Valida los JWT emitidos por Supabase GoTrue sin depender de sesiones en servidor (stateless).

### Responsabilidades
- Configurar Spring Security (CORS, CSRF, reglas de acceso)
- Interceptar cada request y extraer el Bearer token del header `Authorization`
- Validar la firma del JWT contra `SUPABASE_JWT_SECRET`
- Poblar el `SecurityContext` con los datos del usuario autenticado
- Rechazar peticiones sin token o con token invalido con HTTP 401/403

### Estructura interna

```
security/
├── SecurityConfig.java              # @EnableWebSecurity, filtros, reglas de acceso, CORS
├── JwtAuthFilter.java               # OncePerRequestFilter → extrae y valida el JWT
├── JwtService.java                  # Parsea y valida el JWT (firma HS256 con SUPABASE_JWT_SECRET)
└── SupabaseUserDetails.java         # Representa al usuario autenticado (sub, email, rol)
```

### Flujo de autenticacion

```
Request HTTP
    │
    ▼
JwtAuthFilter.doFilterInternal()
    │  extrae "Authorization: Bearer <token>"
    ▼
JwtService.validateToken()
    │  verifica firma con SUPABASE_JWT_SECRET
    │  verifica expiracion (exp claim)
    ▼
SecurityContextHolder.setAuthentication()
    │  almacena SupabaseUserDetails en el contexto
    ▼
Controller recibe la peticion con usuario autenticado
```

### Configuracion de acceso

| Path                  | Acceso          |
|-----------------------|-----------------|
| `/auth/**`            | Publico         |
| `/actuator/health`    | Publico         |
| `/api/**`             | Requiere JWT    |

### Variables de entorno requeridas

| Variable               | Descripcion                          |
|------------------------|--------------------------------------|
| `SUPABASE_JWT_SECRET`  | Secreto HS256 para validar el token  |
| `SUPABASE_ANON_KEY`    | Clave anonima de Supabase            |
| `SUPABASE_SERVICE_KEY` | Clave de servicio de Supabase        |

---

## Parte 3 — Domain (Capa de Dominio)

**Paquete:** `com.techcontent.ai.domain`

Nucleo de la aplicacion. Contiene las entidades de negocio, los repositorios JPA y los servicios que orquestan la logica principal. Es independiente de frameworks web y de detalles de infraestructura.

### Responsabilidades
- Modelar las entidades del negocio (Contenido, Archivo, Categoria)
- Persistir y consultar datos en PostgreSQL a traves de Spring Data JPA
- Implementar la logica de negocio: orchestar la clasificacion, la busqueda semantica y la gestion de archivos
- Delegar al `MlClient` y al `OciStorageClient` (de la capa de Integracion)

### Estructura interna

```
domain/
├── model/
│   ├── Contenido.java               # @Entity: id, titulo, texto, categoria, probabilidad, palabras_clave, userId, procesado_en
│   ├── Archivo.java                 # @Entity: id, nombre, url, tamano, tipo, userId, subido_en
│   └── Categoria.java               # @Entity: id, nombre, descripcion
├── repository/
│   ├── ContenidoRepository.java     # JpaRepository + busqueda por userId, por categoria, busqueda full-text
│   ├── ArchivoRepository.java       # JpaRepository + filtro por userId
│   └── CategoriaRepository.java     # JpaRepository + count por categoria
└── service/
    ├── ContenidoService.java        # clasificar(), procesarLote(), buscar() — llama a MlClient
    ├── ArchivoService.java          # subir(), listar(), obtenerUrl() — llama a OciStorageClient
    └── CategoriaService.java        # listarConConteo()
```

### Modelo de datos

```
contenidos
├── id              UUID (PK)
├── user_id         UUID (FK → Supabase auth.users)
├── titulo          TEXT NOT NULL
├── texto           TEXT NOT NULL
├── categoria       VARCHAR(50)
├── probabilidad    DECIMAL(5,4)
├── palabras_clave  TEXT[] (array de strings)
└── procesado_en    TIMESTAMPTZ

archivos
├── id              UUID (PK)
├── user_id         UUID (FK → Supabase auth.users)
├── nombre          VARCHAR(255)
├── url             TEXT
├── tamano          BIGINT
├── tipo            VARCHAR(100)
└── subido_en       TIMESTAMPTZ
```

### Configuracion JPA

| Propiedad                             | Valor             |
|---------------------------------------|-------------------|
| `spring.jpa.hibernate.ddl-auto`       | `update`          |
| `spring.jpa.properties.hibernate.dialect` | `PostgreSQLDialect` |
| Base de datos                         | PostgreSQL 15 (Supabase) |

---

## Parte 4 — Integration (Capa de Integracion)

**Paquete:** `com.techcontent.ai.integration`

Adapta la comunicacion con servicios externos. Implementa los clientes HTTP y los adaptadores necesarios para conectarse al Motor ML (FastAPI), a OCI Object Storage y a Supabase Auth. Ningun otro paquete conoce los detalles de estos servicios externos.

- Enviar consultas al pipeline GraphRAG y recibir respuesta, categoría, keywords y trazabilidad
- Subir, descargar y listar archivos en OCI Object Storage
- Delegar registro y login a Supabase Auth (GoTrue)
- Aislar los detalles de red del resto de la aplicación

### Estructura interna

```
integration/
├── ml/
│   ├── MlClient.java                # RestClient → POST http://ml-service:5000/api/v1/query
│   ├── QueryRequest.java            # { pregunta }
│   ├── QueryResponse.java           # { pregunta, respuesta, trazabilidad, tiempo_segundos }
│   └── TrazabilidadSeccionDto.java  # Fuente recuperada del grafo
├── oci/
│   ├── OciStorageClient.java        # SDK OCI → upload, download, listObjects
│   └── OciStorageConfig.java        # Configura ObjectStorageClient con credenciales OCI
└── supabase/
    ├── SupabaseAuthClient.java      # RestClient → POST /auth/v1/signup, /auth/v1/token
    ├── SupabaseAuthRequest.java     # { email, password }
    └── SupabaseAuthResponse.java    # { access_token, refresh_token, user }
```

### MlClient — flujo de consulta GraphRAG

```
ContenidoService.clasificar(texto)
    │
    ▼
MlClient.queryGraphRag(texto)
    │  POST http://ml-service:5000/api/v1/query
    │  Body: { "pregunta": "..." }
    ▼
FastAPI GraphRAG
    │  Embeddings + recuperación sobre índice de grafo
    │  Generación de respuesta con el LLM configurado
    ▼
QueryResponse { pregunta, respuesta, trazabilidad, tiempo_segundos }
    │
    ▼
ContenidoService persiste resultado y retorna al Controller
```

### OciStorageClient — flujo de archivos

```
ArchivoService.subir(file, userId)
    │
    ▼
OciStorageClient.upload(bucketName, objectName, inputStream)
    │  Bucket: OCI_FILES_BUCKET
    │  Region: OCI_CLI_REGION
    ▼
OCI Object Storage (S3-compatible)
    │  Retorna URL publica del objeto
    ▼
ArchivoService persiste metadata en PostgreSQL
```

### Variables de entorno requeridas

| Variable              | Descripcion                                  |
|-----------------------|----------------------------------------------|
| `ML_SERVICE_URL`      | URL del Motor ML (default: `http://localhost:5000`) |
| `SUPABASE_AUTH_URL`   | URL de Supabase GoTrue (default: `http://localhost:9999`) |
| `OCI_CLI_USER`        | OCID del usuario OCI                         |
| `OCI_CLI_TENANCY`     | OCID del tenancy OCI                         |
| `OCI_CLI_REGION`      | Region OCI (ej: `sa-santiago-1`)             |
| `OCI_CLI_FINGERPRINT` | Fingerprint de la API Key OCI                |
| `OCI_CLI_KEY_FILE`    | Path a la clave privada OCI                  |
| `OCI_FILES_BUCKET`    | Nombre del bucket para archivos de usuario   |

---

## Resumen de Dependencias entre Capas

```
[API] ──────────► [Domain] ──────────► [Integration]
  │                   │                      │
  │  Controllers       │  Services            │  MlClient
  │  DTOs              │  Entities            │  OciStorageClient
  │  Exception Handler │  Repositories        │  SupabaseAuthClient
  │                   │                      │
  └── [Security] ─────┘                      │
        JwtAuthFilter                         │
        JwtService                  [Servicios Externos]
        SecurityConfig               FastAPI :5000
                                     OCI Object Storage
                                     Supabase Auth :9999
                                     PostgreSQL :5432
```

### Regla de dependencias

- `api` conoce a `domain`, NO conoce a `integration` ni a `security`
- `domain` conoce a `integration` (via interfaces), NO conoce a `api`
- `security` es transversal: intercepta antes de que llegue a `api`
- `integration` no conoce a nadie: solo adapta servicios externos

---

## Stack Tecnico

| Tecnologia              | Version  | Uso                                          |
|-------------------------|----------|----------------------------------------------|
| Java                    | 17       | Lenguaje principal                           |
| Spring Boot             | 3.2.5    | Framework base                               |
| Spring Web              | -        | REST Controllers, RestClient                 |
| Spring Security         | -        | Filtros JWT, autorizacion                    |
| Spring Data JPA         | -        | Repositorios, mapeo ORM                      |
| Spring Validation       | -        | Bean Validation en DTOs                      |
| Spring Actuator         | -        | Health check `/actuator/health`              |
| PostgreSQL              | 15       | Base de datos (Supabase)                     |
| Lombok                  | -        | Reduccion de boilerplate                     |
| Maven                   | 3.8+     | Build y gestion de dependencias              |
| OCI Java SDK            | -        | Acceso a Object Storage                      |
| JUnit 5 + Mockito       | -        | Pruebas unitarias e integracion              |
