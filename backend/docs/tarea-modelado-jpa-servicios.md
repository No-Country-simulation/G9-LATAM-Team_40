# Modelado JPA, repositorios y servicios

## Descripción

Modelado de entidades JPA, repositorios y servicios de lógica de negocio principal para la clasificación, almacenamiento y búsqueda semántica de contenidos técnicos.

## Checklist de criterios de aceptación

### 1. Modelado de entidades JPA y configuración de PostgreSQL

- [x] **CUMPLE — Crear entidad `Contenido.java` (`@Entity`, UUID PK, `user_id`, título, texto, categoría, probabilidad, `procesado_en`).**

  `Contenido` está declarado con `@Entity` y se vincula con la tabla `contenidos`. El identificador utiliza `UUID`, `@Id` y `GenerationType.UUID`. Los campos `userId` y `procesadoEn` se mapean explícitamente como `user_id` y `procesado_en`; también se incluyen título, texto, categoría y probabilidad.

- [x] **CUMPLE — Configurar la lista de palabras clave como `palabras_clave` array en PostgreSQL.**

  La propiedad `palabrasClave` está configurada como `List<String>` con `@JdbcTypeCode(SqlTypes.ARRAY)` y se persiste en la columna PostgreSQL `palabras_clave` de tipo `text[]`. Hibernate trata esta colección básica como un único valor SQL `ARRAY`; no se utiliza una tabla relacionada.

- [x] **CUMPLE — Crear entidad `Archivo.java` (`@Entity`, UUID PK, `user_id`, nombre, url, tamaño, tipo, `subido_en`).**

  `Archivo` está declarado con `@Entity` y se vincula con la tabla `archivos`. El identificador utiliza `UUID`, `@Id` y `GenerationType.UUID`. La entidad contiene `userId`, nombre, URL, tamaño, tipo y fecha de subida, con mapeos explícitos para `user_id` y `subido_en`.

- [x] **CUMPLE — Crear repositorios `ContenidoRepository.java` y `ArchivoRepository.java` (`JpaRepository`).**

  `ContenidoRepository` extiende `JpaRepository<Contenido, UUID>` y `ArchivoRepository` extiende `JpaRepository<Archivo, UUID>`.

- [x] **CUMPLE — Configurar `application.properties` con dialecto PostgreSQL 15 y auto-generación de tablas (`ddl-auto=update`).**

  La configuración utiliza el driver PostgreSQL, `org.hibernate.dialect.PostgreSQLDialect` y `spring.jpa.hibernate.ddl-auto=update`.

### 2. Lógica de `ContenidoService` y `CategoriaService`

- [x] **CUMPLE — Implementar `ContenidoService.clasificar()`: orquestación entre `MlClient`, mapeo al modelo de dominio y persistencia en DB.**

  `clasificar()` envía el texto a `MlClient.queryGraphRag()`, recibe la respuesta, categoría, probabilidad, palabras clave y trazabilidad, construye una entidad `Contenido`, la persiste mediante `ContenidoRepository.save()` y transforma el resultado en `ContenidoResponse`.

- [x] **CUMPLE — Implementar query JPQL personalizada en `ContenidoRepository` para búsqueda por palabras clave (`buscarPorKeyword`).**

  `buscarPorKeyword()` está declarado con `@Query`. La consulta aplica `array_contains()` sobre la columna `palabras_clave` y también contempla coincidencias en el título.

- [x] **CUMPLE — Implementar `ContenidoService.buscar()` para la consulta y filtrado de contenidos por usuario.**

  `buscar()` delega en `ContenidoRepository.buscarPorKeyword(query, userId)`. La consulta JPQL incluye `c.userId = :userId`, por lo que los resultados quedan filtrados por el usuario recibido, y después se transforman en respuestas.

- [x] **CUMPLE — Implementar `ContenidoService.procesarLote()` para procesar listas múltiples de documentos técnicos.**

  `procesarLote()` recorre la lista contenida en `ContenidoLoteRequest`, ejecuta `clasificar()` para cada documento y retorna la lista de resultados.

- [x] **CUMPLE — Implementar `CategoriaRepository` y `CategoriaService.listarConConteo()` para retornar categorías con la cantidad real de documentos.**

  `CategoriaRepository` agrupa las entidades `Contenido` por categoría y calcula `COUNT(c)` mediante JPQL. `CategoriaService.listarConConteo()` delega en `findCategoriasConConteo()` y retorna los nombres de categoría junto con el total calculado.

## Componentes implementados o modificados

### `Contenido.java`

Define la persistencia del contenido técnico, sus datos de clasificación, el usuario propietario, el momento de procesamiento y la lista de palabras clave almacenada como un array PostgreSQL.

### `Archivo.java`

Define la persistencia de metadatos de archivos: propietario, nombre, URL, tamaño, tipo y fecha de subida.

### `ContenidoRepository.java`

Incorpora las operaciones JPA de contenido, el listado por usuario y la búsqueda JPQL mediante título o palabras clave con filtro de usuario.

### `ArchivoRepository.java`

Incorpora las operaciones JPA de archivos, el listado por usuario y la consulta conjunta por identificador y usuario.

### `CategoriaRepository.java`

Agrega la consulta JPQL que agrupa los contenidos por categoría y proyecta el conteo en `CategoriaResponse`.

### `ContenidoService.java`

Implementa la clasificación individual, el procesamiento por lote, la búsqueda, el listado por usuario, el mapeo desde la respuesta ML hacia la entidad y la conversión de la entidad persistida hacia el DTO de respuesta.

### `CategoriaService.java`

Expone `listarConConteo()` y obtiene del repositorio las categorías agrupadas con su cantidad de documentos.

### `application.properties`

Configura la conexión JDBC de PostgreSQL, el driver, el dialecto de Hibernate y la actualización automática del esquema mediante `ddl-auto=update`.

## Decisión de persistencia para palabras clave

El criterio combina `@ElementCollection` con un array PostgreSQL, pero representan dos estrategias de persistencia diferentes:

- `@ElementCollection` almacena los elementos en una tabla secundaria, con una fila por palabra.
- Una colección básica de Hibernate mapeada como `SqlTypes.ARRAY` almacena todos los elementos en una única columna SQL array.

Para obtener explícitamente la columna PostgreSQL `palabras_clave text[]`, se utiliza:

```java
@JdbcTypeCode(SqlTypes.ARRAY)
@Column(name = "palabras_clave", columnDefinition = "text[]")
private List<String> palabrasClave;
```

Con este mapeo, una lista Java como:

```java
List.of("java", "spring", "backend")
```

se persiste en PostgreSQL como:

```text
{java,spring,backend}
```

La consulta `buscarPorKeyword()` dejó de unir la tabla secundaria y ahora evalúa directamente el array:

```java
array_contains(c.palabrasClave, :query)
```

`spring.jpa.hibernate.ddl-auto=update` agrega la columna nueva, pero no elimina automáticamente una tabla auxiliar creada por una versión anterior del mapeo. Si la base ya existía, `contenido_palabras_clave` puede permanecer físicamente aunque el código actualizado no la utilice.

## Verificaciones realizadas

El cambio fue comprobado con las siguientes validaciones:

- Compilación del backend dentro de Docker finalizada con `BUILD SUCCESS`.
- Inicio completo del contexto de Spring Boot.
- Creación de los repositorios Spring Data sin errores de validación HQL.
- Conexión de Hibernate con PostgreSQL.
- Estado `healthy` del contenedor backend.
- Creación de `contenidos.palabras_clave` como un array PostgreSQL real.

La consulta de metadatos de PostgreSQL produjo:

```text
column_name     data_type    udt_name
palabras_clave  ARRAY        _text
```

`ARRAY` confirma que la columna es una colección SQL y `_text` identifica un array cuyos elementos son valores `text`.

## Cómo probar el cambio

Los siguientes comandos se ejecutan desde la raíz del repositorio.

### 1. Compilar el backend

```powershell
docker compose build backend
```

El proceso correcto debe terminar con:

```text
BUILD SUCCESS
```

### 2. Levantar el backend y sus dependencias

```powershell
docker compose up -d backend
```

Comprobar el estado:

```powershell
docker compose ps backend
```

El resultado esperado para el backend es `Up` y, después del período inicial, `healthy`.

### 3. Revisar la creación del contexto

```powershell
docker compose logs --tail=100 backend
```

El arranque correcto incluye mensajes equivalentes a:

```text
Initialized JPA EntityManagerFactory
Started TechContentAiApplication
```

### 4. Verificar el tipo de la columna

```powershell
docker compose exec -T db psql `
    -U postgres `
    -d techcontent `
    -c "SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema='public' AND table_name='contenidos' AND column_name='palabras_clave';"
```

El resultado esperado es:

```text
palabras_clave | ARRAY | _text
```

### 5. Crear un contenido desde Postman

Crear una petición con esta configuración:

```text
Método: POST
URL: http://localhost:8080/api/contenido
Authorization: Bearer Token
Content-Type: application/json
```

Body:

```json
{
  "titulo": "Introducción a Spring Boot",
  "texto": "Spring Boot permite desarrollar servicios backend utilizando Java y componentes de Spring."
}
```

La respuesta debe incluir `palabrasClave` con los valores generados durante la clasificación.

### 6. Comprobar el valor persistido

```powershell
docker compose exec -T db psql `
    -U postgres `
    -d techcontent `
    -c "SELECT titulo, palabras_clave, pg_typeof(palabras_clave) FROM contenidos ORDER BY procesado_en DESC LIMIT 5;"
```

El resultado debe mostrar las palabras entre llaves y el tipo `text[]`:

```text
Introducción a Spring Boot | {java,spring,backend} | text[]
```

Las palabras concretas dependen del resultado de clasificación.

### 7. Probar la búsqueda por palabra clave

Crear otra petición en Postman:

```text
Método: GET
URL: http://localhost:8080/api/contenido/buscar?q=java
Authorization: Bearer Token
```

El endpoint utiliza el usuario autenticado y ejecuta `buscarPorKeyword()`. Si `java` está presente como elemento del array de palabras clave de un contenido de ese usuario, la respuesta debe incluirlo.

### 8. Detener los servicios

```powershell
docker compose stop
```

## Flujo de clasificación

```text
ContenidoRequest
    ↓
ContenidoService.clasificar()
    ↓
MlClient.queryGraphRag(texto)
    ↓
Mapeo a Contenido
    ↓
ContenidoRepository.save(contenido)
    ↓
ContenidoResponse
```

## Flujo de búsqueda

```text
query + userId
    ↓
ContenidoService.buscar()
    ↓
ContenidoRepository.buscarPorKeyword(query, userId)
    ↓
Filtro JPQL por usuario, título y palabras clave
    ↓
List<ContenidoResponse>
```

## Flujo de categorías con conteo

```text
CategoriaService.listarConConteo()
    ↓
CategoriaRepository.findCategoriasConConteo()
    ↓
GROUP BY categoria + COUNT(contenido)
    ↓
List<CategoriaResponse>
```
