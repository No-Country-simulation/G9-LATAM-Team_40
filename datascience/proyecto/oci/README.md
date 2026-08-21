# Lectura de datos desde OCI Object Storage

La API puede descargar el contenido del bucket a `db/` antes de cargar el
GraphRAG. En `proyecto/.env` configura:

```env
DATA_SOURCE=oci
OCI_DATASET_BUCKET=OCI_DATASET_BUCKET
OCI_NAMESPACE=axl8ucsysxgy
OCI_PREFIX=prod
OCI_AUTH_MODE=api_key
OCI_CONFIG_FILE=C:/Users/USUARIO/.oci/config
OCI_CONFIG_PROFILE=DEFAULT
```

Para una instancia desplegada dentro de OCI, usa identidad de instancia en vez
de copiar una clave privada al servidor:

```env
DATA_SOURCE=oci
OCI_DATASET_BUCKET=OCI_DATASET_BUCKET
OCI_NAMESPACE=axl8ucsysxgy
OCI_PREFIX=prod
OCI_AUTH_MODE=instance_principal
```

La identidad de instancia necesita una política IAM que permita leer objetos
del bucket. La sincronización descarga solo objetos nuevos o modificados según
su ETag y no elimina archivos locales.
