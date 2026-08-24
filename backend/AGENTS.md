# AGENTS.md — Backend (TechISOlutions)
**Stack:** Java 17 | Spring Boot 3.2.12 | Maven | PostgreSQL | Spring Security | Spring Data JPA | Lombok

Todo agente de IA y todo desarrollador debe leer este archivo antes de generar o modificar codigo en `backend/`.

---

## Estructura de Paquetes

```
src/main/java/com/techcontent/ai/
├── TechContentAiApplication.java   # Entry point, no tocar
├── api/                            # Capa de presentacion
│   ├── controller/                 # @RestController — solo reciben y delegan
│   ├── dto/
│   │   ├── request/                # Records de entrada con @Valid
│   │   └── response/               # Records de salida
│   └── exception/                  # @ControllerAdvice, ErrorResponse
├── security/                       # Capa de seguridad
│   ├── SecurityConfig.java
│   ├── JwtAuthFilter.java
│   ├── JwtService.java             # HS256 + ES256/JWKS
│   ├── JwtAuthenticationEntryPoint.java
│   ├── JwtAccessDeniedHandler.java
│   └── SupabaseUserDetails.java
├── domain/                         # Nucleo del negocio
│   ├── model/                      # Contenido, Archivo, Grafo
│   ├── repository/                 # interfaces JpaRepository
│   └── service/                    # ContenidoService, ArchivoService, CategoriaService, GrafoService
└── integration/                    # Adaptadores a servicios externos
    ├── ml/                         # MlClient → POST /api/v1/query (GraphRAG :5000)
    ├── oci/                        # Cliente OCI Object Storage
    └── supabase/                   # Cliente Supabase Auth (GoTrue :9999)

src/test/java/com/techcontent/ai/
├── security/
├── domain/service/
├── domain/repository/
├── integration/
└── api/controller/
```

---

## Convenciones de Codigo

### Nomenclatura de clases
| Tipo | Sufijo | Ejemplo |
|------|--------|---------|
| Controller REST | `Controller` | `ContenidoController` |
| Servicio de negocio | `Service` | `ContenidoService` |
| Repositorio JPA | `Repository` | `ContenidoRepository` |
| Cliente HTTP externo | `Client` | `MlClient`, `OciStorageClient` |
| Filtro de seguridad | `Filter` | `JwtAuthFilter` |
| Configuracion Spring | `Config` | `SecurityConfig`, `OciStorageConfig` |
| DTO de request | `Request` | `ContenidoRequest` |
| DTO de response | `Response` | `ContenidoResponse` |
| Entidad JPA | sin sufijo | `Contenido`, `Archivo` |

### DTOs — usar Java Records (Java 17)
```java
// Correcto
public record ContenidoRequest(
    @NotBlank String titulo,
    @NotBlank @Size(min = 20) String texto
) {}

// Incorrecto — no usar clases con getters/setters para DTOs
public class ContenidoRequest { ... }
```

### Entidades JPA — usar Lombok
```java
@Entity
@Table(name = "contenidos")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Contenido { ... }
```

### Inyeccion de dependencias — siempre por constructor
```java
// Correcto
@Service
@RequiredArgsConstructor
public class ContenidoService {
    private final ContenidoRepository repository;
    private final MlClient mlClient;
}

// Incorrecto — no usar @Autowired en campos
@Autowired
private ContenidoRepository repository;
```

### Capas — reglas estrictas
- **Controllers**: solo reciben request, llaman al service, retornan response. Cero logica de negocio.
- **Services**: toda la logica de negocio. Llaman a repositories y a clients de integracion.
- **Repositories**: solo consultas a la DB. Sin logica.
- **Clients**: solo comunicacion HTTP con servicios externos. Sin logica de negocio.
- Un controller NUNCA llama directamente a un repository.
- Un controller NUNCA llama directamente a un client de integracion.

### Manejo de errores
- Toda excepcion se maneja en `GlobalExceptionHandler` con `@ControllerAdvice`.
- Los services lanzan excepciones especificas (ej: `ContenidoNotFoundException`).
- Los controllers no tienen bloques try/catch.

### Propiedades de configuracion
- Formato: `propiedad.sub.propiedad` en `application.properties`
- Los valores sensibles SIEMPRE desde variables de entorno: `${NOMBRE_VAR:valor-default}`
- Nunca hardcodear URLs, passwords ni secrets en el codigo.

---

## Configuracion existente en application.properties

Las siguientes propiedades ya estan configuradas. No duplicarlas:

```properties
server.port=8080
spring.application.name=techcontent-ai
spring.datasource.url=${SPRING_DATASOURCE_URL:jdbc:postgresql://localhost:5432/techcontent}
spring.datasource.username=${SPRING_DATASOURCE_USERNAME:postgres}
spring.datasource.password=${SPRING_DATASOURCE_PASSWORD:postgres}
spring.jpa.hibernate.ddl-auto=update
ml.service.url=${ML_SERVICE_URL:http://localhost:5000}
supabase.auth.url=${SUPABASE_AUTH_URL:http://localhost:9999}
supabase.anon.key=${SUPABASE_ANON_KEY:}
supabase.service.key=${SUPABASE_SERVICE_KEY:}
supabase.jwt.secret=${SUPABASE_JWT_SECRET:}
```

Para leer propiedades en un bean, usar `@Value` o `@ConfigurationProperties`. No hardcodear URLs.

---

## Dependencias disponibles (pom.xml)

Ya declaradas, NO agregar duplicados:
- `spring-boot-starter-web` — REST controllers, RestClient
- `spring-boot-starter-security` — Spring Security, filtros
- `spring-boot-starter-data-jpa` — Repositorios, ORM
- `spring-boot-starter-validation` — @Valid, @NotBlank, @Size
- `spring-boot-starter-actuator` — /actuator/health
- `spring-boot-starter-test` — JUnit 5, Mockito, MockMvc
- `spring-security-test` — @WithMockUser, SecurityMockMvcRequestPostProcessors
- `postgresql` — driver PostgreSQL
- `lombok` — @Data, @Builder, @RequiredArgsConstructor, etc.

Si se necesita una dependencia nueva, agregarla al `pom.xml` y documentar el motivo en el PR.

---

## Testing

### Convencion de nombres
```
NombreClaseTest.java           # unitaria
NombreClaseIntegrationTest.java # integracion con contexto Spring
```

### Estructura de un test unitario
```java
@ExtendWith(MockitoExtension.class)
class ContenidoServiceTest {

    @Mock ContenidoRepository repository;
    @Mock MlClient mlClient;
    @InjectMocks ContenidoService service;

    @Test
    void clasificar_conTextoValido_retornaContenidoResponse() {
        // given
        // when
        // then
    }
}
```

### Convencion de nombres de metodos de test
```
metodoProbado_condicion_resultadoEsperado()
```

### Metas minimas de cobertura
- Services: 80%
- Controllers: 70% (con @WebMvcTest)
- Security filters: 90%

### Tests existentes (no inventar rutas; ampliar estos)

```
TechContentAiApplicationTests
api/controller/   Auth, Contenido, Archivo, Categoria, Grafo
api/exception/    GlobalExceptionHandlerTest
domain/service/   Contenido, Archivo, Categoria, Grafo
domain/repository/ ArchivoSpecification, Categoria, Grafo
integration/ml/   MlClientTest, MlClientDockerIntegrationTest
integration/oci/  OciStorageClientTest
security/         JwtService, JwtAuthFilter, JwtAccessDeniedHandler, SupabaseUserDetails
```

---

## Comandos Maven

```bash
# Compilar sin tests
mvn package -DskipTests

# Correr todos los tests
mvn test

# Levantar en desarrollo
mvn spring-boot:run

# Verificar que compila
mvn compile
```

---

## Endpoints ya definidos (no inventar nuevos sin aprobacion del equipo)

Clasificacion llama a GraphRAG `POST {ml.service.url}/api/v1/query` con `{ "pregunta": texto }`. No existe `/predict`.

| Metodo | Path | Descripcion |
|--------|------|-------------|
| POST | `/auth/register` | Registro (proxy a Supabase) |
| POST | `/auth/login` | Login (proxy a Supabase) |
| GET | `/actuator/health` | Health check (publico) |
| GET | `/actuator/info` | Info (publico) |
| POST | `/api/contenido` | Clasificar texto via GraphRAG |
| POST | `/api/contenido/lote` | Hasta 20 textos, transaccional |
| GET | `/api/contenido` | Listar contenidos del usuario |
| GET | `/api/contenido/buscar` | Busqueda por keywords (`?q=`) |
| POST | `/api/archivos` | Subir PDF/TXT/MD a OCI (`file` + `categoria` opcional) |
| GET | `/api/archivos` | Listar paginado (`page`, `size`, `q`, `tipo`) |
| GET | `/api/archivos/{id}` | Metadata / URL de un archivo |
| DELETE | `/api/archivos/{id}` | Borrar en OCI y DB |
| GET | `/api/categorias` | Categorias con `totalDocumentos` |
| POST | `/api/grafos/sincronizar` | Descargar JSON GraphRAG desde OCI |
| GET | `/api/grafos/actual` | Ultimo grafo persistido |
| GET | `/api/grafos/historial` | Historial paginado |
| GET | `/api/grafos/buscarfecha` | Rango `desde` / `hasta` |
| GET | `/api/grafos/id/{id}` | Grafo por UUID |
