# Lectura de datos desde OCI Object Storage

La API puede descargar el contenido del bucket a `db/` antes de cargar el
GraphRAG. Toda ejecución parte del `.env` ubicado en la raíz del repositorio:
`datascience/proyecto/src/settings.py` lo carga automáticamente en desarrollo
local y Docker Compose inyecta las variables al proceso del contenedor. No se
crea ni se monta un `.env` dentro de `/app`.

Para autenticación con API key, completa en el `.env` raíz:

```env
DATA_SOURCE=oci
OCI_DATASET_BUCKET=your-graphrag-dataset-bucket
OCI_NAMESPACE=your-oci-namespace
OCI_PREFIX=prod
OCI_AUTH_MODE=api_key
OCI_CLI_USER=ocid1.user.oc1..your_user_ocid
OCI_CLI_TENANCY=ocid1.tenancy.oc1..your_tenancy_ocid
OCI_CLI_REGION=your-oci-region
OCI_CLI_FINGERPRINT=xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx:xx
OCI_CLI_KEY_FILE=/home/your-user/.oci/oci_api_key.pem
```

`OCI_CLI_KEY_FILE` es una ruta del host. En Docker Compose se monta como
`/run/secrets/oci_api_key.pem` dentro de `backend` y `ml-service`; no cambies
el valor del `.env` por esa ruta interna.

Para una instancia desplegada dentro de OCI, puede usarse identidad de
instancia en vez de copiar una clave privada al servidor:

```env
DATA_SOURCE=oci
OCI_DATASET_BUCKET=your-graphrag-dataset-bucket
OCI_NAMESPACE=your-oci-namespace
OCI_PREFIX=prod
OCI_AUTH_MODE=instance_principal
```

La identidad de instancia necesita una política IAM que permita leer objetos
del bucket. La sincronización descarga solo objetos nuevos o modificados según
su ETag y no elimina archivos locales.
