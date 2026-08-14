# Guía de pruebas del backend

Esta guía describe los cambios de testing incorporados al backend de TechContent AI y explica cómo ejecutar y verificar las pruebas automatizadas.

## Alcance de los cambios

Se incorporaron pruebas para los servicios de contenido y archivos, el servicio JWT, el manejo global de excepciones y los controladores REST de contenido y archivos.

Los cambios incluyen:

- Dependencia de H2 con alcance exclusivo de test.
- Perfil `test` con una base H2 en memoria.
- Pruebas unitarias con JUnit 5 y Mockito.
- Pruebas de integración con `@SpringBootTest` y MockMvc.
- Prueba de carga del contexto general de Spring.
- Respuestas JSON para errores de autenticación y autorización.

## Estructura de las pruebas

```text
src/test/
├── java/com/techcontent/ai/
│   ├── TechContentAiApplicationTests.java
│   ├── api/
│   │   ├── controller/
│   │   │   ├── ContenidoControllerIntegrationTest.java
│   │   │   └── ArchivoControllerIntegrationTest.java
│   │   └── exception/
│   │       └── GlobalExceptionHandlerTest.java
│   ├── domain/service/
│   │   ├── ContenidoServiceTest.java
│   │   └── ArchivoServiceTest.java
│   └── security/
│       └── JwtServiceTest.java
└── resources/
    └── application-test.properties
```

## Tipos de prueba

### Pruebas unitarias

Las pruebas unitarias ejecutan una clase de manera aislada. Las dependencias externas se reemplazan por mocks, por lo que no se realizan conexiones HTTP ni operaciones reales sobre servicios externos.

| Clase | Alcance comprobado |
|---|---|
| `ContenidoServiceTest` | Clasificación, procesamiento por lote, búsqueda y listado por usuario. Verifica la interacción con el cliente ML y el repositorio. |
| `ArchivoServiceTest` | Carga, listado y consulta de archivos. También valida archivo vacío, tipo no permitido, tamaño máximo y archivo inexistente. |
| `JwtServiceTest` | Token válido, expirado, mal firmado o malformado; extracción de usuario y correo; comportamiento sin secreto configurado. |
| `GlobalExceptionHandlerTest` | Respuestas 400, 404 y 500, estructura de `ErrorResponse` y combinación de errores de validación. |

`ContenidoServiceTest` y `ArchivoServiceTest` utilizan `@ExtendWith(MockitoExtension.class)`, `@Mock` e `@InjectMocks` para crear sus dependencias simuladas.

### Pruebas de integración

Las pruebas de integración levantan el contexto de Spring Boot mediante `@SpringBootTest`, configuran MockMvc y ejercitan el flujo HTTP hasta la persistencia.

| Clase | Alcance comprobado |
|---|---|
| `ContenidoControllerIntegrationTest` | Creación de contenido, validaciones de entrada, autenticación, procesamiento por lote, búsqueda y listado. |
| `ArchivoControllerIntegrationTest` | Carga multipart, validaciones de archivo, autenticación, listado y consulta por identificador. |
| `TechContentAiApplicationTests` | Carga completa del contexto de Spring con el perfil de pruebas. |

Los adaptadores externos se sustituyen con `@MockBean`. Esto permite probar controladores, servicios, seguridad y repositorios sin efectuar llamadas externas reales.

## Base de datos para las pruebas

El archivo `src/test/resources/application-test.properties` configura H2 en memoria y activa compatibilidad con PostgreSQL:

```properties
spring.datasource.url=jdbc:h2:mem:testdb;MODE=PostgreSQL;DB_CLOSE_DELAY=-1
spring.datasource.driver-class-name=org.h2.Driver
spring.jpa.hibernate.ddl-auto=create-drop
```

Características de este entorno:

- La base se crea durante la ejecución de las pruebas.
- Hibernate crea las tablas requeridas.
- Los datos no persisten después de finalizar el proceso.
- No es necesario levantar PostgreSQL ni Docker para ejecutar la suite.
- Las clases de integración seleccionan este entorno con `@ActiveProfiles("test")`.

## Requisitos

Antes de ejecutar las pruebas se necesita:

- Java 17.
- Maven disponible mediante el comando `mvn`.
- Una terminal ubicada en la carpeta `backend`.

Para comprobar las instalaciones:

```powershell
java -version
mvn -version
```

La versión activa de Java debe ser 17.

## Ejecutar toda la suite

Desde la raíz del repositorio:

```powershell
cd backend
mvn test
```

También se puede ejecutar indicando directamente el archivo `pom.xml`:

```powershell
mvn -f backend/pom.xml test
```

Maven compila el código principal, compila los tests y ejecuta todas las clases cuyo nombre coincide con los patrones de prueba configurados por Surefire.

## Ejecutar grupos específicos

### Solo pruebas unitarias de servicios

```powershell
mvn "-Dtest=ContenidoServiceTest,ArchivoServiceTest" test
```

### Solo pruebas de seguridad

```powershell
mvn "-Dtest=JwtServiceTest" test
```

### Solo manejo global de errores

```powershell
mvn "-Dtest=GlobalExceptionHandlerTest" test
```

### Solo pruebas de integración de controladores

```powershell
mvn "-Dtest=ContenidoControllerIntegrationTest,ArchivoControllerIntegrationTest" test
```

### Una clase específica

```powershell
mvn "-Dtest=ArchivoServiceTest" test
```

### Un método específico

```powershell
mvn "-Dtest=ArchivoServiceTest#subir_archivoVacio_deberiaLanzarIllegalArgumentException" test
```

## Interpretar el resultado

Una ejecución correcta termina con:

```text
BUILD SUCCESS
```

El resumen de cada clase presenta esta información:

```text
Tests run: N, Failures: 0, Errors: 0, Skipped: 0
```

La diferencia entre fallos y errores es:

- `Failures`: una aserción produjo un resultado distinto del esperado.
- `Errors`: el test no completó su ejecución por una excepción inesperada o un problema al crear el contexto.
- `Skipped`: el test fue omitido.

Los reportes detallados se generan en:

```text
backend/target/surefire-reports/
```

Cada ejecución reemplaza o actualiza los reportes correspondientes.

## Ejecutar una compilación limpia

Cuando existan resultados antiguos en `target`, se puede solicitar a Maven una ejecución limpia:

```powershell
mvn clean test
```

`clean` elimina los artefactos generados anteriormente y `test` vuelve a compilar y ejecutar la suite completa.

## Problemas frecuentes

### Maven no está reconocido

Si PowerShell muestra que `mvn` no se reconoce como comando, es necesario instalar Maven y agregar su carpeta `bin` a la variable `PATH`. Después se debe abrir una terminal nueva y comprobarlo con:

```powershell
mvn -version
```

### Java utiliza una versión incorrecta

Si Maven informa una versión diferente de Java, se debe configurar `JAVA_HOME` para apuntar a un JDK 17 y abrir una terminal nueva.

### Fallo al cargar el contexto

Comprobar que la clase use:

```java
@ActiveProfiles("test")
```

También se debe verificar que exista:

```text
src/test/resources/application-test.properties
```

### Un reporte muestra resultados antiguos

Ejecutar:

```powershell
mvn clean test
```

Después consultar nuevamente `target/surefire-reports`.

## Flujo recomendado antes de un Pull Request

1. Abrir una terminal en `backend`.
2. Ejecutar `mvn clean test`.
3. Confirmar `BUILD SUCCESS`.
4. Verificar que no existan failures, errors ni tests omitidos inesperadamente.
5. Revisar los archivos preparados mediante `git diff --cached`.
6. Crear el commit y el Pull Request únicamente después de una ejecución exitosa.

## Nota sobre cobertura

La suite ejercita servicios, controladores, seguridad y manejo de excepciones. El proyecto no tiene actualmente un plugin de cobertura configurado en Maven; por lo tanto, `mvn test` informa resultados funcionales, pero no genera porcentajes de cobertura.

