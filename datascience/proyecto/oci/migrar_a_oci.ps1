[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$CompartmentId,

    [Parameter(Mandatory = $true)]
    [string]$BucketName,

    [string]$Prefix = "prod"
)

$ErrorActionPreference = "Stop"

# Script: <raiz>/proyecto/oci; datos: <raiz>/db
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$DbPath = Join-Path $ProjectRoot "db"

function Invoke-Oci {
    param([string[]]$Arguments)

    & oci @Arguments

    if ($LASTEXITCODE -ne 0) {
        throw "Falló el comando: oci $($Arguments -join ' ')"
    }
}

Write-Host "Validando OCI CLI..."
if (-not (Get-Command oci -ErrorAction SilentlyContinue)) {
    throw "No se encontró 'oci'. Instálala con: pip install oci-cli"
}

if (-not (Test-Path -LiteralPath $DbPath -PathType Container)) {
    throw "No existe la carpeta de datos: $DbPath"
}

Write-Host "Obteniendo namespace de Object Storage..."
$Namespace = (& oci os ns get --query "data" --raw-output)

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($Namespace)) {
    throw "No se pudo obtener el namespace. Ejecuta primero: oci setup config"
}

Write-Host "Verificando bucket '$BucketName'..."
& oci os bucket get `
    --namespace-name $Namespace `
    --bucket-name $BucketName `
    --output json 2>$null

$BucketExiste = $LASTEXITCODE -eq 0

if (-not $BucketExiste) {
    if ([string]::IsNullOrWhiteSpace($CompartmentId)) {
        throw "El bucket '$BucketName' no existe. Se necesita -CompartmentId para crearlo."
    }

    Write-Host "El bucket no existe. Creándolo como privado, Standard y con versionado..."

    Invoke-Oci @(
        "os", "bucket", "create",
        "--namespace-name", $Namespace,
        "--compartment-id", $CompartmentId,
        "--name", $BucketName,
        "--public-access-type", "NoPublicAccess",
        "--storage-tier", "Standard",
        "--versioning", "Enabled"
    )
}
else {
    Write-Host "El bucket ya existe."
}


Write-Host "Sincronizando '$DbPath' hacia '$BucketName/$Prefix'..."
Write-Host "No se eliminarán objetos remotos."

Invoke-Oci @(
    "os", "object", "sync",
    "--namespace-name", $Namespace,
    "--bucket-name", $BucketName,
    "--src-dir", $DbPath,
    "--prefix", $Prefix,
    "--no-follow-symlinks"
)

Write-Host "Verificando objetos cargados..."
$Objetos = & oci os object list `
    --namespace-name $Namespace `
    --bucket-name $BucketName `
    --prefix $Prefix `
    --all `
    --query "data[].name" `
    --output json | ConvertFrom-Json

Write-Host "Migración finalizada."
Write-Host "Bucket: $BucketName"
Write-Host "Prefix: $Prefix"
Write-Host "Objetos encontrados: $($Objetos.Count)"

$ArchivosCriticos = @(
    "$Prefix/output_json/grafo_nodos_subnodos_graphrag.json",
    "$Prefix/output_json/embeddings_llm.json"
)

foreach ($Archivo in $ArchivosCriticos) {
    if ($Objetos -contains $Archivo) {
        Write-Host "OK: $Archivo"
    }
    else {
        Write-Warning "Aún no existe: $Archivo. Ejecute primero las etapas que lo generan."
    }
}
