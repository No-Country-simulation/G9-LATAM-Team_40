# Estado de las tareas backend BE-1 a BE-4

## Resumen

Las implementaciones y pruebas automatizadas correspondientes a BE-1, BE-2, BE-3 y BE-4 están completas. Los tests ejecutados no presentan fallos y JaCoCo confirma que se alcanzan las metas de cobertura requeridas.

Quedan pendientes únicamente validaciones contra servicios externos con credenciales y recursos definitivos del equipo.

## BE-1 — Seguridad y autenticación

Implementado:

- Seguridad stateless con Spring Security.
- Validación de JWT emitidos por Supabase.
- Filtro Bearer y carga del usuario en `SecurityContext`.
- Proxy de registro y login mediante Supabase GoTrue.
- CORS, respuestas 401 y respuestas 403 en JSON.
- Pruebas automatizadas de los componentes de seguridad.

Validación externa pendiente:

- Confirmar registro y login contra el entorno definitivo de Supabase.
- Confirmar un JWT Bearer emitido y validado con las credenciales definitivas.
- Confirmar pre-flight desde el frontend definitivo.

Supabase local puede utilizarse para validar ahora el flujo técnico de registro, login y autorización. Esa prueba local no reemplaza la validación posterior con el entorno definitivo del equipo.

## BE-2 — JPA, repositorios y servicios

Implementado:

- Entidades `Contenido` y `Archivo`.
- Identificadores UUID y campos requeridos.
- Colección de palabras clave con `@ElementCollection`.
- Repositorios JPA.
- Configuración PostgreSQL y `ddl-auto=update`.
- Clasificación, persistencia, búsqueda por usuario y procesamiento en lote.
- Categorías con cantidad real de documentos.
- Pruebas automatizadas de servicios.

No quedan validaciones externas específicas pendientes para completar el código de esta tarea.

## BE-3 — ML y OCI Object Storage

Implementado:

- `MlClient` con Spring `RestClient`.
- Solicitud `POST /api/v1/query` y contratos GraphRAG (`QueryRequest`/`QueryResponse`).
- Mapeo de `palabras_clave`, respuesta y trazabilidad desde JSON snake_case.
- Pruebas unitarias del cliente y del contrato GraphRAG.
- Configuración del SDK oficial de OCI.
- Subida mediante `putObject`.
- Generación de URL temporal mediante Pre-Authenticated Request.
- Manejo específico de timeouts de OCI.
- Pruebas unitarias del cliente OCI con Mockito.

Validación externa pendiente:

- Definir con el equipo tenancy, usuario, región, namespace y bucket.
- Configurar credenciales reales sin incorporarlas al repositorio.
- Montar la clave privada dentro del contenedor backend.
- Probar una subida y descarga reales.
- Confirmar una URL temporal sobre un objeto real.
- Confirmar el comportamiento ante un timeout real.

El detalle operativo se encuentra en `docs/pendiente-configuracion-oci.md`.

## BE-4 — API REST, errores y QA

Implementado:

- DTO records y validación Bean Validation.
- Controladores y endpoints requeridos.
- Tratamiento global y unificado de errores 400, 401, 403, 404 y 500.
- Endpoint público `/actuator/health`.
- Pruebas unitarias e integración requeridas.
- Medición y límites automáticos mediante JaCoCo.

Cobertura medida:

| Área | Cobertura | Mínimo requerido | Estado |
|---|---:|---:|---|
| Services | 95,71 % | 80 % | Cumple |
| Controllers | 78,57 % | 70 % | Cumple |
| Security | 98,94 % | 90 % | Cumple |

Para regenerar el reporte:

```powershell
cd backend
mvn clean verify
```

El reporte HTML se genera en:

```text
backend/target/site/jacoco/index.html
```

## Validación local recomendada antes del PR

1. Levantar los servicios:

   ```powershell
   docker compose up -d --build
   ```

2. Comprobar su estado:

   ```powershell
   docker compose ps
   ```

3. Comprobar FastAPI:

   ```powershell
   Invoke-RestMethod http://localhost:5000/health
   ```

4. Comprobar Spring Boot Actuator:

   ```powershell
   Invoke-RestMethod http://localhost:8080/actuator/health
   ```

5. Probar registro y login contra Supabase local mediante `POST /auth/register` y `POST /auth/login` con JSON válido.

6. Utilizar el token del login como `Authorization: Bearer <token>` para llamar un endpoint protegido de `/api/**`.

7. Ejecutar todas las verificaciones:

   ```powershell
   cd backend
   mvn clean verify
   ```

## Seguridad de credenciales

- No subir `.env`.
- No subir claves privadas `.pem`.
- No incluir secrets, fingerprints ni tokens reales en documentación, tests o commits.
- Mantener en `.env.example` solamente nombres de variables y valores ilustrativos.
