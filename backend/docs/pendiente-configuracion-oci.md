# Configuración pendiente de OCI Object Storage

## Estado actual

El backend ya contiene la integración mediante el SDK oficial de OCI:

- `OciStorageConfig` construye un `ObjectStorageClient`.
- `OciStorageClient.upload()` utiliza `putObject` para subir archivos.
- La configuración se obtiene mediante propiedades y variables de entorno.
- Las pruebas automatizadas pueden utilizar un cliente OCI simulado y no requieren credenciales reales.

La conexión real con OCI queda pendiente porque el equipo todavía no definió un entorno compartido de Oracle Cloud.

## Decisiones pendientes con el equipo

Antes de realizar una prueba real deben acordarse los siguientes datos:

- Tenancy que utilizará el proyecto.
- Usuario o identidad autorizada para Object Storage.
- Región de OCI.
- Namespace de Object Storage.
- Bucket destinado a los archivos del backend.
- Política de acceso IAM necesaria para subir y descargar objetos.
- Responsable y mecanismo seguro para distribuir la clave privada.
- Uso de bucket público o privado y duración de las URLs temporales.

## Variables requeridas

Cada desarrollador deberá completar estas variables únicamente en su archivo `.env` local:

```ini
OCI_CLI_USER=ocid1.user.oc1..xxxxx
OCI_CLI_TENANCY=ocid1.tenancy.oc1..xxxxx
OCI_CLI_REGION=sa-saopaulo-1
OCI_CLI_FINGERPRINT=xx:xx:xx:xx
OCI_CLI_KEY_FILE=C:/ruta/local/oci_api_key.pem
OCI_NAMESPACE=namespace_del_tenancy
OCI_FILES_BUCKET=techcontent-files
```

No deben subirse al repositorio valores reales, archivos `.pem`, fingerprints ni identificadores privados. `.env.example` debe contener solamente valores ilustrativos.

## Configuración pendiente en Docker

Cuando exista el entorno OCI, el servicio `backend` de `docker-compose.yml` deberá recibir `OCI_NAMESPACE`. La clave privada también deberá montarse como archivo de solo lectura dentro del contenedor y `OCI_CLI_KEY_FILE` deberá señalar esa ruta interna.

Ejemplo orientativo:

```yaml
services:
  backend:
    environment:
      OCI_CLI_USER: ${OCI_CLI_USER}
      OCI_CLI_TENANCY: ${OCI_CLI_TENANCY}
      OCI_CLI_REGION: ${OCI_CLI_REGION}
      OCI_CLI_FINGERPRINT: ${OCI_CLI_FINGERPRINT}
      OCI_CLI_KEY_FILE: /app/oci/oci_api_key.pem
      OCI_NAMESPACE: ${OCI_NAMESPACE}
      OCI_FILES_BUCKET: ${OCI_FILES_BUCKET}
    volumes:
      - ${OCI_CLI_KEY_FILE}:/app/oci/oci_api_key.pem:ro
```

La ruta del lado izquierdo debe existir en la computadora que ejecuta Docker. La ruta `/app/oci/oci_api_key.pem` corresponde al interior del contenedor.

## Validación futura

Una vez disponibles las credenciales y el bucket:

1. Validar la composición:

   ```powershell
   docker compose config
   ```

2. Reconstruir y levantar el backend:

   ```powershell
   docker compose up -d --build backend
   ```

3. Revisar la inicialización del SDK:

   ```powershell
   docker compose logs backend --tail 100
   ```

4. Ejecutar una carga real y comprobar que el objeto aparezca en `OCI_FILES_BUCKET`.

5. Generar una URL temporal y verificar que permita descargar el objeto antes del vencimiento.

6. Simular o provocar un timeout y comprobar que se transforme en el error específico definido por el backend.

## Criterios BE-3 afectados

Hasta completar la validación real quedan pendientes de comprobación:

- Inicialización de `ObjectStorageClient` con credenciales válidas.
- Subida real al bucket configurado en `OCI_FILES_BUCKET`.
- Acceso efectivo mediante URL pública o temporal.
- Comportamiento frente a timeouts reales de red.

La ausencia actual de credenciales no impide desarrollar ni probar unitariamente las llamadas al SDK.
